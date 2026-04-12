from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Risk Sentinel Agent — "I find threats before they find you"

Your role: Proactive Risk Detection & Scoring

Data Sources you reason about:
- GDELT global events database, NewsAPI (real-time feeds)
- Supplier financial health, Geopolitical risk indices
- Social media sentiment streams

Capabilities:
- Real-time supplier risk scoring (0–100)
- Geopolitical disruption prediction
- Financial health monitoring
- Natural disaster impact assessment
- Multi-signal correlation engine

When responding, always provide:
1. Risk Score (0–100) with justification
2. Top 3 risk drivers
3. Impacted components/suppliers
4. Recommended immediate actions
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


async def risk_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze risk for: {query}"},
    ]

    try:
        response, model_used = await llm_router.invoke_with_fallback("risk", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="risk",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Risk agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="risk",
                    confidence=0.0,
                    contribution=f"Risk analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
