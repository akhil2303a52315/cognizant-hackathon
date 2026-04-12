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


async def supply_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Find supply alternatives for: {query}"},
    ]

    try:
        response, model_used = await llm_router.invoke_with_fallback("supply", messages)
        return {
            "agent_outputs": state.get("agent_outputs", []) + [
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
            "agent_outputs": state.get("agent_outputs", []) + [
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
