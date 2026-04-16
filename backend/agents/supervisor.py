from backend.state import CouncilState
from backend.agents.risk_agent import risk_agent
from backend.agents.supply_agent import supply_agent
from backend.agents.logistics_agent import logistics_agent
from backend.agents.market_agent import market_agent
from backend.agents.finance_agent import finance_agent
from backend.agents.brand_agent import brand_agent
from backend.agents.moderator import moderator_parse, moderator_synthesize
import logging

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "risk": risk_agent,
    "supply": supply_agent,
    "logistics": logistics_agent,
    "market": market_agent,
    "finance": finance_agent,
    "brand": brand_agent,
}


def should_debate(state: CouncilState) -> str:
    """Check if debate is needed based on confidence gap between agents."""
    agent_outputs = state.get("agent_outputs", [])
    if len(agent_outputs) < 2:
        return "synthesize"

    confidences = [o.confidence for o in agent_outputs if o.confidence > 0]
    if not confidences:
        return "synthesize"

    max_conf = max(confidences)
    min_conf = min(confidences)
    gap = max_conf - min_conf

    round_number = state.get("round_number", 1)

    # If confidence gap > threshold and rounds remaining, debate
    if gap > 20.0 and round_number < 3:
        return "debate"

    return "synthesize"


async def run_all_agents(state: CouncilState) -> dict:
    """Run all 6 domain agents in parallel (fan-out from moderator)."""
    import asyncio

    tasks = []
    for name, agent_fn in AGENT_MAP.items():
        tasks.append(agent_fn(state))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_outputs = list(state.get("agent_outputs", []))
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Agent {list(AGENT_MAP.keys())[i]} failed: {result}")
        elif isinstance(result, dict):
            outputs = result.get("agent_outputs", [])
            if outputs:
                all_outputs.extend(outputs)

    return {"agent_outputs": all_outputs}
