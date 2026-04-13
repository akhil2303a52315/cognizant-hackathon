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
    google_api_key: str = ""
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

    # External Data APIs
    newsapi_key: str = ""
    firecrawl_api_key: str = ""
    finnhub_api_key: str = ""
    fred_api_key: str = ""
    bytez_api_key: str = ""
    gemini_api_key: str = ""
    comtrade_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
