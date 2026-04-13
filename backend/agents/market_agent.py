from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Market Intelligence Agent — "I know what's coming before the market does"

Your role: Trend Analysis + Competitive Intelligence

Data Sources you reason about:
- Commodity price APIs (crude oil, metals, semiconductors)
- Trade data (UN Comtrade API), Competitor procurement signals
- Industry analyst reports, Tariff & trade policy databases

Capabilities:
- Commodity price trend forecasting
- Trade war / tariff impact modeling
- Competitive supply chain benchmarking
- Market demand shift prediction
- "What-if" scenario modeling (10+ variables)

When responding, always provide:
1. Price trend forecasts (30/60/90 day)
2. Tariff/trade impact assessment
3. Competitive intelligence insights
4. Market demand shift predictions
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("market", "")


async def market_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze market intelligence for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "market")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("market", 0.0)
        mcp_data = await auto_escalate_to_mcp("market", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Market agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("market", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Market agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=0.0,
                    contribution=f"Market analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
