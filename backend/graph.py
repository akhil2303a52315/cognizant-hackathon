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


async def rag_prefetch(state: CouncilState) -> dict:
    """RAG pre-fetch node: fetch context for all agents before fan-out.

    Runs Agentic RAG + Graph RAG for the query and stores per-agent
    context in state['context']['rag_contexts'] so each agent can
    inject it into their LLM messages.
    """
    query = state.get("query", "")
    if not query:
        return {"context": {**(state.get("context") or {}), "rag_contexts": {}}}

    try:
        from backend.rag.agent_rag_integration import prefetch_rag_for_all_agents
        rag_contexts = await prefetch_rag_for_all_agents(query)
        logger.info(f"RAG prefetch complete for {len(rag_contexts)} agents")
        return {"context": {**(state.get("context") or {}), "rag_contexts": rag_contexts}}
    except Exception as e:
        logger.warning(f"RAG prefetch node failed (agents will proceed without RAG): {e}")
        return {"context": {**(state.get("context") or {}), "rag_contexts": {}}}


async def mcp_escalation(state: CouncilState) -> dict:
    """MCP escalation node: auto-call MCP tools for agents with low RAG confidence.

    Runs after RAG pre-fetch. Checks each agent's RAG confidence and
    calls relevant MCP tools for agents below their confidence threshold.
    Stores MCP results in state['context']['mcp_contexts'] and
    RAG confidence metadata in state['context']['rag_meta'].
    """
    query = state.get("query", "")
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {} if context else {}

    # Extract RAG confidence from each agent's context (heuristic)
    rag_meta = {}
    for agent_name, rag_ctx in rag_contexts.items():
        # Parse confidence from the RAG context string
        confidence = 0.0
        if "confidence:" in rag_ctx:
            try:
                import re
                match = re.search(r"confidence:\s*(\d+)%", rag_ctx)
                if match:
                    confidence = int(match.group(1)) / 100.0
            except Exception:
                pass
        rag_meta[agent_name] = confidence

    if not query:
        return {"context": {**context, "rag_meta": rag_meta, "mcp_contexts": {}}}

    try:
        from backend.mcp.agent_mcp_integration import prefetch_mcp_for_all_agents
        mcp_contexts = await prefetch_mcp_for_all_agents(query, rag_confidences=rag_meta)
        escalated = [n for n, c in mcp_contexts.items() if c]
        if escalated:
            logger.info(f"MCP escalation: auto-called tools for agents {escalated}")
        return {"context": {**context, "rag_meta": rag_meta, "mcp_contexts": mcp_contexts}}
    except Exception as e:
        logger.warning(f"MCP escalation node failed: {e}")
        return {"context": {**context, "rag_meta": rag_meta, "mcp_contexts": {}}}


def build_council_graph() -> StateGraph:
    graph = StateGraph(CouncilState)

    # Add all nodes
    graph.add_node("moderator", moderator_parse)
    graph.add_node("rag_prefetch", rag_prefetch)
    graph.add_node("mcp_escalation", mcp_escalation)
    graph.add_node("risk", risk_agent)
    graph.add_node("supply", supply_agent)
    graph.add_node("logistics", logistics_agent)
    graph.add_node("market", market_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("brand", brand_agent)
    graph.add_node("synthesize", moderator_synthesize)

    graph.set_entry_point("moderator")

    # Moderator → RAG pre-fetch → MCP escalation → agent fan-out
    graph.add_edge("moderator", "rag_prefetch")
    graph.add_edge("rag_prefetch", "mcp_escalation")

    # Fan-out from MCP escalation to all 6 domain agents
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge("mcp_escalation", agent)
        graph.add_conditional_edges(agent, should_debate, {
            "debate": "moderator",
            "synthesize": "synthesize",
        })

    graph.add_edge("synthesize", END)

    return graph
