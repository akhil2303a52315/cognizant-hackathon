from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Supply Optimizer Agent — "I find you the best supplier, always"

Your role: Demand-Supply Matching + Alternate Sourcing

Data Sources you reason about:
- Supplier Database (Neo4j graph), Historical procurement data
- Global supplier marketplaces, Contract terms database

Capabilities:
- Alternate supplier recommendation engine
- Demand forecasting (seasonal + event-driven)
- Multi-tier supplier mapping (Tier 1, 2, 3 visibility)
- Safety stock optimization
- Lead time comparison across suppliers

When responding, always provide:
1. List of alternate suppliers with capability match %, lead time, location
2. Demand-supply gap analysis
3. Safety stock recommendations
4. Multi-tier dependency warnings
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("supply", "")


async def supply_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Find supply alternatives for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "supply")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("supply", 0.0)
        mcp_data = await auto_escalate_to_mcp("supply", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Supply agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("supply", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="supply",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Supply agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="supply",
                    confidence=0.0,
                    contribution=f"Supply analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
