"""Council V2 — Multi-round debate with 7 agents + Moderator + Supervisor.

Flow:
  Round 1: 7 agents analyze in parallel → Moderator scores
  Round 2: 7 agents debate (react to Round 1) in parallel → Moderator scores
  Round 3: Supervisor reviews both rounds → Final verdict
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from backend.llm.router import llm_router
from backend.agents.analyst_agent import SYSTEM_PROMPT as ANALYST_PROMPT
from backend.agents.critic_agent import SYSTEM_PROMPT as CRITIC_PROMPT
from backend.agents.creative_agent import SYSTEM_PROMPT as CREATIVE_PROMPT
from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
from backend.agents.legal_agent import SYSTEM_PROMPT as LEGAL_PROMPT
from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
from backend.agents.optimizer_agent import SYSTEM_PROMPT as OPTIMIZER_PROMPT
from backend.agents.moderator import SYSTEM_PROMPT as MODERATOR_PROMPT
from backend.middleware.security import sanitize_input
import uuid
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 7 agent roles with their system prompts
SEVEN_AGENTS = {
    "analyst": {"prompt": ANALYST_PROMPT, "label": "Analyst"},
    "critic": {"prompt": CRITIC_PROMPT, "label": "Critic"},
    "creative": {"prompt": CREATIVE_PROMPT, "label": "Creative"},
    "risk": {"prompt": RISK_PROMPT, "label": "Risk"},
    "legal": {"prompt": LEGAL_PROMPT, "label": "Legal"},
    "market": {"prompt": MARKET_PROMPT, "label": "Market"},
    "optimizer": {"prompt": OPTIMIZER_PROMPT, "label": "Optimizer"},
}

SUPERVISOR_PROMPT = """You are the Supervisor Agent — the final decision authority on the Supply Chain Council.

You receive the Moderator's aggregated results from Round 1 and Round 2 of a multi-agent debate.

Your responsibilities:
1. Review the Moderator's summaries from both rounds
2. Determine the final verdict / consensus answer
3. Identify which agents were most reliable/accurate
4. Assign a final confidence score (0-100) for the answer
5. Flag any unresolved conflicts or disagreements between agents

Output format:
## Final Verdict
[Clear, actionable final answer]

## Most Reliable Agents
[Rank agents by reliability with brief justification]

## Confidence Score
[0-100 score with explanation]

## Unresolved Conflicts
[Any disagreements that could not be resolved]

