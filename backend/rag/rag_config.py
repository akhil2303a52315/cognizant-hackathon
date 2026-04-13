"""Centralized RAG configuration for SupplyChainGPT Council.

Pulls all RAG-related settings from backend.config.settings and env vars.
Provides domain-specific collection names and retrieval profiles for each agent.
"""

import os
import logging
from backend.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedding configuration
# ---------------------------------------------------------------------------
EMBEDDING_PROVIDERS = {
    "huggingface": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
    },
    "openai": {
        "model": "text-embedding-3-small",
        "dimension": 1536,
    },
}

DEFAULT_EMBEDDING_PROVIDER = os.environ.get("RAG_EMBEDDING_PROVIDER", "huggingface")


# ---------------------------------------------------------------------------
# Vector store configuration
# ---------------------------------------------------------------------------
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", settings.pinecone_index_name)
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data")
DEFAULT_COLLECTION = "supplychaingpt"


# ---------------------------------------------------------------------------
# Neo4j / Graph RAG configuration
# ---------------------------------------------------------------------------
NEO4J_URI = os.environ.get("NEO4J_URI", settings.neo4j_uri)
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", settings.neo4j_password)


# ---------------------------------------------------------------------------
# Chunking defaults (override via settings)
# ---------------------------------------------------------------------------
CHUNK_SIZE = settings.rag_chunk_size          # 512 by default
CHUNK_OVERLAP = settings.rag_chunk_overlap    # 50 by default
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


# ---------------------------------------------------------------------------
# Retrieval profiles per agent domain
# ---------------------------------------------------------------------------
AGENT_RAG_PROFILES = {
    "risk": {
        "collection": "risk-events-gdelt",
        "top_k": 6,
        "recency_days": 7,
        "confidence_threshold": 0.70,
        "description": "GDELT events, news, geopolitical risk data",
        "mcp_escalation_tools": ["gdelt_search_events", "newsapi_top_headlines", "gdelt_search_gkg"],
    },
    "supply": {
        "collection": "supplier-docs",
        "top_k": 6,
        "recency_days": 30,
        "confidence_threshold": 0.65,
        "description": "Supplier contracts, SOPs, capability matrices",
        "mcp_escalation_tools": ["search_suppliers", "supplier_risk_score"],
    },
    "logistics": {
        "collection": "logistics-routes",
        "top_k": 6,
        "recency_days": 3,
        "confidence_threshold": 0.70,
        "description": "Shipping routes, port congestion, weather alerts",
        "mcp_escalation_tools": ["get_shipping_routes", "weather_current", "usgs_earthquakes"],
    },
    "market": {
        "collection": "market-intelligence",
        "top_k": 6,
        "recency_days": 7,
        "confidence_threshold": 0.65,
        "description": "Commodity prices, trade data, market trends",
        "mcp_escalation_tools": ["finnhub_stock_quote", "fred_commodity_price", "comtrade_trade_data"],
    },
    "finance": {
        "collection": "finance-forex",
        "top_k": 6,
        "recency_days": 1,
        "confidence_threshold": 0.75,
        "description": "Financial reports, currency exchange, insurance claims",
        "mcp_escalation_tools": ["frankfurter_latest_rates", "finnhub_stock_quote"],
    },
    "brand": {
        "collection": "brand-sentiment",
        "top_k": 6,
        "recency_days": 3,
        "confidence_threshold": 0.60,
        "description": "Social sentiment, PR news, crisis communications",
        "mcp_escalation_tools": ["reddit_search", "newsapi_top_headlines", "wikipedia_search"],
    },
    "moderator": {
        "collection": DEFAULT_COLLECTION,
        "top_k": 8,
        "recency_days": 7,
        "confidence_threshold": 0.70,
        "description": "Cross-domain council knowledge base",
        "mcp_escalation_tools": ["rag_query"],
    },
}


# ---------------------------------------------------------------------------
# Agentic RAG parameters
# ---------------------------------------------------------------------------
CRITIQUE_TOP_K = 6                          # docs to retrieve before critique
CRITIQUE_LLM_AGENT = "market"               # LLM routing key for critique
SELF_REFLECTION_THRESHOLD = 0.70            # re-retrieve if confidence < 70%
MAX_RETRIEVAL_LOOPS = 2                     # max self-reflection re-retrievals
RECENCY_BOOST_FACTOR = 1.3                  # score multiplier for docs < recency_days
VECTOR_DRIFT_THRESHOLD = 0.15               # cosine drift threshold for alert


def get_agent_profile(agent_name: str) -> dict:
    """Return the RAG profile for a given agent, with fallback to defaults."""
    profile = AGENT_RAG_PROFILES.get(agent_name, AGENT_RAG_PROFILES["risk"]).copy()
    profile["agent"] = agent_name
    return profile


def get_rag_settings() -> dict:
    """Return a summary dict of all RAG settings for diagnostics."""
    return {
        "embedding_provider": DEFAULT_EMBEDDING_PROVIDER,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "default_collection": DEFAULT_COLLECTION,
        "pinecone_index": PINECONE_INDEX_NAME,
        "neo4j_uri": NEO4J_URI,
        "critique_top_k": CRITIQUE_TOP_K,
        "self_reflection_threshold": SELF_REFLECTION_THRESHOLD,
        "max_retrieval_loops": MAX_RETRIEVAL_LOOPS,
        "vector_drift_threshold": VECTOR_DRIFT_THRESHOLD,
        "agent_profiles": list(AGENT_RAG_PROFILES.keys()),
    }
