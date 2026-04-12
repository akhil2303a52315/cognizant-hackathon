# SupplyChainGPT — Backend Specification

Complete backend implementation specification: project structure, setup, dependencies, configuration, all modules, database, API, WebSocket, agents, MCP, RAG, optimization, security, testing, and deployment.

---

## 1. Backend Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND ARCHITECTURE                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    FASTAPI APPLICATION (:8000)                 │ │
│  │                                                               │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │ │
│  │  │ REST API │  │WebSocket│  │ MCP      │  │ Middleware   │   │ │
│  │  │ Routes   │  │ Server  │  │ Server   │  │ Auth/CORS/RL│   │ │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └─────────────┘   │ │
│  │       │             │            │                            │ │
│  │  ┌────▼─────────────▼────────────▼──────────────────────┐   │ │
│  │  │                  CORE ENGINE                           │   │ │
│  │  │                                                       │   │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │ │
│  │  │  │ Council  │  │ LLM      │  │ State Manager     │  │   │ │
│  │  │  │ Graph    │  │ Router   │  │ (Neon PG Checkptr)│  │   │ │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘  │   │ │
│  │  │                                                       │   │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │ │
│  │  │  │ 7 Agents │  │ RAG      │  │ OR-Tools         │  │   │ │
│  │  │  │ + Moder. │  │ Pipeline │  │ Optimizer        │  │   │ │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘  │   │ │
│  │  │                                                       │   │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │ │
│  │  │  │ MCP Tools│  │ Cache    │  │ Audit Logger     │  │   │ │
│  │  │  │ (18+)    │  │ (Redis)  │  │ (Neon PG)        │  │   │ │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘  │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
backend/
├── main.py                     # FastAPI app entry point
├── config.py                   # Environment & configuration
├── state.py                    # CouncilState TypedDict + Pydantic models
├── graph.py                    # LangGraph council graph compilation
│
├── agents/
│   ├── __init__.py
│   ├── risk_agent.py           # Risk Sentinel Agent
│   ├── supply_agent.py         # Supply Optimizer Agent
│   ├── logistics_agent.py      # Logistics Navigator Agent
│   ├── market_agent.py         # Market Intelligence Agent
│   ├── finance_agent.py        # Finance Guardian Agent
│   ├── brand_agent.py          # Brand Protector Agent
│   ├── moderator.py            # Moderator / Orchestrator Agent
│   └── supervisor.py           # Graph builder + routing logic
│
├── llm/
│   ├── __init__.py
│   ├── router.py               # LLM routing across providers
│   ├── providers.py            # Provider client factories
│   ├── fallback.py             # Fallback chain implementation
│   └── config.py               # Model configs + routing table
│
├── rag/
│   ├── __init__.py
│   ├── loader.py               # Document loading (PDF, DOCX, TXT)
│   ├── chunker.py              # Text splitting (512 tokens, 50 overlap)
│   ├── embedder.py             # Embedding router (free/quality)
│   ├── vectorstore.py          # ChromaDB + Pinecone manager
│   ├── retriever.py            # Hybrid retriever (vector + BM25 + rerank)
│   ├── context.py              # Context construction + citation injection
│   ├── generator.py            # LLM generation with grounding
│   ├── graph_rag.py            # Neo4j Graph RAG retriever
│   ├── hybrid_rag.py           # Vector + Graph merged pipeline
│   └── api.py                  # RAG FastAPI router
│
├── mcp/
│   ├── __init__.py
│   ├── server.py               # MCP FastAPI server
│   ├── registry.py             # Tool definition registry
│   ├── sandbox.py              # Sandbox rules + validation
│   ├── sanitize.py             # Prompt injection sanitization
│   ├── audit.py                # MCP audit logging to Neon PG
│   ├── cache.py                # Redis cache for MCP results
│   └── tools/
│       ├── __init__.py
│       ├── news_tools.py       # news_search, gdelt_query, supplier_financials
│       ├── supplier_tools.py   # neo4j_query, supplier_search, contract_lookup
│       ├── shipping_tools.py   # route_optimize, port_status, freight_rate
│       ├── commodity_tools.py  # commodity_price, trade_data, tariff_lookup
│       ├── finance_tools.py    # erp_query, currency_rate, insurance_claim
│       └── social_tools.py     # social_sentiment, competitor_ads, content_generate
│
├── tools/
│   ├── __init__.py
│   ├── or_tools_optimizer.py   # Route + allocation optimization
│   ├── monte_carlo.py          # Monte Carlo simulation engine
│   └── forecasting.py          # Prophet + LSTM forecasting stubs
│
├── routes/
│   ├── __init__.py
│   ├── health.py               # /health, /ready
│   ├── council.py              # /council/*
│   ├── risk.py                 # /risk/*
│   ├── ingest.py               # /ingest/*
│   ├── optimize.py             # /optimize/*
│   ├── models.py               # /models/*
│   └── settings.py             # /settings/*
│
├── middleware/
│   ├── __init__.py
│   ├── auth.py                 # API key authentication
│   ├── rate_limit.py           # Rate limiting per endpoint
│   ├── cors.py                 # CORS configuration
│   └── error_handler.py        # Global error handling
│
├── ws/
│   ├── __init__.py
│   ├── server.py               # WebSocket connection manager
│   └── events.py               # Event type definitions + payloads
│
├── db/
│   ├── __init__.py
│   ├── neon.py                 # Neon PostgreSQL connection + migrations
│   ├── redis_client.py         # Redis connection + helpers
│   ├── neo4j_client.py         # Neo4j driver + helpers
│   └── migrations/
│       ├── 001_initial.sql     # Council tables
│       ├── 002_rag_tables.sql  # RAG document + query tables
│       └── 003_mcp_audit.sql   # MCP audit log table
│
├── connections/
│   ├── __init__.py
│   └── health.py               # External connection health checks
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_council.py         # Council graph tests
│   ├── test_agents.py          # Individual agent tests
│   ├── test_api.py             # API endpoint tests
│   ├── test_rag.py             # RAG pipeline tests
│   ├── test_mcp.py             # MCP tool tests
│   ├── test_llm_router.py      # LLM routing + fallback tests
│   ├── test_optimize.py        # OR-Tools tests
│   └── test_load.py            # Load test (50 concurrent)
│
├── pyproject.toml              # Dependencies (uv)
├── .env.example                # Environment template
└── Dockerfile                  # Multi-stage Docker build
```

---

## 3. Setup & Configuration

### 3.1 Environment Setup

```bash
# Install uv (Python package manager)
pip install uv