## Recommended Actions
[Ordered list of next steps]
"""

# No sentinel needed — we count agent_done events from the SSE data itself


class CouncilV2Request(BaseModel):
    query: str
    context: Optional[dict] = None


async def _run_agent_parallel(
    agent_key: str,
    agent_info: dict,
    messages: list,
    round_num: int,
    queue: asyncio.Queue,
    outputs: dict,
    confidences: dict,
    default_confidence: float = 50.0,
):
    """Run a single agent, push SSE events to a shared queue, and store results."""
    await queue.put(f"data: {json.dumps({'type': 'agent_start', 'agent': agent_key, 'round': round_num})}\n\n")

    full_response = ""
    try:
        async for token in llm_router.stream_with_fallback(agent_key, messages):
            full_response += token
            await queue.put(f"data: {json.dumps({'type': 'token', 'agent': agent_key, 'round': round_num, 'content': token})}\n\n"
)
    except Exception as e:
        full_response = f"Agent {agent_key} unavailable: {e}"
        await queue.put(f"data: {json.dumps({'type': 'agent_error', 'agent': agent_key, 'round': round_num, 'error': str(e)})}\n\n")

    confidence = _parse_confidence(full_response, default_confidence)
    outputs[agent_key] = full_response
    confidences[agent_key] = confidence

    await queue.put(f"data: {json.dumps({'type': 'agent_done', 'agent': agent_key, 'round': round_num, 'confidence': confidence})}\n\n")


async def _drain_queue(queue: asyncio.Queue, agent_count: int):
    """Read SSE events from the queue until all agents in a round are done.

    Yields SSE event strings. Tracks how many agent_done events we've seen;
    once that equals agent_count, the round is complete.
    """
    done_count = 0
    while done_count < agent_count:
        event_str = await queue.get()
        # Count agent_done events by inspecting the SSE data
        if '"type": "agent_done"' in event_str:
            done_count += 1
        yield event_str


@router.post("/stream")
async def council_v2_stream(request: CouncilV2Request):
    """SSE streaming endpoint for the 3-round council debate.

    All 7 agents run in PARALLEL per round. Tokens from different agents
    are interleaved on the SSE stream so the UI can show live progress
    for every agent simultaneously.

    Event types:
      - round_start: {round: 1|2|3, phase: "analysis"|"debate"|"supervisor"}
      - agent_start: {agent: "analyst", round: 1}
      - token: {agent: "analyst", round: 1, content: "..."}
      - agent_done: {agent: "analyst", round: 1, confidence: 87}
      - moderator_start: {round: 1}
      - moderator_done: {round: 1, scores: {...}, consensus: 72}
      - supervisor_done: {verdict: "...", confidence: 85, reliable_agents: [...]}
      - complete: {session_id: "..."}
    """
    query = sanitize_input(request.query)
    session_id = str(uuid.uuid4())

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'query': query})}\n\n"

        # ── ROUND 1: Parallel Analysis ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 1, 'phase': 'analysis'})}\n\n"

        r1_outputs: dict[str, str] = {}
        r1_confidences: dict[str, float] = {}
        queue: asyncio.Queue = asyncio.Queue()

        r1_tasks = [
            asyncio.create_task(
                _run_agent_parallel(
                    agent_key=key,
                    agent_info=info,
                    messages=[
                        {"role": "system", "content": info["prompt"]},
                        {"role": "user", "content": f"Analyze for: {query}"},
                    ],
                    round_num=1,
                    queue=queue,
                    outputs=r1_outputs,
                    confidences=r1_confidences,
                    default_confidence=50.0,
                )
            )
            for key, info in SEVEN_AGENTS.items()
        ]

        # Drain the queue (interleaved events from all 7 agents) while tasks run
        async for event_str in _drain_queue(queue, len(SEVEN_AGENTS)):
            yield event_str

        # Ensure all tasks finished
        await asyncio.gather(*r1_tasks, return_exceptions=True)

        # ── MODERATOR Round 1 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 1})}\n\n"
        moderator_r1 = await _run_moderator(query, r1_outputs, r1_confidences, 1)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 1, **moderator_r1})}\n\n"

        # ── ROUND 2: Parallel Debate (react to Round 1) ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 2, 'phase': 'debate'})}\n\n"

        r2_outputs: dict[str, str] = {}
        r2_confidences: dict[str, float] = {}
        queue2: asyncio.Queue = asyncio.Queue()

        r2_tasks = [
            asyncio.create_task(
                _run_agent_parallel(
                    agent_key=key,
                    agent_info=info,
                    messages=[
                        {"role": "system", "content": info["prompt"]},
                        {"role": "user", "content": (
                            f"Original query: {query}\n\n"
                            + "Other agents' Round 1 analyses:\n"
                            + "\n".join([
                                f"**{SEVEN_AGENTS[k]['label']}**: {v[:500]}"
                                for k, v in r1_outputs.items() if k != key
                            ])
                            + "\n\nNow provide your updated analysis considering their perspectives."
                        )},
                    ],
                    round_num=2,
                    queue=queue2,
                    outputs=r2_outputs,
                    confidences=r2_confidences,
                    default_confidence=r1_confidences.get(key, 50.0),
                )
            )
            for key, info in SEVEN_AGENTS.items()
        ]

        async for event_str in _drain_queue(queue2, len(SEVEN_AGENTS)):
            yield event_str

        await asyncio.gather(*r2_tasks, return_exceptions=True)

        # ── MODERATOR Round 2 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 2})}\n\n"
        moderator_r2 = await _run_moderator(query, r2_outputs, r2_confidences, 2)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 2, **moderator_r2})}\n\n"

        # ── ROUND 3: Supervisor ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 3, 'phase': 'supervisor'})}\n\n"

        supervisor_context = f"""
