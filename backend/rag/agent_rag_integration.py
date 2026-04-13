"""Agent-RAG integration for SupplyChainGPT Council.

Provides domain-specific AgenticRAG retrievers for each of the 7 agents,
and helpers to inject RAG context into agent messages before LLM invocation.

Each agent gets:
  - A dedicated AgenticRAG instance with its own collection and profile
  - Optional GraphRAG context for supply/logistics agents
  - A helper function that pre-fetches RAG context and appends it to the
    agent's user message

Usage in agents/risk_agent.py:
    from backend.rag.agent_rag_integration import get_rag_context
    rag_ctx = await get_rag_context("risk", query)
    messages.append({"role": "system", "content": f"Retrieved Context:\\n{rag_ctx}"})
"""

import logging
from typing import Optional

from backend.rag.agentic_rag import AgenticRAG
from backend.rag.graph_rag import HybridCypherRetriever, get_graph_retriever
from backend.rag.rag_config import AGENT_RAG_PROFILES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Singleton AgenticRAG instances per agent
# ---------------------------------------------------------------------------
_agent_rag_instances: dict[str, AgenticRAG] = {}


def get_agent_rag(agent_name: str) -> AgenticRAG:
    """Get or create the AgenticRAG instance for a specific agent."""
    if agent_name not in _agent_rag_instances:
        profile = AGENT_RAG_PROFILES.get(agent_name, AGENT_RAG_PROFILES["risk"])
        _agent_rag_instances[agent_name] = AgenticRAG(
            agent_name=agent_name,
            collection=profile.get("collection"),
        )
        logger.info(f"Created AgenticRAG for agent '{agent_name}' (collection: {profile.get('collection')})")
    return _agent_rag_instances[agent_name]


# ---------------------------------------------------------------------------
# Domain-specific convenience accessors
# ---------------------------------------------------------------------------
def risk_retriever() -> AgenticRAG:
    """GDELT/news-focused retriever for the Risk Sentinel Agent."""
    return get_agent_rag("risk")


def supply_retriever() -> AgenticRAG:
    """Supplier docs/contracts retriever for the Supply Optimizer Agent."""
    return get_agent_rag("supply")


def logistics_retriever() -> AgenticRAG:
    """Shipping/routes/weather retriever for the Logistics Navigator Agent."""
    return get_agent_rag("logistics")


def market_retriever() -> AgenticRAG:
    """Commodity/trade data retriever for the Market Intelligence Agent."""
    return get_agent_rag("market")


def finance_retriever() -> AgenticRAG:
    """Financial/forex retriever for the Finance Guardian Agent."""
    return get_agent_rag("finance")


def brand_retriever() -> AgenticRAG:
    """Social sentiment/PR retriever for the Brand Protector Agent."""
    return get_agent_rag("brand")


def moderator_retriever() -> AgenticRAG:
    """Cross-domain retriever for the Moderator/Orchestrator Agent."""
    return get_agent_rag("moderator")


# ---------------------------------------------------------------------------
# Graph RAG integration (for supply and logistics agents)
# ---------------------------------------------------------------------------
_agents_with_graph = {"supply", "logistics", "risk", "moderator"}


async def get_graph_context(agent_name: str, query: str) -> Optional[str]:
    """Fetch Graph RAG context for agents that need supplier graph data.

    Only supply, logistics, risk, and moderator agents use graph context.
    Returns formatted string or None if agent doesn't use graph or query fails.
    """
    if agent_name not in _agents_with_graph:
        return None

    try:
        retriever = get_graph_retriever(use_llm=False, combine_vector=False)
        result = await retriever.retrieve(query)
        context = retriever.format_graph_context(result)
        if context and context != "No graph data available for this query.":
            return context
        return None
    except Exception as e:
        logger.warning(f"[{agent_name}] Graph RAG context failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main integration function: get RAG context for an agent
# ---------------------------------------------------------------------------
async def get_rag_context(agent_name: str, query: str, include_graph: bool = True) -> str:
    """Fetch combined Agentic RAG + Graph RAG context for an agent.

    This is the primary entry point for agents to get RAG context.
    Returns a formatted string ready to inject into the LLM prompt.

    Args:
        agent_name: One of risk, supply, logistics, market, finance, brand, moderator
        query: The user's query or the agent's task description
        include_graph: Whether to include Neo4j graph context (default True)

    Returns:
        Formatted context string with sources and confidence info.
    """
    context_parts = []

    # Step 1: Agentic RAG (vector + BM25 + critique + self-reflection)
    try:
        rag = get_agent_rag(agent_name)
        result = await rag.run(query)

        if result.get("context"):
            context_parts.append(f"--- Retrieved Documents (confidence: {result['confidence']:.0%}, loops: {result['loops_used']}) ---")
            context_parts.append(result["context"])

        # Add source citations
        if result.get("sources"):
            sources_str = ", ".join(
                f"[{s['id']}] {s.get('source', 'unknown')}" for s in result["sources"][:10]
            )
            context_parts.append(f"Sources: {sources_str}")

        # Log escalation
        if result.get("escalated"):
            context_parts.append("(Note: RAG confidence was low — escalated to MCP tools for additional data)")

    except Exception as e:
        logger.warning(f"[{agent_name}] Agentic RAG failed: {e}")
        context_parts.append(f"(RAG retrieval unavailable: {e})")

    # Step 2: Graph RAG (Neo4j supplier graph)
    if include_graph:
        graph_ctx = await get_graph_context(agent_name, query)
        if graph_ctx:
            context_parts.append("--- Supply Chain Graph Data ---")
            context_parts.append(graph_ctx)

    return "\n\n".join(context_parts) if context_parts else ""


# ---------------------------------------------------------------------------
# Helper to inject RAG context into agent state/messages
# ---------------------------------------------------------------------------
def inject_rag_into_messages(messages: list[dict], rag_context: str) -> list[dict]:
    """Inject RAG context into the agent's message list.

    Adds a system message with the retrieved context before the user message.
    If a RAG context system message already exists, updates it.
    """
    if not rag_context:
        return messages

    rag_message = {
        "role": "system",
        "content": f"You have access to the following retrieved context. Use it to inform your analysis and cite sources where applicable.\n\n{rag_context}",
    }

    # Check if a RAG context message already exists and update it
    for i, msg in enumerate(messages):
        if msg.get("role") == "system" and "retrieved context" in msg.get("content", "").lower():
            messages[i] = rag_message
            return messages

    # Insert RAG context as a system message before the last user message
    # (so it's after the main system prompt but before the user query)
    inserted = False
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            messages.insert(i, rag_message)
            inserted = True
            break

    if not inserted:
        messages.append(rag_message)

    return messages


# ---------------------------------------------------------------------------
# Batch RAG pre-fetch for all agents (used by graph.py RAG node)
# ---------------------------------------------------------------------------
async def prefetch_rag_for_all_agents(query: str) -> dict[str, str]:
    """Pre-fetch RAG context for all 6 domain agents in parallel.

    Used by the RAG pre-fetch node in graph.py before agent fan-out.
    Returns a dict mapping agent_name → rag_context_string.
    """
    import asyncio

    agent_names = ["risk", "supply", "logistics", "market", "finance", "brand"]
    tasks = [get_rag_context(name, query, include_graph=(name in _agents_with_graph)) for name in agent_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    context_map = {}
    for name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            logger.error(f"RAG prefetch failed for {name}: {result}")
            context_map[name] = ""
        else:
            context_map[name] = result

    logger.info(f"RAG prefetch complete for {len(context_map)} agents")
    return context_map
