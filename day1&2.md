# SupplyChainGPT — Day 1 & Day 2 Implementation Guide

Hour-by-hour implementation guide for the first 2 days. Covers Phase 0 (Setup & Docs) and Phase 1 (Backend Foundation). Every task has exact commands, file paths, and verification steps.

---

## Day 1: Setup & Documentation (Phase 0)

### Timeline

```
09:00 ─── 10:30  Repo Setup + Structure
10:30 ─── 11:30  Environment Configuration
11:30 ─── 12:30  Documentation (README, features, spec)
12:30 ─── 13:00  Lunch
13:00 ─── 14:30  Documentation (agents, mcp, rag)
14:30 ─── 15:30  Documentation (routing, backend, frontend)
15:30 ─── 16:30  Documentation (testing, security, debate-engine, workflow, phasewiseplan)
16:30 ─── 17:00  Git Setup + Push
```

---

### 09:00–10:30 — Repo Setup + Structure

#### 09:00 — Create Monorepo

```bash
# Create project root
mkdir -p supplychaingpt
cd supplychaingpt
git init

# Create directory structure
mkdir -p backend/agents
mkdir -p backend/llm
mkdir -p backend/rag
mkdir -p backend/mcp/tools
mkdir -p backend/tools
mkdir -p backend/routes
mkdir -p backend/middleware
mkdir -p backend/ws
mkdir -p backend/db/migrations
mkdir -p backend/connections
mkdir -p backend/tests/fixtures/mock_responses

mkdir -p frontend/public
mkdir -p frontend/src/pages
mkdir -p frontend/src/components/layout
mkdir -p frontend/src/components/dashboard
mkdir -p frontend/src/components/chat
mkdir -p frontend/src/components/debate
mkdir -p frontend/src/components/brand
mkdir -p frontend/src/components/modals
mkdir -p frontend/src/components/shared
mkdir -p frontend/src/hooks
mkdir -p frontend/src/store
mkdir -p frontend/src/lib
mkdir -p frontend/src/types
mkdir -p frontend/src/assets/agent-avatars
mkdir -p frontend/src/__tests__/components
mkdir -p frontend/src/__tests__/store
mkdir -p frontend/e2e

mkdir -p docs
mkdir -p project
```

#### 09:30 — Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
*.egg

# Environment
.env
.env.local
.env.production

# Node
node_modules/
dist/
.next/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
*.log

# ChromaDB
chroma_data/

# Neo4j
neo4j_data/

# Redis
redis_data/

# Coverage
htmlcov/
.coverage
coverage.xml

# Build
build/
*.pyc
EOF
```

#### 09:45 — Create .env.example

```bash
cat > .env.example << 'EOF'
# LLM PROVIDERS (All Free Tier)
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
NVIDIA_API_KEY=nvapi-...
GOOGLE_API_KEY=AIza...
COHERE_API_KEY=...
SAMBANOVA_API_KEY=...

# DATABASES
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/supplychaingpt?sslmode=require
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=supplychaingpt

# RAG
HUGGINGFACE_API_KEY=hf_...
UNSTRUCTURED_API_KEY=...
OPENAI_API_KEY=sk-...

# OBSERVABILITY
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=supplychaingpt-council

# EXTERNAL
NEWSAPI_KEY=...

# APP
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
API_KEYS=dev-key
MCP_API_KEY=dev-mcp-key
RATE_LIMIT_PER_MINUTE=60
MCP_RATE_LIMIT=30
LOG_LEVEL=INFO
EOF
```

#### 10:00 — Verify Structure

```bash
# Check directory tree
find . -type d | head -50

# Initialize git
git add .
git commit -m "chore: initial project structure"
```

**✅ Checkpoint:** Repo created with all directories, .gitignore, .env.example

---

### 10:30–11:30 — Environment Configuration

#### 10:30 — Backend Python Setup

```bash
cd backend

# Create pyproject.toml (copy from backend.md spec)
# Create config.py (copy from backend.md spec)

# Install uv
pip install uv