MODERATOR ROUND 1 SUMMARY:
{moderator_r1.get('summary', '')}

Agent Scores Round 1: {json.dumps(moderator_r1.get('scores', {}))}
Consensus Round 1: {moderator_r1.get('consensus', 0)}%

MODERATOR ROUND 2 SUMMARY:
{moderator_r2.get('summary', '')}

Agent Scores Round 2: {json.dumps(moderator_r2.get('scores', {}))}
Consensus Round 2: {moderator_r2.get('consensus', 0)}%
"""

        sup_messages = [
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user", "content": f"Original query: {query}\n\n{supervisor_context}\n\nProvide your final verdict."},
        ]

        supervisor_output = ""
        sup_confidence = 0.0
        yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'supervisor', 'round': 3})}\n\n"

        try:
            async for token in llm_router.stream_with_fallback("moderator", sup_messages):
                supervisor_output += token
                yield f"data: {json.dumps({'type': 'token', 'agent': 'supervisor', 'round': 3, 'content': token})}\n\n"
        except Exception as e:
            supervisor_output = f"Supervisor unavailable: {e}"
            yield f"data: {json.dumps({'type': 'agent_error', 'agent': 'supervisor', 'round': 3, 'error': str(e)})}\n\n"

        sup_confidence = _parse_confidence(supervisor_output, moderator_r2.get('consensus', 50))

        yield f"data: {json.dumps({'type': 'supervisor_done', 'round': 3, 'confidence': sup_confidence, 'output_preview': supervisor_output[:200]})}\n\n"

        # ── COMPLETE ──
        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'confidence': sup_confidence, 'recommendation': supervisor_output})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _run_moderator(query: str, agent_outputs: dict[str, str], agent_confidences: dict[str, float], round_num: int) -> dict:
    """Run moderator to score and summarize agent outputs."""
    agent_summaries = "\n".join([
        f"- {SEVEN_AGENTS[k]['label']} (confidence {agent_confidences.get(k, 0):.0f}%): {v[:400]}"
        for k, v in agent_outputs.items()
    ])

    scoring_prompt = f"""You are the Council Moderator. Score each agent's contribution and summarize the debate.

Query: {query}
Round: {round_num}

Agent Outputs:
{agent_summaries}

For each agent, assign a contribution percentage (0-100) representing how valuable their input was.
Also provide an overall consensus score (0-100) representing how much the agents agree.

Return JSON only:
{{
  "scores": {{"analyst": 87, "critic": 73, "creative": 65, "risk": 80, "legal": 70, "market": 75, "optimizer": 82}},
  "consensus": 72,
  "summary": "Brief summary of key findings and disagreements"
}}"""

    messages = [
        {"role": "system", "content": MODERATOR_PROMPT},
        {"role": "user", "content": scoring_prompt},
    ]

    try:
        response, _ = await llm_router.invoke_with_fallback("moderator", messages)
        # Try to parse JSON from response
        content = response.content
        # Extract JSON from response (may have markdown wrapping)
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "scores": parsed.get("scores", agent_confidences),
                "consensus": parsed.get("consensus", 50),
                "summary": parsed.get("summary", content[:500]),
            }
    except Exception as e:
        logger.warning(f"Moderator scoring failed for round {round_num}: {e}")

    # Fallback: use agent confidences as scores
    return {
        "scores": agent_confidences,
        "consensus": sum(agent_confidences.values()) / len(agent_confidences) if agent_confidences else 50,
        "summary": "Moderator scoring unavailable; using agent self-reported confidences.",
    }


def _parse_confidence(text: str, default: float) -> float:
    """Extract confidence score from LLM response text."""
    import re
    patterns = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"confidence\s+score[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*%\s*confidence",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return min(val, 100.0) if val > 1 else val * 100
    return default
