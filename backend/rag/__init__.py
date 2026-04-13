# RAG package

from backend.rag.rag_config import (
    get_agent_profile,
    get_rag_settings,
    AGENT_RAG_PROFILES,
    CRITIQUE_TOP_K,
    SELF_REFLECTION_THRESHOLD,
    MAX_RETRIEVAL_LOOPS,
    VECTOR_DRIFT_THRESHOLD,
)
from backend.rag.base_rag import BaseRAG
from backend.rag.agentic_rag import AgenticRAG
from backend.rag.graph_rag import HybridCypherRetriever, get_graph_retriever, graph_rag_query
from backend.rag.agent_rag_integration import (
    get_agent_rag,
    get_rag_context,
    inject_rag_into_messages,
    prefetch_rag_for_all_agents,
    risk_retriever,
    supply_retriever,
    logistics_retriever,
    market_retriever,
    finance_retriever,
    brand_retriever,
    moderator_retriever,
)

__all__ = [
    # Config
    "get_agent_profile",
    "get_rag_settings",
    "AGENT_RAG_PROFILES",
    "CRITIQUE_TOP_K",
    "SELF_REFLECTION_THRESHOLD",
    "MAX_RETRIEVAL_LOOPS",
    "VECTOR_DRIFT_THRESHOLD",
    # Core classes
    "BaseRAG",
    "AgenticRAG",
    "HybridCypherRetriever",
    "get_graph_retriever",
    "graph_rag_query",
    # Agent integration
    "get_agent_rag",
    "get_rag_context",
    "inject_rag_into_messages",
    "prefetch_rag_for_all_agents",
    # Domain-specific retrievers
    "risk_retriever",
    "supply_retriever",
    "logistics_retriever",
    "market_retriever",
    "finance_retriever",
    "brand_retriever",
    "moderator_retriever",
]
