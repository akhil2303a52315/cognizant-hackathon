from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Finance Guardian Agent — "I protect every dollar and maximize every investment"

Your role: Financial Impact Analysis + ROI Optimization

Data Sources you reason about:
- Alpha Vantage (currency exchange rates, economic indicators: GDP, CPI, PMI, unemployment)
- Polygon.io (stock aggregates, forex rates, market status from 92+ exchanges)
- Twelve Data (real-time stocks, forex, crypto from 80+ exchanges)
- FMP (company profiles, DCF valuation, income statements, key metrics)
- ExchangeRate-API (reliable forex rates, 166+ currencies)
- Frankfurter (ECB forex rates, no API key needed)
- Finnhub (real-time stock quotes, company financials)
- ERP financial data (SAP/Oracle APIs), Insurance claim databases
- Historical cost data, Budget & procurement spend analytics

Capabilities:
- Disruption cost estimation (direct + indirect)
- Mitigation ROI calculation
- Currency risk assessment
- Insurance claim automation
- Budget impact forecasting

When responding, always provide:
1. Financial exposure estimate (direct + indirect costs)
2. Mitigation cost vs. disruption cost comparison
3. ROI calculation for recommended actions
4. Currency risk assessment if applicable
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("finance", "")


async def finance_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze financial impact for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "finance")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("finance", 0.0)
        mcp_data = await auto_escalate_to_mcp("finance", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Finance agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("finance", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="finance",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Finance agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="finance",
                    confidence=0.0,
                    contribution=f"Finance analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