# Create virtual environment
uv venv --python 3.12
# Activate:
# Linux/Mac: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# Install core dependencies first
uv pip install fastapi uvicorn python-dotenv pydantic pydantic-settings httpx
```

#### 10:50 — Frontend React Setup

```bash
cd frontend

# Create Vite React TypeScript project
npm create vite@latest . -- --template react-ts

# Install core dependencies
npm install react-router-dom @tanstack/react-query zustand socket.io-client recharts framer-motion lucide-react date-fns clsx tailwind-merge class-variance-authority

# Install Radix UI primitives
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-slider @radix-ui/react-progress @radix-ui/react-separator

# Install dev dependencies
npm install -D tailwindcss postcss autoprefixer @testing-library/react @testing-library/jest-dom vitest @playwright/test

# Initialize Tailwind
npx tailwindcss init -p
```

#### 11:10 — Docker Compose

```bash
cd ..  # back to project root

cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/testpassword
    volumes:
      - neo4j_data:/data

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  redis_data:
  neo4j_data:
  chroma_data:
EOF
```

#### 11:20 — Start Infrastructure

```bash
# Start Redis, Neo4j, ChromaDB
docker compose up -d redis neo4j chromadb

# Verify they're running
docker compose ps

# Test Redis
docker compose exec redis redis-cli ping
# Expected: PONG