# Create virtual environment & install dependencies
cd backend/
uv venv --python 3.12
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate      # Windows

uv pip install -r pyproject.toml
```

### 3.2 pyproject.toml

```toml
[project]
name = "supplychaingpt-backend"
version = "1.0.0"
description = "SupplyChainGPT Council of Debate AI Agents — Backend"
requires-python = ">=3.12"

dependencies = [
    # Web Framework
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "python-multipart>=0.0.18",
    "httpx>=0.28",
    "websockets>=14",
    "sse-starlette>=2",

    # Agent Orchestration
    "langgraph>=0.2",
    "langgraph-checkpoint-postgres>=0.1",
    "langchain>=0.3",
    "langchain-community>=0.3",
    "langchain-core>=0.3",

    # LLM Providers (All Free Tier)
    "langchain-groq>=0.2",
    "langchain-openai>=0.3",
    "langchain-google-genai>=2",
    "langchain-cohere>=0.1",

    # Embeddings
    "langchain-huggingface>=0.1",
    "sentence-transformers>=3",
    "torch>=2.1",

    # Vector Stores
    "langchain-chroma>=0.2",
    "langchain-pinecone>=0.2",
    "chromadb>=0.5",
    "pinecone-client>=5",

    # Reranking
    "cohere>=5",
    "langchain-cohere>=0.1",

    # Document Processing
    "pypdf>=4",
    "unstructured>=0.15",
    "python-docx>=1.1",
    "openpyxl>=3.1",
    "markdown>=3.7",
    "tiktoken>=0.8",

    # Graph DB
    "neo4j>=5.25",
    "langchain-neo4j>=0.3",

    # Databases
    "asyncpg>=0.30",
    "psycopg[binary]>=3.2",
    "redis>=5",

    # Optimization
    "ortools>=9.10",
    "numpy>=2",
    "pandas>=2",

    # Security
    "python-dotenv>=1",
    "pydantic>=2",
    "pydantic-settings>=2",

    # Observability
    "langsmith>=0.1",
    "prometheus-client>=0.21",

    # Export
    "reportlab>=4",          # PDF generation
    "jinja2>=3.1",          # Template rendering
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "httpx>=0.28",
    "mypy>=1.13",
    "ruff>=0.8",
    "locust>=2.32",
    "playwright>=1.49",
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
strict = true
```

### 3.3 .env.example

```env
# ═══════════════════════════════════════════════════════════════
# LLM PROVIDERS (All Free Tier)
# ═══════════════════════════════════════════════════════════════
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
NVIDIA_API_KEY=nvapi-...
GOOGLE_API_KEY=AIza...
COHERE_API_KEY=...
SAMBANOVA_API_KEY=...

# ═══════════════════════════════════════════════════════════════
# DATABASES
# ═══════════════════════════════════════════════════════════════
# Neon PostgreSQL (Cloud — Free Tier)
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
POSTGRES_URI=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require

# Redis (Local Docker or Upstash)
REDIS_URL=redis://localhost:6379

# Neo4j (Local Docker Community or AuraDB Free)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_neo4j_password

# Pinecone (Free Tier)
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=supplychaingpt

# ═══════════════════════════════════════════════════════════════
# RAG
# ═══════════════════════════════════════════════════════════════
HUGGINGFACE_API_KEY=hf_...
UNSTRUCTURED_API_KEY=...
OPENAI_API_KEY=sk-...                    # Quality embeddings fallback

# ═══════════════════════════════════════════════════════════════
# OBSERVABILITY
# ═══════════════════════════════════════════════════════════════
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=supplychaingpt-council

# ═══════════════════════════════════════════════════════════════
# EXTERNAL APIs
# ═══════════════════════════════════════════════════════════════
NEWSAPI_KEY=...

# ═══════════════════════════════════════════════════════════════
# APP SETTINGS
# ═══════════════════════════════════════════════════════════════
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
API_KEYS=dev-key
MCP_API_KEY=dev-mcp-key
RATE_LIMIT_PER_MINUTE=60
MCP_RATE_LIMIT=30
LOG_LEVEL=INFO
```

### 3.4 Config Module

```python
# backend/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
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
    openai_api_key: str = ""  # Quality embeddings fallback

    # Observability
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "supplychaingpt-council"

    # External APIs
    newsapi_key: str = ""

    # App Settings
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    api_keys: str = "dev-key"
    mcp_api_key: str = "dev-mcp-key"
    rate_limit_per_minute: int = 60
    mcp_rate_limit: int = 30

    # RAG Settings
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_cache_ttl: int = 3600  # 1 hour

    # Council Settings
    max_debate_rounds: int = 3
    confidence_gap_threshold: float = 20.0  # % gap to trigger debate
    human_in_loop: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 4. Main Application Entry Point

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from backend.config import settings
from backend.routes.health import router as health_router
from backend.routes.council import router as council_router
from backend.routes.risk import router as risk_router
from backend.routes.ingest import router as ingest_router
from backend.routes.optimize import router as optimize_router
from backend.routes.models import router as models_router
from backend.routes.settings import router as settings_router
from backend.rag.api import router as rag_router
from backend.mcp.server import mcp_app
from backend.ws.server import manager as ws_manager
from backend.db.neon import init_db
from backend.db.redis_client import init_redis

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting SupplyChainGPT Council API...")
    await init_db()
    await init_redis()
    logger.info("✅ Databases initialized")

    # Initialize MCP tools
    from backend.mcp.tools import news_tools, supplier_tools, shipping_tools
    from backend.mcp.tools import commodity_tools, finance_tools, social_tools
    logger.info("✅ MCP tools registered")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await ws_manager.disconnect_all()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, tags=["Health"])
