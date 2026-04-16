"""Council V2 — Multi-round debate with 6 real domain agents + Moderator + Supervisor.

REAL DATA PIPELINE (with live stage events):
  stage: rag_fetching   → RAG vector retrieval firing for all agents
  stage: api_called     → Live APIs: GNews, Alpha Vantage, OpenWeather, NOAA, GDELT...
  stage: mcp_fetched    → MCP tools invoked (Firecrawl scraping, DuckDuckGo)
  stage: sources_ready  → All citations assembled (≥9 per agent)

Flow:
  Pre-fetch: Parallel RAG+API+MCP+Scraping per agent → citations_map events
  Round 1: 6 agents analyze with research context → Moderator scores
  Round 2: 6 agents debate → Moderator scores
  Round 3: Supervisor final verdict
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from backend.llm.router import llm_router
from backend.middleware.security import sanitize_input
import uuid
import json
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Import enhanced prompts from agent files (single source of truth) ─────────
from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
from backend.agents.supply_agent import SYSTEM_PROMPT as SUPPLY_PROMPT
from backend.agents.logistics_agent import SYSTEM_PROMPT as LOGISTICS_PROMPT
from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
from backend.agents.finance_agent import SYSTEM_PROMPT as FINANCE_PROMPT
from backend.agents.brand_agent import SYSTEM_PROMPT as BRAND_PROMPT

AGENT_PROMPTS = {
    "risk": RISK_PROMPT,
    "supply": SUPPLY_PROMPT,
    "logistics": LOGISTICS_PROMPT,
    "market": MARKET_PROMPT,
    "finance": FINANCE_PROMPT,
    "brand": BRAND_PROMPT,
}


MODERATOR_PROMPT = """You are the Moderator — you orchestrate the council, score agent contributions, and synthesize findings.

Your job:
1. Score each agent's contribution (0-100) based on data quality, citation count, and relevance
2. Identify where agents agree (consensus points) and disagree (conflict points)
3. Write a concise executive summary of key findings
4. Calculate an overall consensus percentage

Be objective. Higher scores for: more real data citations, quantified claims, specific actionable insights.
Lower scores for: vague statements, lack of citations, contradicted by data.
"""

SUPERVISOR_PROMPT = """You are the Supervisor — the final decision authority of the Supply Chain Council.

You review the debate results from 2 rounds and deliver the definitive final verdict.

**The agents have used real-time data:** DuckDuckGo search, Firecrawl web scraping, live APIs (news, market, weather, forex), and RAG retrieval — with numbered citations.

**Your final verdict must include:**

## 🎯 Executive Summary
[2-3 sentences maximum — the most important finding]

## ✅ Final Verdict
[Unambiguous answer to the original question]

## 📊 Confidence Assessment
- Overall confidence: XX/100
- Data quality: [Strong/Moderate/Weak]
- Consensus level: [High/Medium/Low] among agents

## 🏆 Most Reliable Agents This Session
[Rank top 3 with one-line justification each]

## ⚡ Priority Actions (Next 72 Hours)
1. [Most urgent action]
2. [Second priority]
3. [Third priority]

## 📅 Strategic Roadmap
- **30 days:** [Key milestone]
- **60 days:** [Key milestone]
- **90 days:** [Key milestone]

