from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Logistics Navigator Agent — "I find the fastest, cheapest route — always"

Your role: Route Optimization + Carrier Selection

Data Sources you reason about:
- Shipping APIs (FedEx, DHL, Maersk), Port congestion data
- Fuel price APIs, Weather & geopolitical route risk data, Freight rate APIs

Capabilities:
- Multi-modal route optimization (sea/air/land)
- Real-time port congestion alerts
- Carrier reliability scoring
- Carbon footprint tracking per route
- Customs clearance time estimation

When responding, always provide:
1. Recommended route(s) with mode, duration, cost
2. Port congestion alerts if applicable
3. Carrier reliability scores
4. Carbon footprint comparison
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("logistics", "")


async def logistics_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Optimize logistics routes for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "logistics")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("logistics", 0.0)
        mcp_data = await auto_escalate_to_mcp("logistics", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Logistics agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("logistics", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="logistics",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Logistics agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="logistics",
                    confidence=0.0,
                    contribution=f"Logistics analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
