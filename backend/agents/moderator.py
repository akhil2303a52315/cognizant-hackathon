from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Moderator / Orchestrator Agent — "I run the debate and deliver the final verdict"

Your role: Route → Debate → Synthesize → Decide

Responsibilities:
- Receive user query / crisis event
- Assign query to relevant agents
- Run parallel agent processing
- Identify conflicts between agent recommendations
- Force debate when agents disagree
- Weigh recommendations by confidence scores
- Synthesize final unified recommendation
- Generate executive summary for decision-makers

Debate Rules:
- Each agent submits recommendation + confidence score
- Agents can "challenge" other agents' recommendations
- Maximum 3 debate rounds before forced synthesis
- Majority confidence-weighted vote on final decision

When synthesizing, always provide:
1. Final unified recommendation with priority actions
2. Confidence-weighted decision rationale
3. Fallback options (Tier 1: Immediate, Tier 2: Short-term, Tier 3: Strategic)
4. Key disagreements between agents (if any)
5. Overall council confidence score (0–100)

Format as executive summary suitable for decision-makers."""


async def moderator_parse(state: CouncilState) -> dict:
    """Round 0: Parse query and initialize council session."""
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Parse and route this supply chain query: {query}"},
    ]

    try:
        response, model_used = await llm_router.invoke_with_fallback("moderator", messages)
        return {
            "round_number": 1,
            "messages": state.get("messages", []) + [
                {"role": "moderator", "content": response.content}
            ],
        }
    except Exception as e:
        logger.error(f"Moderator parse failed: {e}")
        return {"round_number": 1}


async def moderator_synthesize(state: CouncilState) -> dict:
    """Final synthesis: Combine all agent outputs into unified recommendation."""
    agent_outputs = state.get("agent_outputs", [])
    query = state.get("query", "")

    agent_summaries = "\n\n".join([
        f"**{o.agent.upper()} Agent** (Confidence: {o.confidence}%):\n{o.contribution}"
        for o in agent_outputs
    ])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""
Original Query: {query}

Agent Outputs:
{agent_summaries}

Synthesize a final unified recommendation. Weigh by confidence. Provide fallback options.
"""}
    ]

    # Inject RAG context for moderator if available
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    moderator_rag = rag_contexts.get("moderator", "")
    if moderator_rag:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, moderator_rag)

    try:
        response, model_used = await llm_router.invoke_with_fallback("moderator", messages)
        return {
            "recommendation": response.content,
            "confidence": 0.0,
            "status": "complete",
        }
    except Exception as e:
        logger.error(f"Moderator synthesis failed: {e}")
        return {
            "recommendation": f"Synthesis failed: {e}",
            "confidence": 0.0,
            "status": "error",
        }