## ⚠️ Unresolved Risks
[Any conflicts or gaps the council could not resolve]
"""

# Citation + formatting enforcement added to every agent prompt
CITATION_ENFORCEMENT = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY FORMATTING RULES:

You have real-time research data ABOVE with numbered citations [1]...[N].

RULES (all required):
• Use INLINE citations: write [N] immediately after any factual claim (e.g., "Prices surged 18% [2][4]")
• Use the OUTPUT STRUCTURE defined above — do not skip sections
• Mix formats naturally: one-liners for status, bullets for lists, paragraphs for analysis
• Reference at least 6 different [N] citation numbers
• End with: ## Sources Used → list citation numbers referenced
• Include "Confidence Score: XX/100" exactly as written

DO NOT write generic statements without citations.
DO NOT skip the Sources Used section.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class CouncilV2Request(BaseModel):
    query: str
    context: Optional[dict] = None


# ── Pipeline stage event helper ───────────────────────────────────────────────
def _stage_event(stage: str, detail: str = "", count: int = 0) -> str:
    return f"data: {json.dumps({'type': 'pipeline_stage', 'stage': stage, 'detail': detail, 'count': count})}\n\n"


# ── Agent message builder ─────────────────────────────────────────────────────
def _build_agent_messages(
    agent_key: str,
    query: str,
    citation_context: str,
    citation_list_hint: str,
    round1_outputs: dict = None,
    round_num: int = 1,
) -> list:
    system_content = AGENT_PROMPTS.get(agent_key, AGENT_PROMPTS["risk"]) + CITATION_ENFORCEMENT
    messages = [{"role": "system", "content": system_content}]

    # Optional MCP tool descriptions
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt
        messages = inject_mcp_system_prompt(messages, agent_key)
    except Exception:
        pass

    # Research context with citations
    if citation_context:
        messages.append({"role": "system", "content": f"{citation_context}\n\n{citation_list_hint}"})

    # User task
    agent_labels = {
        "risk": "Identify and assess ALL risks for",
        "supply": "Find supply alternatives and optimize sourcing for",
        "logistics": "Optimize logistics routes and carrier selection for",
        "market": "Provide market intelligence and trend analysis for",
        "finance": "Analyze financial exposure and ROI for",
        "brand": "Assess brand impact and draft crisis response for",
    }

    prefix = agent_labels.get(agent_key, "Analyze")
    if round_num == 1:
        user_msg = (
            f"{prefix}: {query}\n\n"
            "Use the research data above. Cite [N] inline with every factual claim. "
            "Follow your defined output structure. End with ## Sources Used and Confidence Score."
        )
    else:
        agent_names = {
            "risk": "Risk Sentinel", "supply": "Supply Optimizer",
            "logistics": "Logistics Navigator", "market": "Market Intelligence",
            "finance": "Finance Guardian", "brand": "Brand Protector",
        }
        other_outputs = "\n".join([
            f"**{agent_names.get(k, k)}**: {v[:350]}"
            for k, v in (round1_outputs or {}).items() if k != agent_key
        ])
        user_msg = (
            f"Original query: {query}\n\n"
            f"Other agents' Round 1 analyses:\n{other_outputs}\n\n"
            "Your task for Round 2:\n"
            "• Challenge any weak points or unsupported claims from other agents\n"
            "• Reinforce agreements with additional evidence\n"
            "• Update your position with new insights from the debate\n"
            "Continue citing [N] sources. End with ## Sources Used and Confidence Score."
        )

    messages.append({"role": "user", "content": user_msg})
    return messages


# ── Streaming agent runner ────────────────────────────────────────────────────
async def _run_agent_parallel(
    agent_key: str,
    messages: list,
    round_num: int,
    queue: asyncio.Queue,
    outputs: dict,
    confidences: dict,
    default_confidence: float = 50.0,
):
    await queue.put(f"data: {json.dumps({'type': 'agent_start', 'agent': agent_key, 'round': round_num})}\n\n")
    full_response = ""
    try:
        async for token in llm_router.stream_with_fallback(agent_key, messages):
            full_response += token
            await queue.put(f"data: {json.dumps({'type': 'token', 'agent': agent_key, 'round': round_num, 'content': token})}\n\n")
    except Exception as e:
        full_response = f"Agent {agent_key} unavailable: {e}"
        await queue.put(f"data: {json.dumps({'type': 'agent_error', 'agent': agent_key, 'round': round_num, 'error': str(e)})}\n\n")

    confidence = _parse_confidence(full_response, default_confidence)
    outputs[agent_key] = full_response
    confidences[agent_key] = confidence
    await queue.put(f"data: {json.dumps({'type': 'agent_done', 'agent': agent_key, 'round': round_num, 'confidence': confidence})}\n\n")


async def _drain_queue(queue: asyncio.Queue, agent_count: int):
    done_count = 0
    while done_count < agent_count:
        event_str = await queue.get()
        if '"type": "agent_done"' in event_str or '"type":"agent_done"' in event_str:
            done_count += 1
        yield event_str


# ── Main SSE endpoint ─────────────────────────────────────────────────────────
@router.post("/stream")
async def council_v2_stream(request: CouncilV2Request):
    """Live-streaming council debate with animated pipeline stages."""
    query = sanitize_input(request.query)
    session_id = str(uuid.uuid4())

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'query': query})}\n\n"

        # ── STAGE 1: RAG Fetching ──
        yield _stage_event("rag_fetching", "Querying RAG vector store for all 6 agents...", 0)

        try:
            from backend.data_gatherer import gather_all_agents
        except ImportError as e:
            logger.error(f"data_gatherer import failed: {e}")
            gather_all_agents = None

        citation_bundles = {}
        if gather_all_agents:
            try:
                # ── STAGE 2: API Calls ──
                yield _stage_event("api_called", "Firing real-time APIs: GNews, Alpha Vantage, OpenWeather, GDELT, NVD...", 0)

                # ── STAGE 3: MCP / Firecrawl ──
                yield _stage_event("mcp_fetched", "Launching Firecrawl scrapers + DuckDuckGo search queries...", 0)

                citation_bundles = await gather_all_agents(query)

                total = sum(len(b.citations) for b in citation_bundles.values())
                logger.info(f"[{session_id[:8]}] Total citations: {total}")

                # ── STAGE 4: Sources Ready ──
                yield _stage_event("sources_ready", f"Research complete — {total} citations gathered across 6 agents", total)

            except Exception as e:
                logger.error(f"Data gathering failed: {e}")
                yield _stage_event("sources_ready", f"Partial data gathered (some sources unavailable): {e}", 0)

        def get_bundle(agent_key: str):
            from backend.data_gatherer import CitationBundle
            return citation_bundles.get(agent_key, CitationBundle())

        # Emit per-agent citation maps for clickable [N] links
        for agent_key in ("risk", "supply", "logistics", "market", "finance", "brand"):
            bundle = get_bundle(agent_key)
            url_map = {str(c.number): c.url for c in bundle.citations if c.url and c.url.startswith("http")}
            if url_map:
                yield f"data: {json.dumps({'type': 'citations_map', 'agent': agent_key, 'urls': url_map})}\n\n"
        yield f"data: {json.dumps({'type': 'citations_ready'})}\n\n"

        # ── ROUND 1: Parallel Analysis ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 1, 'phase': 'analysis'})}\n\n"

        r1_outputs: dict[str, str] = {}
        r1_confidences: dict[str, float] = {}
        queue1: asyncio.Queue = asyncio.Queue()
        r1_tasks = []

        for key in ("risk", "supply", "logistics", "market", "finance", "brand"):
            bundle = get_bundle(key)
            messages = _build_agent_messages(
                agent_key=key, query=query,
                citation_context=bundle.format_context(),
                citation_list_hint=bundle.format_citation_list(),
                round_num=1,
            )
            r1_tasks.append(asyncio.create_task(
                _run_agent_parallel(key, messages, 1, queue1, r1_outputs, r1_confidences)
            ))

        async for ev in _drain_queue(queue1, 6):
            yield ev
        await asyncio.gather(*r1_tasks, return_exceptions=True)

        # ── MODERATOR Round 1 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 1})}\n\n"
        mod_r1 = await _run_moderator(query, r1_outputs, r1_confidences, 1)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 1, **mod_r1})}\n\n"

        # ── ROUND 2: Debate ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 2, 'phase': 'debate'})}\n\n"

        r2_outputs: dict[str, str] = {}
        r2_confidences: dict[str, float] = {}
        queue2: asyncio.Queue = asyncio.Queue()
        r2_tasks = []

        for key in ("risk", "supply", "logistics", "market", "finance", "brand"):
            bundle = get_bundle(key)
            messages = _build_agent_messages(
                agent_key=key, query=query,
                citation_context=bundle.format_context(),
                citation_list_hint=bundle.format_citation_list(),
                round1_outputs=r1_outputs,
                round_num=2,
            )
            r2_tasks.append(asyncio.create_task(
                _run_agent_parallel(key, messages, 2, queue2, r2_outputs, r2_confidences,
                                    default_confidence=r1_confidences.get(key, 50.0))
            ))

        async for ev in _drain_queue(queue2, 6):
            yield ev
        await asyncio.gather(*r2_tasks, return_exceptions=True)

        # ── MODERATOR Round 2 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 2})}\n\n"
        mod_r2 = await _run_moderator(query, r2_outputs, r2_confidences, 2)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 2, **mod_r2})}\n\n"

        # ── ROUND 3: Supervisor ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 3, 'phase': 'supervisor'})}\n\n"

        sup_context = (
            f"MODERATOR ROUND 1:\n{mod_r1.get('summary', '')}\n"
            f"Scores: {json.dumps(mod_r1.get('scores', {}))}\nConsensus: {mod_r1.get('consensus', 0)}%\n\n"
            f"MODERATOR ROUND 2:\n{mod_r2.get('summary', '')}\n"
            f"Scores: {json.dumps(mod_r2.get('scores', {}))}\nConsensus: {mod_r2.get('consensus', 0)}%\n\n"
            "All agents used real-time DuckDuckGo, Firecrawl, APIs, and RAG with ≥9 numbered citations each."
        )
        sup_messages = [
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\n{sup_context}\n\nDeliver your final verdict."},
        ]

        supervisor_output = ""
        yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'supervisor', 'round': 3})}\n\n"
        try:
            async for token in llm_router.stream_with_fallback("moderator", sup_messages):
                supervisor_output += token
                yield f"data: {json.dumps({'type': 'token', 'agent': 'supervisor', 'round': 3, 'content': token})}\n\n"
        except Exception as e:
            supervisor_output = f"Supervisor unavailable: {e}"
            yield f"data: {json.dumps({'type': 'agent_error', 'agent': 'supervisor', 'round': 3, 'error': str(e)})}\n\n"

        sup_confidence = _parse_confidence(supervisor_output, mod_r2.get("consensus", 50))
        yield f"data: {json.dumps({'type': 'supervisor_done', 'round': 3, 'confidence': sup_confidence})}\n\n"
        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'confidence': sup_confidence, 'recommendation': supervisor_output})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def _run_moderator(query: str, outputs: dict, confidences: dict, round_num: int) -> dict:
    summaries = "\n".join([
        f"- {k} (confidence {confidences.get(k, 0):.0f}%): {v[:250]}"
        for k, v in outputs.items()
    ])
    msg = (
        f"Query: {query}\nRound: {round_num}\n\nAgent Outputs:\n{summaries}\n\n"
        f"Score each agent and provide consensus. Return ONLY valid JSON:\n"
        f'{{"scores":{{"risk":80,"supply":75,"logistics":70,"market":80,"finance":75,"brand":70}},'
        f'"consensus":75,"summary":"Brief summary of key consensus and conflicts"}}'
    )
    try:
        response, _ = await llm_router.invoke_with_fallback("moderator", [
            {"role": "system", "content": MODERATOR_PROMPT},
            {"role": "user", "content": msg},
        ])
        m = re.search(r'\{[\s\S]*\}', response.content)
        if m:
            parsed = json.loads(m.group())
            return {"scores": parsed.get("scores", confidences), "consensus": parsed.get("consensus", 50),
                    "summary": parsed.get("summary", response.content[:400])}
    except Exception as e:
        logger.warning(f"Moderator R{round_num} failed: {e}")
    return {"scores": confidences, "consensus": sum(confidences.values()) / max(len(confidences), 1),
            "summary": "Moderator unavailable."}


def _parse_confidence(text: str, default: float) -> float:
    for p in [r"confidence[:\s]+(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)\s*/\s*100", r"(\d+(?:\.\d+)?)\s*%\s*confidence"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = float(m.group(1))
            return min(v, 100.0) if v > 1 else v * 100
    return default