# Test Neo4j (wait 30s for startup)
curl http://localhost:7474
# Expected: Neo4j web interface
```

**✅ Checkpoint:** Backend venv, frontend deps, Docker infra running

---

### 11:30–12:30 — Documentation Part 1

#### All documentation files already created in `project/` folder:

| File | Status | Content |
|------|--------|---------|
| `README.md` | ✅ Done | Full project overview from PDFs |
| `features.md` | ✅ Done | Feature breakdown by category |
| `spec.md` | ✅ Done | Technical specs + OpenRouter + NVIDIA |
| `agents.md` | ✅ Done | 7 agents + Neon PG + free models |
| `mcp.md` | ✅ Done | MCP tools + sandbox + audit |
| `rag.md` | ✅ Done | RAG pipeline + APIs + wireframes |

**No action needed** — these were created in previous session. Verify they exist:

```bash
ls -la project/*.md
# Should show: README.md, features.md, spec.md, agents.md, mcp.md, rag.md
```

---

### 13:00–14:30 — Documentation Part 2

| File | Status | Content |
|------|--------|---------|
| `routing.md` | ✅ Done | All routes + APIs + wireframes |
| `backend.md` | ✅ Done | Backend implementation spec |
| `frontend.md` | ✅ Done | Frontend implementation spec |

Verify:

```bash
ls -la project/routing.md project/backend.md project/frontend.md
```

---

### 14:30–15:30 — Documentation Part 3

| File | Status | Content |
|------|--------|---------|
| `testing.md` | ✅ Done | Test suite specification |
| `security.md` | ✅ Done | Security specification |
| `debate-engine.md` | ✅ Done | Debate mechanics + Monte Carlo |
| `workflow.md` | ✅ Done | All workflow specifications |
| `phasewiseplan.md` | ✅ Done | Phase plan with status |

Verify:

```bash
ls -la project/testing.md project/security.md project/debate-engine.md project/workflow.md project/phasewiseplan.md
```

---

### 15:30–16:30 — Copy Docs to Repo + Finalize

```bash
# Copy project docs to docs/ folder in repo
cp project/*.md docs/

# Verify all 12 docs exist
ls docs/*.md | wc -l
# Expected: 12

# List all docs
ls docs/
# Expected: README.md, features.md, spec.md, agents.md, mcp.md, rag.md,
#           routing.md, backend.md, frontend.md, testing.md, security.md,
#           debate-engine.md, workflow.md, phasewiseplan.md, day1&2.md
```

---

### 16:30–17:00 — Git Setup + Push

```bash
# Stage all files
git add .

# Commit
git commit -m "docs: complete project documentation + repo structure"

# Create GitHub repo (if not exists)
# gh repo create SupplyChainGPT --private --source=.

# Push
git push origin main
```

**✅ Day 1 Complete:** Repo + all 14 documentation files + infrastructure running

---

## Day 2: Backend Foundation (Phase 1)

### Timeline

```
09:00 ─── 10:00  FastAPI App + Config + Middleware
10:00 ─── 11:00  Database Connections (Neon PG, Redis, Neo4j)
11:00 ─── 12:00  DB Migrations + Schema
12:00 ─── 12:30  Lunch
12:30 ─── 14:00  LLM Router (6 providers + fallback)
14:00 ─── 15:00  Health + Auth + Rate Limit Endpoints
15:00 ─── 16:00  Council State + Graph Skeleton
16:00 ─── 17:00  Tests + Verification
```

---

### 09:00–10:00 — FastAPI App + Config + Middleware

#### 09:00 — Create config.py

```python
# backend/config.py

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

    # External
    newsapi_key: str = ""

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
```

#### 09:15 — Create main.py

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from backend.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting SupplyChainGPT Council API...")
    # DB init will happen later (Phase 1 step)
    yield
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health route (temporary — will move to routes/ later)
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}

@app.get("/ready")
async def ready():
    return {"status": "ok", "checks": {}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
```

#### 09:30 — Create auth middleware

```python
# backend/middleware/auth.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEYS = os.getenv("API_KEYS", "dev-key").split(",")
MCP_API_KEYS = os.getenv("MCP_API_KEY", "dev-mcp-key").split(",")
PUBLIC_ENDPOINTS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_ENDPOINTS or request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path.startswith("/mcp/"):
            key = request.headers.get("X-MCP-API-Key", "")
            if key not in MCP_API_KEYS:
                raise HTTPException(401, "Invalid MCP API key")
            return await call_next(request)

        key = request.headers.get("X-API-Key", "")
        if key not in API_KEYS:
            raise HTTPException(401, "Invalid API key")

        return await call_next(request)
```

#### 09:40 — Create error handler middleware

```python
# backend/middleware/error_handler.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled error: {traceback.format_exc()}")
            raise HTTPException(500, "Internal server error. Please try again.")
```

#### 09:50 — Wire middleware into main.py

```python
# Add to backend/main.py after CORS middleware

from backend.middleware.auth import AuthMiddleware
from backend.middleware.error_handler import ErrorHandlerMiddleware

app.add_middleware(AuthMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
```

#### 09:55 — Test the server starts

```bash
cd backend
uvicorn backend.main:app --reload --port 8000

# In another terminal:
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}

curl http://localhost:8000/council/analyze
# Expected: 401 Unauthorized (no API key)

curl -H "X-API-Key: dev-key" http://localhost:8000/council/analyze
# Expected: 405 Method Not Allowed (GET instead of POST)
```

**✅ Checkpoint:** FastAPI running with CORS, auth, error handling

---

### 10:00–11:00 — Database Connections

#### 10:00 — Create Neon PostgreSQL connection

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
            dsn=os.environ.get("NEON_DATABASE_URL", os.environ.get("DATABASE_URL", "")),
            min_size=2,
            max_size=10,
        )
    return _pool

async def init_db():
    pool = await get_pool()
    migrations_dir = Path(__file__).parent / "migrations"
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            applied = await conn.fetchval(
                "SELECT 1 FROM _migrations WHERE filename = $1", sql_file.name
            )
            if not applied:
                await conn.execute(sql_file.read_text())
                await conn.execute(
                    "INSERT INTO _migrations (filename) VALUES ($1)", sql_file.name
                )
                print(f"  ✅ Migration: {sql_file.name}")

async def execute_query(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_one(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
```

#### 10:20 — Create Redis client

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
```

#### 10:30 — Create Neo4j client

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
            auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "testpassword")),
        )
    return _driver

async def close_neo4j():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None

async def run_cypher(query: str, params: dict = None):
    driver = await get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(query, params or {})
        return await result.data()

async def init_neo4j_schema():
    constraints = [
        "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    ]
    for c in constraints:
        try:
            await run_cypher(c)
        except:
            pass

    # Sample data
    await run_cypher("""
        MERGE (s1:Supplier {id: 'S1', name: 'Taiwan Semi Corp', capability_match: 95, lead_time_days: 14, location: 'Taiwan', tier: 1})
        MERGE (s2:Supplier {id: 'S2', name: 'India Electronics Ltd', capability_match: 82, lead_time_days: 12, location: 'India', tier: 1})
        MERGE (s3:Supplier {id: 'S3', name: 'Vietnam Components', capability_match: 75, lead_time_days: 18, location: 'Vietnam', tier: 2})
        MERGE (c1:Component {id: 'C1', name: 'Chip Module A'})
        MERGE (c2:Component {id: 'C2', name: 'PCB Assembly'})
        MERGE (s1)-[:SUPPLIES {lead_time_days: 14, moq: 10000, cost_per_unit: 12.50}]->(c1)
        MERGE (s2)-[:SUPPLIES {lead_time_days: 12, moq: 5000, cost_per_unit: 14.00}]->(c1)
        MERGE (s3)-[:SUPPLIES {lead_time_days: 18, moq: 3000, cost_per_unit: 11.00}]->(c2)
        MERGE (s1)-[:DEPENDS_ON]->(s3)
        MERGE (c1)-[:USED_IN]->(c2)
    """)
```

#### 10:50 — Wire DB init into main.py lifespan

```python
# Update lifespan in backend/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting SupplyChainGPT Council API...")
    try:
        from backend.db.neon import init_db
        await init_db()
        logger.info("✅ Neon PostgreSQL initialized")
    except Exception as e:
        logger.warning(f"⚠️ Neon PG not available: {e}")

    try:
        from backend.db.redis_client import init_redis
        await init_redis()
        logger.info("✅ Redis initialized")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")

    try:
        from backend.db.neo4j_client import init_neo4j_schema
        await init_neo4j_schema()
        logger.info("✅ Neo4j initialized with sample data")
    except Exception as e:
        logger.warning(f"⚠️ Neo4j not available: {e}")

    yield
    logger.info("🛑 Shutting down...")
```

#### 10:55 — Test DB connections

```bash
# Restart server
uvicorn backend.main:app --reload --port 8000

# Check logs for:
# ✅ Neon PostgreSQL initialized
# ✅ Redis initialized
# ✅ Neo4j initialized with sample data

# Test readiness
curl http://localhost:8000/ready
# Should show checks for each DB
```

**✅ Checkpoint:** All 3 databases connected + Neo4j seeded

---

### 11:00–12:00 — DB Migrations

#### 11:00 — Create migration 001

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
```

#### 11:20 — Create migration 002

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
    chunks_retrieved INT,
    reranked BOOLEAN DEFAULT false,
    cached BOOLEAN DEFAULT false,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_queries_created ON rag_queries(created_at DESC);
```

#### 11:30 — Create migration 003

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

CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    source_ip VARCHAR(45),
    api_key_prefix VARCHAR(8),
    endpoint VARCHAR(200),
    details JSONB,
    severity VARCHAR(10) DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_agent ON mcp_audit_log(agent);
CREATE INDEX IF NOT EXISTS idx_security_audit_type ON security_audit_log(event_type);
```

#### 11:40 — Run migrations

```bash
# Migrations run automatically on server startup via init_db()
# Restart server to trigger:
uvicorn backend.main:app --reload --port 8000

# Check logs for:
# ✅ Migration: 001_initial.sql
# ✅ Migration: 002_rag_tables.sql
# ✅ Migration: 003_mcp_audit.sql
```

**✅ Checkpoint:** All 3 migrations applied, 7 tables created

---

### 12:30–14:00 — LLM Router

#### 12:30 — Create LLM provider factories

```python
# backend/llm/providers.py

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
import os

def get_groq_client(model="llama-3.3-70b-versatile"):
    return ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name=model, temperature=0.3, max_tokens=2048)

def get_openrouter_client(model="meta-llama/llama-3.3-70b-instruct:free"):
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
        default_headers={"HTTP-Referer": "https://supplychaingpt.ai", "X-Title": "SupplyChainGPT"},
    )

def get_nvidia_client(model="nvidia/llama-3.1-nemotron-70b-instruct"):
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
    )

def get_google_client(model="gemini-2.0-flash"):
    return ChatGoogleGenerativeAI(google_api_key=os.getenv("GOOGLE_API_KEY"), model=model, temperature=0.3)

def get_cohere_client(model="command-r-plus"):
    return ChatCohere(cohere_api_key=os.getenv("COHERE_API_KEY"), model=model, temperature=0.3)

def get_sambanova_client(model="Meta-Llama-3.3-70B-Instruct"):
    return ChatOpenAI(
        base_url="https://api.sambanova.ai/v1",
        api_key=os.getenv("SAMBANOVA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
    )
```

#### 12:45 — Create LLM router

```python
# backend/llm/router.py

import os
import logging
from backend.llm.providers import *

logger = logging.getLogger(__name__)

PROVIDER_FACTORIES = {
    "groq": lambda model="llama-3.3-70b-versatile": get_groq_client(model),
    "openrouter": lambda model="meta-llama/llama-3.3-70b-instruct:free": get_openrouter_client(model),
    "nvidia": lambda model="nvidia/llama-3.1-nemotron-70b-instruct": get_nvidia_client(model),
    "google": lambda model="gemini-2.0-flash": get_google_client(model),
    "cohere": lambda model="command-r-plus": get_cohere_client(model),
    "sambanova": lambda model="Meta-Llama-3.3-70B-Instruct": get_sambanova_client(model),
}

ROUTING = {
    "risk":      {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash"]},
    "supply":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:qwen/qwen-2.5-72b-instruct:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "sambanova:Meta-Llama-3.3-70B-Instruct"]},
    "logistics": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"]},
    "market":    {"primary": "openrouter:deepseek/deepseek-r1:free", "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile", "google:gemini-2.0-flash"]},
    "finance":   {"primary": "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "fallback": ["openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile", "cohere:command-r-plus"]},
    "brand":     {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["google:gemini-2.0-flash", "openrouter:google/gemma-2-9b-it:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"]},
    "moderator": {"primary": "google:gemini-2.0-flash", "fallback": ["openrouter:deepseek/deepseek-r1:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile"]},
}

class LLMRouter:
    _clients = {}

    def _get_client(self, provider: str, model: str):
        key = f"{provider}:{model}"
        if key not in self._clients:
            factory = PROVIDER_FACTORIES.get(provider)
            if not factory:
                raise ValueError(f"Unknown provider: {provider}")
            self._clients[key] = factory(model)
        return self._clients[key]

    async def invoke_with_fallback(self, agent: str, messages: list):
        config = ROUTING.get(agent, ROUTING["risk"])

        # Try primary
        try:
            provider, model = config["primary"].split(":", 1)
            client = self._get_client(provider, model)
            response = await client.ainvoke(messages)
            return response, config["primary"]
        except Exception as e:
            logger.warning(f"Primary failed for {agent}: {e}")

        # Try fallbacks
        for fb in config["fallback"]:
            try:
                provider, model = fb.split(":", 1)
                client = self._get_client(provider, model)
                response = await client.ainvoke(messages)
                return response, fb
            except Exception as e:
                logger.warning(f"Fallback {fb} failed for {agent}: {e}")

        raise RuntimeError(f"All LLM providers failed for agent {agent}")

llm_router = LLMRouter()
```

#### 13:30 — Test LLM connections

```python
# Quick test script
import asyncio
from backend.llm.router import llm_router

async def test_providers():
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand", "moderator"]:
        try:
            response, model = await llm_router.invoke_with_fallback(agent, [
                {"role": "user", "content": "Say 'hello' in one word."}
            ])
            print(f"✅ {agent}: {model} → {response.content[:50]}")
        except Exception as e:
            print(f"❌ {agent}: {e}")

asyncio.run(test_providers())
```

**✅ Checkpoint:** LLM router working with 6 providers + fallback chains

---

### 14:00–15:00 — Health + Auth + Rate Limit Endpoints

#### 14:00 — Create health routes

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

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["neon_postgres"] = "ok"
    except:
        checks["neon_postgres"] = "error"

    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
```

#### 14:20 — Create models status endpoint

```python
# backend/routes/models.py

from fastapi import APIRouter
from backend.llm.router import PROVIDER_FACTORIES
import os
import time

router = APIRouter()

@router.get("/status")
async def models_status():
    providers = {}
    for name, factory in PROVIDER_FACTORIES.items():
        try:
            start = time.time()
            client = factory()
            await client.ainvoke([{"role": "user", "content": "ping"}])
            providers[name] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
        except:
            providers[name] = {"available": False, "latency_ms": None}
    return {"providers": providers}
```

#### 14:40 — Register routes in main.py

```python
# Add to backend/main.py

from backend.routes.health import router as health_router
from backend.routes.models import router as models_router

app.include_router(health_router, tags=["Health"])
app.include_router(models_router, prefix="/models", tags=["Models"])
```

#### 14:50 — Test endpoints

```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":...}

curl http://localhost:8000/ready
# {"status":"ok","checks":{"neon_postgres":"ok","redis":"ok"}}

curl -H "X-API-Key: dev-key" http://localhost:8000/models/status
# {"providers":{"groq":{"available":true,...},...}}
```

**✅ Checkpoint:** Health + models endpoints working

---

### 15:00–16:00 — Council State + Graph Skeleton

#### 15:00 — Create state.py

```python
# backend/state.py

from typing import TypedDict, List, Optional
from pydantic import BaseModel

class AgentOutput(BaseModel):
    agent: str
    confidence: float
    contribution: str
    key_points: List[str]
    model_used: str
    provider: str

class Evidence(BaseModel):
    type: str
    id: str
    tag: Optional[str] = None

class Action(BaseModel):
    type: str
    details: str
    cost_estimate: Optional[float] = None
    time_to_implement: Optional[str] = None

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
    context: Optional[dict]
```

#### 15:20 — Create graph skeleton

```python
# backend/graph.py

from langgraph.graph import StateGraph, END
from backend.state import CouncilState
import logging

logger = logging.getLogger(__name__)

def moderator_parse(state: CouncilState) -> dict:
    """Round 0: Parse query and initialize."""
    return {"round_number": 1}

def placeholder_agent(state: CouncilState) -> dict:
    """Placeholder — will be replaced by real agents in Phase 2."""
    return {"agent_outputs": []}

def should_debate(state: CouncilState) -> str:
    """Check if debate is needed."""
    return "synthesize"

def synthesize(state: CouncilState) -> dict:
    """Synthesize final recommendation."""
    return {
        "recommendation": "Placeholder recommendation",
        "confidence": 0.0,
    }

def build_council_graph() -> StateGraph:
    graph = StateGraph(CouncilState)

    graph.add_node("moderator", moderator_parse)
    graph.add_node("risk", placeholder_agent)
    graph.add_node("supply", placeholder_agent)
    graph.add_node("logistics", placeholder_agent)
    graph.add_node("market", placeholder_agent)
    graph.add_node("finance", placeholder_agent)
    graph.add_node("brand", placeholder_agent)
    graph.add_node("synthesize", synthesize)

    graph.set_entry_point("moderator")

    # Fan-out from moderator to all agents
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge("moderator", agent)
        graph.add_conditional_edges(agent, should_debate, {
            "debate": "moderator",
            "synthesize": "synthesize",
        })

    graph.add_edge("synthesize", END)

    return graph
```

#### 15:40 — Test graph compilation

```python
# Quick test
from backend.graph import build_council_graph

graph = build_council_graph()
compiled = graph.compile()
print("✅ Graph compiled successfully")
print(f"Nodes: {list(compiled.nodes.keys())}")
```

**✅ Checkpoint:** Council state + graph skeleton compiled

---

### 16:00–17:00 — Tests + Verification

#### 16:00 — Create test conftest

```python
# backend/tests/conftest.py

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop; loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def api_headers():
    return {"X-API-Key": "dev-key"}
```

#### 16:10 — Create basic tests

```python
# backend/tests/test_api.py

import pytest

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_ready(client):
    r = await client.get("/ready")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_auth_required(client):
    r = await client.post("/council/analyze", json={"query": "test"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_auth_valid(client, api_headers):
    # Any authenticated endpoint
    r = await client.get("/models/status", headers=api_headers)
    assert r.status_code == 200
```

```python
# backend/tests/test_llm_router.py

import pytest
from backend.llm.router import LLMRouter

class TestRouter:
    def test_all_agents_routed(self):
        router = LLMRouter()
        assert set(router.ROUTING.keys()) == {"risk","supply","logistics","market","finance","brand","moderator"}

    def test_fallback_chains(self):
        router = LLMRouter()
        for agent, cfg in router.ROUTING.items():
            assert len(cfg["fallback"]) >= 2
```

```python
# backend/tests/test_council.py

import pytest
from backend.graph import build_council_graph

class TestGraph:
    def test_compiles(self):
        graph = build_council_graph()
        assert graph is not None

    def test_has_all_nodes(self):
        graph = build_council_graph()
        compiled = graph.compile()
        for node in ["moderator", "risk", "supply", "logistics", "market", "finance", "brand", "synthesize"]:
            assert node in compiled.nodes
```

#### 16:40 — Run all tests

```bash
cd backend
pytest -v

# Expected output:
# test_api.py::test_health PASSED
# test_api.py::test_ready PASSED
# test_api.py::test_auth_required PASSED
# test_api.py::test_auth_valid PASSED
# test_llm_router.py::test_all_agents_routed PASSED
# test_llm_router.py::test_fallback_chains PASSED
# test_council.py::test_compiles PASSED
# test_council.py::test_has_all_nodes PASSED
```

#### 16:50 — Git commit

```bash
git add .
git commit -m "feat: backend foundation — FastAPI, DB connections, LLM router, council graph skeleton"
git push origin main
```

---

## Day 2 End-of-Day Verification Checklist

| # | Item | Expected | Status |
|---|------|----------|--------|
| 1 | FastAPI server starts | `uvicorn` runs without errors | ⬜ |
| 2 | `/health` returns ok | `{"status":"ok"}` | ⬜ |
| 3 | `/ready` checks DBs | Neon + Redis status | ⬜ |
| 4 | Auth middleware blocks unauthenticated | 401 on protected routes | ⬜ |
| 5 | Auth middleware allows valid key | 200 with `X-API-Key: dev-key` | ⬜ |
| 6 | Neon PG migrations applied | 7 tables created | ⬜ |
| 7 | Redis ping works | `PONG` | ⬜ |
| 8 | Neo4j sample data loaded | 3 suppliers + 2 components | ⬜ |
| 9 | LLM router connects to Groq | Returns response | ⬜ |
| 10 | LLM router fallback works | Tries next provider on failure | ⬜ |
| 11 | `/models/status` returns providers | 6 provider statuses | ⬜ |
| 12 | Council graph compiles | 8 nodes present | ⬜ |
| 13 | All pytest tests pass | 8/8 green | ⬜ |
| 14 | Git pushed to repo | Latest commit on main | ⬜ |

---

## Day 1+2 Deliverables Summary

| Deliverable | File(s) | Status |
|-------------|---------|--------|
| Project structure | `backend/`, `frontend/`, `docs/`, `project/` | ✅ |
| 14 documentation files | `project/*.md` | ✅ |
| Docker Compose (Redis, Neo4j, ChromaDB) | `docker-compose.yml` | ✅ |
| FastAPI app with middleware | `backend/main.py` | ✅ |
| Pydantic config | `backend/config.py` | ✅ |
| Auth middleware | `backend/middleware/auth.py` | ✅ |
| Error handler middleware | `backend/middleware/error_handler.py` | ✅ |
| Neon PG connection + migrations | `backend/db/neon.py`, `migrations/*.sql` | ✅ |
| Redis client | `backend/db/redis_client.py` | ✅ |
| Neo4j client + seed data | `backend/db/neo4j_client.py` | ✅ |
| LLM router (6 providers + fallback) | `backend/llm/router.py` | ✅ |
| Health + models endpoints | `backend/routes/health.py`, `models.py` | ✅ |
| Council state definition | `backend/state.py` | ✅ |
| Council graph skeleton | `backend/graph.py` | ✅ |
| Basic test suite | `backend/tests/test_*.py` | ✅ |
