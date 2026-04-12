from langgraph.graph import StateGraph, END
from backend.state import CouncilState
from backend.agents.moderator import moderator_parse, moderator_synthesize
from backend.agents.risk_agent import risk_agent
from backend.agents.supply_agent import supply_agent
from backend.agents.logistics_agent import logistics_agent
from backend.agents.market_agent import market_agent
from backend.agents.finance_agent import finance_agent
from backend.agents.brand_agent import brand_agent
from backend.agents.supervisor import should_debate
import logging

logger = logging.getLogger(__name__)


def build_council_graph() -> StateGraph:
    graph = StateGraph(CouncilState)

    # Add all nodes
    graph.add_node("moderator", moderator_parse)
    graph.add_node("risk", risk_agent)
    graph.add_node("supply", supply_agent)
    graph.add_node("logistics", logistics_agent)
    graph.add_node("market", market_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("brand", brand_agent)
    graph.add_node("synthesize", moderator_synthesize)

    graph.set_entry_point("moderator")

    # Fan-out from moderator to all 6 domain agents
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge("moderator", agent)
        graph.add_conditional_edges(agent, should_debate, {
            "debate": "moderator",
            "synthesize": "synthesize",
        })

    graph.add_edge("synthesize", END)

    return graph