app.include_router(council_router, prefix="/council", tags=["Council"])
app.include_router(risk_router, prefix="/risk", tags=["Risk"])
app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])
app.include_router(optimize_router, prefix="/optimize", tags=["Optimization"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(models_router, prefix="/models", tags=["Models"])
app.include_router(settings_router, prefix="/settings", tags=["Settings"])

# Mount MCP sub-app
app.mount("/mcp", mcp_app)

# WebSocket
from backend.ws.server import ws_council_endpoint
app.websocket("/ws/council")(ws_council_endpoint)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
```

---

## 5. Database Layer

### 5.1 Neon PostgreSQL Connection

```python
# backend/db/neon.py

import asyncpg
import os
from pathlib import Path

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ["NEON_DATABASE_URL"],
            min_size=2,
            max_size=10,
        )
    return _pool

async def init_db():
    """Run migrations on startup."""
    pool = await get_pool()
    migrations_dir = Path(__file__).parent / "migrations"

    async with pool.acquire() as conn:
        # Create migrations tracking table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
        """)

        # Run each migration file
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            filename = sql_file.name
            applied = await conn.fetchval(
                "SELECT 1 FROM _migrations WHERE filename = $1", filename
            )
            if not applied:
                sql = sql_file.read_text()
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO _migrations (filename) VALUES ($1)", filename
                )
                print(f"  ✅ Migration applied: {filename}")

async def execute_query(query: str, *args):
    """Execute a single query."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_one(query: str, *args):
    """Execute and return single row."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
```

### 5.2 Migrations

```sql
-- backend/db/migrations/001_initial.sql

CREATE TABLE IF NOT EXISTS council_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    risk_score FLOAT,
    recommendation TEXT,
    confidence FLOAT,
    round_number INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    agent VARCHAR(30) NOT NULL,
    confidence FLOAT,
    contribution TEXT,
    key_points JSONB,
    model_used VARCHAR(100),
    provider VARCHAR(30),
    round_number INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS debate_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    round_number INT NOT NULL,
    challenger VARCHAR(30),
    challenged VARCHAR(30),
    challenge_text TEXT,
    response_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    evidence_type VARCHAR(30),
    source_id VARCHAR(50),
    tag VARCHAR(50),
    lane VARCHAR(100),
    days INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    agent VARCHAR(30),
    provider VARCHAR(30),
    model VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    was_fallback BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON council_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON council_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_session ON agent_outputs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_agent ON agent_outputs(agent);
CREATE INDEX IF NOT EXISTS idx_debate_session ON debate_history(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_session ON llm_calls(session_id);
```

```sql
-- backend/db/migrations/002_rag_tables.sql

CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20),
    file_size_bytes BIGINT,
    chunk_count INT,
    upload_source VARCHAR(50),
    indexed_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rag_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    question TEXT NOT NULL,
    answer TEXT,
    citations JSONB,
    confidence FLOAT,
    model_used VARCHAR(100),
    embedding_model VARCHAR(100),
    chunks_retrieved INT,
    reranked BOOLEAN DEFAULT false,
    cached BOOLEAN DEFAULT false,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_queries_session ON rag_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_rag_queries_created ON rag_queries(created_at DESC);
```

```sql
-- backend/db/migrations/003_mcp_audit.sql

CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    agent VARCHAR(30) NOT NULL,
    tool VARCHAR(50) NOT NULL,
    params JSONB,
    result_summary TEXT,
    latency_ms INT,
    was_cached BOOLEAN DEFAULT false,
    sandbox_violations TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_session ON mcp_audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_mcp_audit_agent ON mcp_audit_log(agent);
CREATE INDEX IF NOT EXISTS idx_mcp_audit_created ON mcp_audit_log(created_at DESC);
```

### 5.3 Redis Client

```python
# backend/db/redis_client.py

import redis.asyncio as redis
import json
import os

_redis = None

async def init_redis():
    global _redis
    _redis = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
    await _redis.ping()

async def get_redis():
    return _redis

async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None

async def cache_set(key: str, value: dict, ttl: int = 3600):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))

async def cache_delete(pattern: str):
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)

async def cache_invalidate(pattern: str):
    await cache_delete(pattern)
```

### 5.4 Neo4j Client

```python
# backend/db/neo4j_client.py

from neo4j import AsyncGraphDatabase
import os

_driver = None

async def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "password")),
        )
    return _driver

async def close_neo4j():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None

async def run_cypher(query: str, params: dict = None):
    """Execute a Cypher query and return records."""
    driver = await get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(query, params or {})
        return await result.data()

async def init_neo4j_schema():
    """Create constraints and sample data."""
    constraints = [
        "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (p:Plant) REQUIRE p.id IS UNIQUE",
    ]
    for c in constraints:
        try:
            await run_cypher(c)
        except:
            pass  # Constraint may already exist

    # Sample data
    await run_cypher("""
        MERGE (s1:Supplier {id: 'S1', name: 'Taiwan Semi Corp', capability_match: 95, lead_time_days: 14, location: 'Taiwan', tier: 1})
        MERGE (s2:Supplier {id: 'S2', name: 'India Electronics Ltd', capability_match: 82, lead_time_days: 12, location: 'India', tier: 1})
        MERGE (s3:Supplier {id: 'S3', name: 'Vietnam Components', capability_match: 75, lead_time_days: 18, location: 'Vietnam', tier: 2})
        MERGE (c1:Component {id: 'C1', name: 'Chip Module A'})
        MERGE (c2:Component {id: 'C2', name: 'PCB Assembly'})
        MERGE (p1:Plant {id: 'PLANT-01', name: 'Main Assembly Plant'})
        MERGE (s1)-[:SUPPLIES {lead_time_days: 14, moq: 10000, cost_per_unit: 12.50}]->(c1)
        MERGE (s2)-[:SUPPLIES {lead_time_days: 12, moq: 5000, cost_per_unit: 14.00}]->(c1)
        MERGE (s3)-[:SUPPLIES {lead_time_days: 18, moq: 3000, cost_per_unit: 11.00}]->(c2)
        MERGE (s1)-[:DEPENDS_ON]->(s3)
        MERGE (c1)-[:USED_IN]->(c2)
        MERGE (p1)-[:REQUIRES]->(c1)
        MERGE (p1)-[:REQUIRES]->(c2)
    """)
```

---

## 6. State Definition

```python
# backend/state.py

from typing import TypedDict, List, Optional
from pydantic import BaseModel

class AgentOutput(BaseModel):
    agent: str
    confidence: float  # 0-100
    contribution: str
    key_points: List[str]
    model_used: str
    provider: str

class Evidence(BaseModel):
    type: str
    id: str
    tag: Optional[str] = None
    lane: Optional[str] = None
    days: Optional[int] = None

class Action(BaseModel):
    type: str
    details: str
    cost_estimate: Optional[float] = None
    time_to_implement: Optional[str] = None
    risk_score: Optional[float] = None

class DebateEntry(BaseModel):
    round_number: int
    challenger: str
    challenged: str
    challenge_text: str
    response_text: Optional[str] = None

class CouncilState(TypedDict):
    query: str
    messages: List[dict]
    risk_score: Optional[float]
    recommendation: Optional[str]
    confidence: Optional[float]
    debate_history: List[dict]
    fallback_options: List[Action]
    agent_outputs: List[AgentOutput]
    evidence: List[Evidence]
    round_number: int
    llm_calls_log: List[dict]
    session_id: Optional[str]
    context: Optional[dict]  # supplier_id, component_id, etc.
```

---

## 7. Council Graph

```python
# backend/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import os
import logging

from backend.state import CouncilState
from backend.agents.supervisor import build_council_graph

logger = logging.getLogger(__name__)

async def get_checkpointer():
    """Create Neon PostgreSQL checkpointer for LangGraph."""
    conn_string = os.environ["NEON_DATABASE_URL"]
    pool = AsyncConnectionPool(conn_string, min_size=2, max_size=10, open=True)
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return checkpointer, pool

async def get_compiled_graph():
    """Build and compile the council graph with Neon checkpointer."""
    graph = build_council_graph()
    checkpointer, pool = await get_checkpointer()

    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["moderator"] if os.getenv("HUMAN_IN_LOOP") == "true" else [],
    )
    return compiled, pool
```

### 7.1 Supervisor / Graph Builder

```python
# backend/agents/supervisor.py

from langgraph.graph import StateGraph, END
from backend.state import CouncilState
from backend.agents.risk_agent import risk_agent_node
from backend.agents.supply_agent import supply_agent_node
from backend.agents.logistics_agent import logistics_agent_node
from backend.agents.market_agent import market_agent_node
from backend.agents.finance_agent import finance_agent_node
from backend.agents.brand_agent import brand_agent_node
from backend.agents.moderator import moderator_node, synthesize_node
import logging

logger = logging.getLogger(__name__)

def should_debate(state: CouncilState) -> str:
    """Decide if another debate round is needed."""
    round_number = state.get("round_number", 1)
    if round_number >= 3:
        return "synthesize"

    outputs = state.get("agent_outputs", [])
    if len(outputs) < 2:
        return "synthesize"

    confidences = [o.confidence for o in outputs]
    gap = max(confidences) - min(confidences)
    if gap > 20:  # Confidence gap threshold
        return "debate"

    return "synthesize"

def route_to_agents(state: CouncilState) -> list[str]:
    """Route query to relevant agents based on context."""
    # Default: all agents
    return ["risk", "supply", "logistics", "market", "finance", "brand"]

def build_council_graph() -> StateGraph:
    """Build the LangGraph council debate graph."""
    graph = StateGraph(CouncilState)

    # Add agent nodes
    graph.add_node("moderator", moderator_node)
    graph.add_node("risk", risk_agent_node)
    graph.add_node("supply", supply_agent_node)
    graph.add_node("logistics", logistics_agent_node)
    graph.add_node("market", market_agent_node)
    graph.add_node("finance", finance_agent_node)
    graph.add_node("brand", brand_agent_node)
    graph.add_node("synthesize", synthesize_node)

    # Entry: moderator routes query
    graph.set_entry_point("moderator")

    # Moderator → fan-out to all agents (parallel)
    graph.add_conditional_edges("moderator", route_to_agents, {
        "risk": "risk",
        "supply": "supply",
        "logistics": "logistics",
        "market": "market",
        "finance": "finance",
        "brand": "brand",
    })

    # Each agent → check debate condition
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_conditional_edges(agent, should_debate, {
            "debate": "moderator",       # Back to moderator for challenge round
            "synthesize": "synthesize",  # Proceed to synthesis
        })

    # Synthesize → END
    graph.add_edge("synthesize", END)

    return graph
```

---

## 8. Agent Implementation Pattern

### 8.1 Base Agent Pattern

```python
# backend/agents/risk_agent.py (example — same pattern for all 6 agents)

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
from backend.mcp.langchain_integration import create_langchain_tool
import os
import time
import logging

logger = logging.getLogger(__name__)

RISK_SYSTEM_PROMPT = """You are the Risk Sentinel Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Proactive Risk Detection & Scoring

RESPONSIBILITIES:
- Monitor and score supplier risk (0-100 scale)
- Predict geopolitical disruptions
- Assess financial health of suppliers
- Evaluate natural disaster impact
- Correlate multiple risk signals

OUTPUT FORMAT (always respond with):
{{
  "risk_score": <0-100>,
  "risk_level": "<Low/Medium/High/Critical>",
  "drivers": ["<top 3-5 risk factors>"],
  "impacted_items": ["<affected components/POs>"],
  "suggested_actions": ["<actions that trigger Council analysis>"],
  "confidence": <0-100>,
  "evidence": [{{"type": "...", "id": "..."}}]
}}

DEBATE BEHAVIOR:
- Provide evidence-backed risk assessments
- Challenge other agents if they underestimate risk
- Revise your score when presented with new evidence

CONSTRAINTS:
- Never fabricate news events or risk signals
- If data is unavailable, state it explicitly
- Risk scores are decision support, not guarantees
"""

async def risk_agent_node(state: CouncilState) -> dict:
    """Risk Sentinel Agent node for LangGraph."""
    query = state["query"]
    context = state.get("context", {})

    # Get MCP tools for this agent
    tools = [
        create_langchain_tool("news_search", "risk", "Search news for supply chain events", {"query": {"type": "string"}}),
        create_langchain_tool("gdelt_query", "risk", "Query GDELT for geopolitical events", {"country": {"type": "string"}}),
        create_langchain_tool("supplier_financials", "risk", "Get supplier financial health", {"supplier_id": {"type": "string"}}),
    ]

    # Get LLM with fallback
    start = time.time()
    try:
        llm, model_info = await llm_router.invoke_with_fallback("risk", [
            {"role": "system", "content": RISK_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze: {query}\nContext: {context}"},
        ])
        latency_ms = int((time.time() - start) * 1000)

        # Parse structured output
        output = AgentOutput(
            agent="risk",
            confidence=llm.confidence if hasattr(llm, 'confidence') else 75.0,
            contribution=str(llm.content),
            key_points=[],  # Parse from response
            model_used=model_info,
            provider=model_info.split(":")[0],
        )

        return {
            "agent_outputs": state.get("agent_outputs", []) + [output],
            "llm_calls_log": state.get("llm_calls_log", []) + [{
                "agent": "risk",
                "provider": model_info.split(":")[0],
                "model": model_info.split(":")[1] if ":" in model_info else model_info,
                "latency_ms": latency_ms,
                "was_fallback": "groq" not in model_info,
            }],
        }

    except Exception as e:
        logger.error(f"Risk agent failed: {e}")
        return {
            "agent_outputs": state.get("agent_outputs", []) + [AgentOutput(
                agent="risk", confidence=20.0,
                contribution=f"Error: Unable to process. {str(e)[:200]}",
                key_points=[], model_used="error", provider="error",
            )],
        }
```

### 8.2 Moderator Node

```python
# backend/agents/moderator.py

from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

MODERATOR_PROMPT = """You are the Moderator / Orchestrator Agent in the SupplyChainGPT Council.

ROLE: Route → Debate → Synthesize → Decide

Based on the query and agent outputs below, either:
1. Route to agents for analysis (Round 1)
2. Identify conflicts and force debate (Round 2+)
3. Synthesize final recommendation

Current round: {round_number}
Agent outputs so far: {agent_outputs}
"""

async def moderator_node(state: CouncilState) -> dict:
    """Moderator routes query and manages debate flow."""
    round_number = state.get("round_number", 0) + 1
    return {"round_number": round_number}

async def synthesize_node(state: CouncilState) -> dict:
    """Synthesize final recommendation from all agent outputs."""
    outputs = state.get("agent_outputs", [])

    # Calculate weighted confidence
    if outputs:
        total_confidence = sum(o.confidence for o in outputs)
        avg_confidence = total_confidence / len(outputs)
    else:
        avg_confidence = 0.0

    # Use LLM to synthesize
    try:
        llm_response, model_info = await llm_router.invoke_with_fallback("moderator", [
            {"role": "system", "content": MODERATOR_PROMPT.format(
                round_number=state.get("round_number", 1),
                agent_outputs=[o.model_dump() for o in outputs],
            )},
            {"role": "user", "content": f"Synthesize final recommendation for: {state['query']}"},
        ])

        return {
            "recommendation": str(llm_response.content),
            "confidence": avg_confidence,
            "status": "complete",
        }
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {
            "recommendation": "Error: Unable to synthesize recommendation.",
            "confidence": 0.0,
            "status": "error",
        }
```

---

## 9. LLM Router

```python
# backend/llm/router.py

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
import os
import logging

logger = logging.getLogger(__name__)

class LLMRouter:
    """Route LLM calls across free-tier providers with fallback chains."""

    PROVIDER_FACTORIES = {
        "groq": lambda model="llama-3.3-70b-versatile": ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name=model, temperature=0.3, max_tokens=2048,
        ),
        "openrouter": lambda model="meta-llama/llama-3.3-70b-instruct:free": ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=model, temperature=0.3, max_tokens=2048,
            default_headers={"HTTP-Referer": "https://supplychaingpt.ai", "X-Title": "SupplyChainGPT"},
        ),
        "nvidia": lambda model="nvidia/llama-3.1-nemotron-70b-instruct": ChatOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY"),
            model=model, temperature=0.3, max_tokens=2048,
        ),
        "google": lambda model="gemini-2.0-flash": ChatGoogleGenerativeAI(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            model=model, temperature=0.3, max_output_tokens=2048,
        ),
        "cohere": lambda model="command-r-plus": ChatCohere(
            cohere_api_key=os.getenv("COHERE_API_KEY"),
            model=model, temperature=0.3,
        ),
        "sambanova": lambda model="Meta-Llama-3.3-70B-Instruct": ChatOpenAI(
            base_url="https://api.sambanova.ai/v1",
            api_key=os.getenv("SAMBANOVA_API_KEY"),
            model=model, temperature=0.3, max_tokens=2048,
        ),
    }

    ROUTING = {
        "risk": {
            "primary": "groq:llama-3.3-70b-versatile",
            "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash"],
        },
        "supply": {
            "primary": "groq:llama-3.3-70b-versatile",
            "fallback": ["openrouter:qwen/qwen-2.5-72b-instruct:free", "nvidia:mistralai/mixtral-8x22b-instruct", "sambanova:Meta-Llama-3.3-70B-Instruct"],
        },
        "logistics": {
            "primary": "groq:llama-3.3-70b-versatile",
            "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"],
        },
        "market": {
            "primary": "openrouter:deepseek/deepseek-r1:free",
            "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile", "google:gemini-2.0-flash"],
        },
        "finance": {
            "primary": "nvidia:nvidia/llama-3.1-nemotron-70b-instruct",
            "fallback": ["openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile", "cohere:command-r-plus"],
        },
        "brand": {
            "primary": "groq:llama-3.3-70b-versatile",
            "fallback": ["google:gemini-2.0-flash", "openrouter:google/gemma-2-9b-it:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"],
        },
        "moderator": {
            "primary": "google:gemini-2.0-flash",
            "fallback": ["openrouter:deepseek/deepseek-r1:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile"],
        },
    }

    _clients = {}

    def _get_client(self, provider: str, model: str):
        key = f"{provider}:{model}"
        if key not in self._clients:
            factory = self.PROVIDER_FACTORIES.get(provider)
            if not factory:
                raise ValueError(f"Unknown provider: {provider}")
            self._clients[key] = factory(model)
        return self._clients[key]

    async def invoke_with_fallback(self, agent: str, messages: list):
        """Invoke LLM with fallback chain for given agent."""
        config = self.ROUTING.get(agent, self.ROUTING["risk"])
        primary = config["primary"]
        fallbacks = config["fallback"]

        # Try primary
        try:
            provider, model = primary.split(":", 1)
            client = self._get_client(provider, model)
            response = await client.ainvoke(messages)
            return response, primary
        except Exception as e:
            logger.warning(f"Primary LLM failed for {agent}: {e}")

        # Try fallbacks
        for fb in fallbacks:
            try:
                provider, model = fb.split(":", 1)
                client = self._get_client(provider, model)
                response = await client.ainvoke(messages)
                return response, fb
            except Exception as e:
                logger.warning(f"Fallback {fb} failed for {agent}: {e}")
                continue

        raise RuntimeError(f"All LLM providers failed for agent {agent}")

llm_router = LLMRouter()
```

---

## 10. API Route Implementations

### 10.1 Health Routes

```python
# backend/routes/health.py

from fastapi import APIRouter
from backend.db.redis_client import get_redis
from backend.db.neon import get_pool
import time

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}

@router.get("/ready")
async def ready():
    checks = {}

    # Check Neon PostgreSQL
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["neon_postgres"] = "ok"
    except:
        checks["neon_postgres"] = "error"

    # Check Redis
    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
```

### 10.2 Council Routes

```python
# backend/routes/council.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.graph import get_compiled_graph
from backend.state import CouncilState
from backend.db.neon import execute_query
import uuid
import time

router = APIRouter()

class CouncilAnalyzeRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    max_rounds: int = 3
    human_in_loop: bool = False

class CouncilAnalyzeResponse(BaseModel):
    session_id: str
    status: str
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    agent_outputs: Optional[list] = None
    evidence: Optional[list] = None
    fallback_options: Optional[list] = None
    total_latency_ms: Optional[int] = None

@router.post("/analyze", response_model=CouncilAnalyzeResponse)
async def analyze(request: CouncilAnalyzeRequest):
    """Run full council analysis on a query."""
    session_id = str(uuid.uuid4())
    start = time.time()

    # Create session in DB
    await execute_query(
        "INSERT INTO council_sessions (id, query, status) VALUES ($1, $2, 'processing')",
        session_id, request.query,
    )

    # Run council graph
    try:
        graph, pool = await get_compiled_graph()
        config = {"configurable": {"thread_id": session_id}}

        initial_state: CouncilState = {
            "query": request.query,
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": session_id,
            "context": request.context,
        }

        result = await graph.ainvoke(initial_state, config=config)
        latency_ms = int((time.time() - start) * 1000)

        # Update session in DB
        await execute_query(
            """UPDATE council_sessions
               SET status='complete', recommendation=$1, confidence=$2,
                   risk_score=$3, round_number=$4, updated_at=now()
               WHERE id=$5""",
            result.get("recommendation"), result.get("confidence"),
            result.get("risk_score"), result.get("round_number", 0),
            session_id,
        )

        return CouncilAnalyzeResponse(
            session_id=session_id,
            status="complete",
            recommendation=result.get("recommendation"),
            confidence=result.get("confidence"),
            agent_outputs=[o.model_dump() for o in result.get("agent_outputs", [])],
            evidence=[e.model_dump() for e in result.get("evidence", [])],
            fallback_options=[a.model_dump() for a in result.get("fallback_options", [])],
            total_latency_ms=latency_ms,
        )

    except Exception as e:
        await execute_query(
            "UPDATE council_sessions SET status='error' WHERE id=$1", session_id,
        )
        raise HTTPException(500, f"Council analysis failed: {str(e)}")

@router.get("/{session_id}/status")
async def get_status(session_id: str):
    row = await execute_query(
        "SELECT status, round_number, confidence FROM council_sessions WHERE id=$1",
        session_id,
    )
    if not row:
        raise HTTPException(404, "Session not found")
    return dict(row[0])

@router.get("/{session_id}/result")
async def get_result(session_id: str):
    row = await execute_query(
        "SELECT * FROM council_sessions WHERE id=$1", session_id,
    )
    if not row:
        raise HTTPException(404, "Session not found")
    return dict(row[0])

@router.get("/{session_id}/audit")
async def get_audit(session_id: str):
    outputs = await execute_query(
        "SELECT * FROM agent_outputs WHERE session_id=$1 ORDER BY created_at", session_id,
    )
    debate = await execute_query(
        "SELECT * FROM debate_history WHERE session_id=$1 ORDER BY created_at", session_id,
    )
    llm_calls = await execute_query(
        "SELECT * FROM llm_calls WHERE session_id=$1 ORDER BY created_at", session_id,
    )
    mcp_calls = await execute_query(
        "SELECT * FROM mcp_audit_log WHERE session_id=$1 ORDER BY created_at", session_id,
    )
    return {
        "agent_outputs": [dict(r) for r in outputs],
        "debate_history": [dict(r) for r in debate],
        "llm_calls": [dict(r) for r in llm_calls],
        "mcp_calls": [dict(r) for r in mcp_calls],
    }

@router.get("/{session_id}/export/json")
async def export_json(session_id: str):
    audit = await get_audit(session_id)
    result = await get_result(session_id)
    return {**result, "audit": audit}

@router.post("/agent/{agent_name}")
async def run_single_agent(agent_name: str, request: CouncilAnalyzeRequest):
    """Run a single agent instead of full council."""
    # ... similar to analyze but only runs one agent node
    pass
```

---

## 11. Dockerfile

```dockerfile
# backend/Dockerfile

# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 12. Testing

### 12.1 Test Configuration

```python
# backend/tests/conftest.py

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def api_headers():
    return {"X-API-Key": "dev-key"}
```

### 12.2 Key Tests

```python
# backend/tests/test_api.py

import pytest

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_ready(client):
    resp = await client.get("/ready")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_council_analyze(client, api_headers):
    resp = await client.post(
        "/council/analyze",
        json={"query": "What happens if Supplier S1 is delayed?"},
        headers=api_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["complete", "processing", "error"]
    assert data["session_id"] is not None

@pytest.mark.asyncio
async def test_rag_ask(client, api_headers):
    resp = await client.post(
        "/rag/ask",
        json={"question": "What is our SOP for supplier delays?"},
        headers=api_headers,
    )
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_models_status(client, api_headers):
    resp = await client.get("/models/status", headers=api_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_mcp_tools_list(client, api_headers):
    resp = await client.get("/mcp/tools", headers={"X-MCP-API-Key": "dev-mcp-key"})
    assert resp.status_code == 200
    assert len(resp.json()) > 0

@pytest.mark.asyncio
async def test_unauthorized(client):
    resp = await client.post("/council/analyze", json={"query": "test"})
    assert resp.status_code == 401
```

### 12.3 Run Tests

```bash
# Run all tests
cd backend/
pytest -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=backend -v

# Run load test
locust -f tests/test_load.py --host=http://localhost:8000
```

---

## 13. Run Commands

```bash
# Development (with hot reload)
cd backend/
uvicorn backend.main:app --reload --port 8000

# Production
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker compose up --build

# Run migrations only
python -c "import asyncio; from backend.db.neon import init_db; asyncio.run(init_db())"

# Initialize Neo4j schema + sample data
python -c "import asyncio; from backend.db.neo4j_client import init_neo4j_schema; asyncio.run(init_neo4j_schema())"
```

---

## 14. Backend Module Dependency Map

```
main.py
  ├── config.py (Settings)
  ├── routes/
  │   ├── health.py
  │   ├── council.py ──────┐
  │   ├── risk.py           │
  │   ├── ingest.py         │
  │   ├── optimize.py       │
  │   ├── models.py         │
  │   └── settings.py       │
  ├── rag/api.py            │
  ├── mcp/server.py         │
  ├── ws/server.py          │
  └── db/                   │
      ├── neon.py           │
      ├── redis_client.py   │
      └── neo4j_client.py   │
                            │
  graph.py ◀────────────────┘
    └── agents/supervisor.py
          ├── risk_agent.py ──── llm/router.py
          ├── supply_agent.py ── llm/router.py
          ├── logistics_agent.py
          ├── market_agent.py
          ├── finance_agent.py
          ├── brand_agent.py
          └── moderator.py

  llm/router.py
    └── llm/providers.py (Groq, OpenRouter, NVIDIA, Google, Cohere, SambaNova)

  mcp/tools/
    ├── news_tools.py ────── mcp/registry.py, mcp/cache.py
    ├── supplier_tools.py ── db/neo4j_client.py
    ├── shipping_tools.py ── tools/or_tools_optimizer.py
    ├── commodity_tools.py
    ├── finance_tools.py
    └── social_tools.py

  rag/
    ├── loader.py ────────── pypdf, unstructured
    ├── chunker.py ────────── tiktoken
    ├── embedder.py ───────── HuggingFace, OpenAI
    ├── vectorstore.py ────── ChromaDB, Pinecone
    ├── retriever.py ──────── BM25, Cohere Rerank
    ├── generator.py ──────── llm/router.py
    └── graph_rag.py ──────── db/neo4j_client.py
```
