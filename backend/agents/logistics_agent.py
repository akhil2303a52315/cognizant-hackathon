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


async def logistics_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Optimize logistics routes for: {query}"},
    ]

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
