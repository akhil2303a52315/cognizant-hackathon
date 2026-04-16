from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "SupplyChainGPT Council API"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # LLM Providers
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    cohere_api_key: str = ""
    sambanova_api_key: str = ""

    # Databases
    database_url: str = ""
    neon_database_url: str = ""
    postgres_uri: str = ""
    redis_url: str = "redis://localhost:6379"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_password: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "supplychaingpt"

    # RAG
    huggingface_api_key: str = ""
    unstructured_api_key: str = ""
    openai_api_key: str = ""

    # Observability
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "supplychaingpt-council"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_cost_tracking: bool = True
    langsmith_trace_sample_rate: float = 1.0  # 0.0-1.0 for sampling

    # Prometheus Metrics
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100
    ws_debate_buffer_size: int = 1000

    # Security
    security_headers_enabled: bool = True
    prompt_injection_guard: bool = True
    pii_redaction_enabled: bool = True
    max_query_length: int = 2000

    # Session Storage
    session_store_ttl: int = 86400  # 24h Redis TTL for council sessions

    # External Data APIs
    newsapi_key: str = ""
    firecrawl_api_key: str = ""
    firecrawl_base_url: str = ""  # Self-hosted Firecrawl URL (e.g. http://localhost:3002)
    finnhub_api_key: str = ""
    fred_api_key: str = ""
    bytez_api_key: str = ""
    comtrade_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""

    # New External Data APIs (Day 7+)
    alpha_vantage_api_key: str = ""
    polygon_api_key: str = ""
    openweathermap_api_key: str = ""
    mediastack_api_key: str = ""
    noaa_api_key: str = ""
    nist_nvd_api_key: str = ""
    currents_api_key: str = ""

    # Additional External Data APIs (Day 7+)
    twelvedata_api_key: str = ""
    fmp_api_key: str = ""  # Financial Modeling Prep
    shodan_api_key: str = ""
    exchangerate_api_key: str = ""
    gnews_api_key: str = ""
    marketaux_api_key: str = ""
    graphhopper_api_key: str = ""

    # App
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    api_keys: str = "dev-key"
    mcp_api_key: str = "dev-mcp-key"
    rate_limit_per_minute: int = 60
    mcp_rate_limit: int = 30

    # RAG Settings
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_cache_ttl: int = 3600

    # Council Settings
    max_debate_rounds: int = 3
    confidence_gap_threshold: float = 20.0
    human_in_loop: bool = False
    council_lite_mode: bool = False
    enable_self_critique: bool = True
    council_cache_ttl: int = 600  # 10 min cache for identical queries

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
