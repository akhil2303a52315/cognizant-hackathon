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


# ---------------------------------------------------------------------------
# Day 3: RAG Pre-fetch node
# ---------------------------------------------------------------------------
async def rag_prefetch(state: CouncilState) -> dict:
    """RAG pre-fetch node: fetch context for all agents before fan-out."""
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


# ---------------------------------------------------------------------------
# Day 4: MCP Escalation node
# ---------------------------------------------------------------------------
async def mcp_escalation(state: CouncilState) -> dict:
    """MCP escalation node: auto-call MCP tools for agents with low RAG confidence."""
    query = state.get("query", "")
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {} if context else {}

    rag_meta = {}
    for agent_name, rag_ctx in rag_contexts.items():
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


# ---------------------------------------------------------------------------
# Day 5: Predictions node
# ---------------------------------------------------------------------------
async def predictions_node(state: CouncilState) -> dict:
    """Generate ensemble predictions (price, disruption, lead time) for the debate."""
    query = state.get("query", "")
    if not query:
        return {"predictions": []}

    try:
        from backend.predictions_engine import generate_predictions_for_debate
        preds = await generate_predictions_for_debate(query, state)
        logger.info(f"Generated {len(preds)} predictions")
        return {"predictions": preds}
    except Exception as e:
        logger.warning(f"Predictions node failed: {e}")
        return {"predictions": []}


# ---------------------------------------------------------------------------
# Day 5: Debate Engine node
# ---------------------------------------------------------------------------
async def debate_node(state: CouncilState) -> dict:
    """Run the 3-round structured debate engine.

    After all agents have contributed, the DebateEngine orchestrates:
      Round 1: Parallel Analysis summary
      Round 2: Challenge & Counter phase
      Round 3: Validation & Synthesis

    Produces: debate_rounds, confidence, risk_score, recommendation, fallback_options
    """
    try:
        from backend.debate_engine import debate_engine
        result = await debate_engine.run_debate(state)
        logger.info(
            f"Debate complete: {len(result.get('debate_rounds', []))} rounds, "
            f"confidence={result.get('confidence', 0):.2f}, "
            f"risk={result.get('risk_score', 0):.1f}"
        )
        return result
    except Exception as e:
        logger.error(f"Debate engine failed: {e}")
        return {
            "debate_rounds": [],
            "confidence": 0.0,
            "risk_score": 50.0,
            "recommendation": f"Debate engine failed: {e}",
            "fallback_options": [],
        }


# ---------------------------------------------------------------------------
# Day 5: Fallback Engine node
# ---------------------------------------------------------------------------
async def fallback_node(state: CouncilState) -> dict:
    """Generate tiered fallback options based on debate and prediction results."""
    try:
        from backend.fallback_engine import fallback_engine
        result = await fallback_engine.generate_fallbacks(state)
        n = len(result.get("tiered_fallbacks", []))
        logger.info(f"Generated {n} tiered fallback options")
        return result
    except Exception as e:
        logger.warning(f"Fallback engine failed: {e}")
        return {"tiered_fallbacks": []}


# ---------------------------------------------------------------------------
# Day 5: Brand Enhancement node
# ---------------------------------------------------------------------------
async def brand_enhancement_node(state: CouncilState) -> dict:
    """Run brand sentiment analysis, crisis comms, ad pivot, and competitor analysis."""
    try:
        from backend.brand_agent_enhancement import brand_enhancer
        result = await brand_enhancer.run_full_enhancement(state)
        sentiment = result.get("brand_sentiment", {})
        logger.info(f"Brand enhancement: sentiment={sentiment.get('overall_sentiment', 'unknown')}")
        return result
    except Exception as e:
        logger.warning(f"Brand enhancement failed: {e}")
        return {"brand_sentiment": None}


# ---------------------------------------------------------------------------
# Day 5: Conditional edge — should we run brand enhancement?
# ---------------------------------------------------------------------------
def needs_brand_enhancement(state: CouncilState) -> str:
    """Route to brand enhancement if brand agent detected negative sentiment."""
    agent_outputs = state.get("agent_outputs", [])
    for o in agent_outputs:
        if o.agent == "brand" and o.confidence < 50:
            return "brand_enhancement"
    # Check if query mentions brand/reputation/PR keywords
    query = (state.get("query") or "").lower()
    brand_keywords = ["brand", "reputation", "pr", "crisis", "sentiment", "social media", "consumer"]
    if any(kw in query for kw in brand_keywords):
        return "brand_enhancement"
    return "skip_brand"


# ---------------------------------------------------------------------------
# Build the full council graph
# ---------------------------------------------------------------------------
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
    graph.add_node("predictions", predictions_node)
    graph.add_node("debate", debate_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("brand_enhancement", brand_enhancement_node)
    graph.add_node("synthesize", moderator_synthesize)

    graph.set_entry_point("moderator")

    # Phase 1: Moderator → RAG → MCP → Agent fan-out
    graph.add_edge("moderator", "rag_prefetch")
    graph.add_edge("rag_prefetch", "mcp_escalation")

    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge("mcp_escalation", agent)

    # Phase 2: After all agents → Predictions → Debate → Fallback
    # All agents converge to predictions node
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge(agent, "predictions")

    graph.add_edge("predictions", "debate")
    graph.add_edge("debate", "fallback")

    # Phase 3: Conditional brand enhancement
    graph.add_conditional_edges("fallback", needs_brand_enhancement, {
        "brand_enhancement": "brand_enhancement",
        "skip_brand": "synthesize",
    })
    graph.add_edge("brand_enhancement", "synthesize")

    # Final synthesis
    graph.add_edge("synthesize", END)

    return graph
