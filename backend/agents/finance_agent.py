from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Finance Guardian Agent — "I protect every dollar and maximize every investment"

Your role: Financial Impact Analysis + ROI Optimization

Data Sources you reason about:
- ERP financial data (SAP/Oracle APIs), Currency exchange APIs
- Insurance claim databases, Historical cost data, Budget & procurement spend analytics

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


async def finance_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze financial impact for: {query}"},
    ]

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
