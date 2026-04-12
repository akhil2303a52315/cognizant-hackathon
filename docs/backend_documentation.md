# SupplyChainGPT — Backend Documentation

> **Last Updated:** Day 2 (Phase 1–5 complete)  
> **Server:** FastAPI @ `http://localhost:8000`  
> **Total Endpoints:** 37 (32 main + 5 MCP)  
> **Python Files:** 57 modules across 10 packages

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Configuration](#3-configuration)
4. [Database Layer](#4-database-layer)
5. [Middleware Stack](#5-middleware-stack)
6. [LLM Router](#6-llm-router)
7. [Agent System](#7-agent-system)
8. [Council Graph](#8-council-graph)
9. [MCP Tool Server](#9-mcp-tool-server)
10. [RAG Pipeline](#10-rag-pipeline)
11. [API Routes](#11-api-routes)
12. [WebSocket Server](#12-websocket-server)
13. [Docker Infrastructure](#13-docker-infrastructure)
14. [Authentication & Security](#14-authentication--security)
15. [Testing & Verification](#15-testing--verification)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Main App                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  CORS     │  │  Rate    │  │  Auth    │  │  Error   │   │
│  │ Middleware│  │  Limit   │  │ Middleware│  │ Handler  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   API Routes                         │    │
│  │  /health  /models  /council  /risk  /ingest         │    │
│  │  /optimize  /settings  /rag                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────────────────┐      │
│  │  MCP Sub-App    │  │  WebSocket Server            │      │
│  │  /mcp/tools/*   │  │  /ws                         │      │
│  └─────────────────┘  └──────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Core Services                       │   │
│  │  LLM Router │ Council Graph │ RAG Pipeline           │   │
│  │  MCP Registry │ Sandbox │ Audit │ Cache              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Neon PG  │  │  Redis   │  │  Neo4j   │                 │
│  │ (Neon)   │  │ (Docker) │  │ (Docker) │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                │
│  │ ChromaDB │  │ Pinecone │                                │
│  │ (Docker) │  │ (Cloud)  │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
project/
├── docker-compose.yml              # Redis, Neo4j, ChromaDB containers
├── test.html                       # Full interactive dashboard
├── .venv/                          # Python virtual environment
│
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Pydantic Settings
│   ├── state.py                    # CouncilState TypedDict
│   ├── graph.py                    # LangGraph council graph
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── risk_agent.py           # 🛡️ Risk Sentinel (llama-3.1-70b)
│   │   ├── supply_agent.py         # 🏭 Supply Optimizer (mixtral-8x7b)
│   │   ├── logistics_agent.py      # 🚢 Logistics Navigator (phi-3-medium)
│   │   ├── market_agent.py         # 📈 Market Intelligence (llama-3.1-8b)
│   │   ├── finance_agent.py        # 💰 Finance Guardian (mistral-7b)
│   │   ├── brand_agent.py          # 🏷️ Brand Protector (phi-3-mini)
│   │   ├── moderator.py            # 🎯 Moderator/Orchestrator (llama-3.1-70b)
│   │   └── supervisor.py           # Fan-out supervisor node
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── neon.py                 # Neon PostgreSQL (asyncpg)
│   │   ├── redis_client.py         # Redis cache helpers
│   │   ├── neo4j_client.py         # Neo4j graph driver
│   │   └── migrations/
│   │       ├── 001_initial.sql     # Council sessions, agent outputs, debate
│   │       ├── 002_rag_tables.sql  # Documents, queries
│   │       └── 003_mcp_audit.sql   # MCP audit log, security audit
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── router.py               # 6-provider LLM router + fallback chains
│   │   └── providers.py            # Provider factory functions
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py               # MCP FastAPI sub-app (5 endpoints)
│   │   ├── registry.py             # Tool registry (19 tools)
│   │   ├── sandbox.py              # Cypher/SQL validation + PII redaction
│   │   ├── audit.py                # Audit logging to Neon PG
│   │   ├── cache.py                # Redis caching with per-tool TTL
│   │   ├── langchain_integration.py # Wrap MCP tools as LangChain Tools
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── news_tools.py       # news_search, gdelt_query, supplier_financials
│   │       ├── supplier_tools.py   # neo4j_query, supplier_search, contract_lookup
│   │       ├── shipping_tools.py   # route_optimize, port_status, freight_rate
│   │       ├── commodity_tools.py  # commodity_price, trade_data, tariff_lookup
│   │       ├── finance_tools.py    # erp_query, currency_rate, insurance_claim
│   │       └── social_tools.py     # social_sentiment, competitor_ads, content_generate
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                 # API key + MCP key authentication
│   │   ├── error_handler.py        # Global exception handler
│   │   └── rate_limit.py           # Token-bucket rate limiter
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── api.py                  # 10 RAG API endpoints
│   │   ├── loader.py               # Multi-format document loader
│   │   ├── chunker.py              # RecursiveCharacterTextSplitter
│   │   ├── embedder.py             # HuggingFace + OpenAI embedding router
│   │   ├── vectorstore.py          # ChromaDB + Pinecone vector store
│   │   ├── retriever.py            # Vector + BM25 + Hybrid (RRF) retrieval
│   │   ├── context.py              # Context builder with citations
│   │   ├── generator.py            # LLM-grounded answer generation
│   │   ├── graph_rag.py            # Neo4j graph RAG retriever
│   │   └── hybrid_rag.py           # Vector + Graph merged RAG
│   │
│   ├── routes/
│   │   ├── health.py               # /health, /ready
│   │   ├── models.py               # /models/status
│   │   ├── council.py              # /council/analyze, /council/stream
│   │   ├── risk.py                 # /risk/suppliers, /risk/score/{id}, /risk/heatmap
│   │   ├── ingest.py               # /ingest/erp, /ingest/news, /ingest/social
│   │   ├── optimize.py             # /optimize/routes, /allocation, /expedite, /monte-carlo
│   │   └── settings.py             # /settings/app, /rag, /mcp (GET + PUT)
│   │
│   ├── tools/
│   │   ├── or_tools_optimizer.py   # OR-Tools route + allocation optimizer
│   │   └── monte_carlo.py          # Monte Carlo simulation engine
│   │
│   ├── ws/
│   │   └── server.py               # WebSocket connection manager
│   │
│   └── connections/
│       └── __init__.py
│
└── docs/
    ├── phasewiseplan.md            # 11-phase development plan
    └── backend_documentation.md    # This file
```

---

## 3. Configuration

**File:** `backend/config.py`

Uses `pydantic-settings` with `.env` file support.

| Setting | Default | Description |
|---------|---------|-------------|
| `app_name` | SupplyChainGPT | Application title |
| `version` | 2.0.0 | API version |
| `debug` | False | Debug mode |
| `log_level` | INFO | Logging level |
| `neon_database_url` | (env) | Neon PostgreSQL connection string |
| `redis_url` | redis://localhost:6379 | Redis connection |
| `neo4j_uri` | bolt://localhost:7687 | Neo4j bolt URI |
| `neo4j_password` | testpassword | Neo4j password |
| `nvidia_api_key` | (env) | NVIDIA NIM API key |
| `openai_api_key` | (env) | OpenAI API key |
| `groq_api_key` | (env) | Groq API key |
| `openrouter_api_key` | (env) | OpenRouter API key |
| `google_api_key` | (env) | Google GenAI key |
| `cohere_api_key` | (env) | Cohere API key |
| `rate_limit_per_minute` | 60 | API rate limit |
| `mcp_rate_limit` | 30 | MCP endpoint rate limit |
| `api_keys` | ["dev-key"] | Valid API keys |
| `mcp_api_keys` | ["dev-mcp-key"] | Valid MCP API keys |
| `rag_chunk_size` | 512 | RAG chunk size (tokens) |
| `rag_chunk_overlap` | 50 | RAG chunk overlap |
| `rag_embedding_provider` | huggingface | Embedding provider (huggingface/openai) |
| `chroma_persist_dir` | ./chroma_data | ChromaDB persist directory |
| `pinecone_index_name` | supplychaingpt | Pinecone index name |
| `max_debate_rounds` | 3 | Council max debate rounds |
| `confidence_gap_threshold` | 20.0 | Gap % to trigger debate |

---

## 4. Database Layer

### 4.1 Neon PostgreSQL (`backend/db/neon.py`)

- **Driver:** `asyncpg` with connection pool
- **Schema:** 3 migration files
  - `001_initial.sql` — `council_sessions`, `agent_outputs`, `debate_history`, `llm_calls`
  - `002_rag_tables.sql` — `documents`, `rag_queries`
  - `003_mcp_audit.sql` — `mcp_audit_log`, `security_audit_log`
- **Helpers:** `execute_query()`, `fetch_one()`, `fetch_all()`
- **Init:** `init_db()` runs all migrations on startup

### 4.2 Redis (`backend/db/redis_client.py`)

- **Driver:** `redis.asyncio`
- **URL:** `redis://localhost:6379`
- **Helpers:** `cache_get()`, `cache_set()`, `cache_delete()`
- **Used by:** MCP tool caching, rate limiting

### 4.3 Neo4j (`backend/db/neo4j_client.py`)

- **Driver:** `neo4j` async driver
- **URI:** `bolt://localhost:7687`
- **Schema:** Constraints on `Supplier.id`, `Component.name`
- **Sample Data:** 5 suppliers, 4 components, SUPPLIES relationships
- **Helper:** `run_cypher()` for parameterized queries

### 4.4 ChromaDB (Docker)

- **Port:** 8001
- **Persist:** `./chroma_data`
- **Used by:** RAG vector store (primary)

### 4.5 Pinecone (Cloud)

- **Index:** `supplychaingpt`
- **Used by:** RAG vector store (cloud fallback)

---

## 5. Middleware Stack

Middleware is added in reverse order (last added = first executed):

```
Request → CORS → RateLimit → Auth → ErrorHandler → Route Handler
```

### 5.1 CORS Middleware
- **Origins:** `*` (all)
- **Methods:** `*`
- **Headers:** `*`
- **Credentials:** False

### 5.2 Rate Limit Middleware (`backend/middleware/rate_limit.py`)
- **Algorithm:** Token bucket (in-memory)
- **API limit:** 60 requests/minute per API key
- **MCP limit:** 30 requests/minute per MCP key
- **Exempt:** `/health`, `/ready`, `/docs`, `/openapi.json`, `/redoc`, `/test`
- **Response:** 429 with `{"detail": "Rate limit exceeded", "limit": N, "window": "60s"}`

### 5.3 Auth Middleware (`backend/middleware/auth.py`)
- **API endpoints:** `X-API-Key` header or `?api_key=` query param
- **MCP endpoints:** `X-MCP-API-Key` header or `?mcp_key=` query param
- **Public endpoints:** `/health`, `/ready`, `/docs`, `/openapi.json`, `/redoc`, `/test`
- **OPTIONS:** Always allowed (CORS preflight)
- **Response:** 401 with `{"detail": "Invalid API key"}`

### 5.4 Error Handler Middleware (`backend/middleware/error_handler.py`)
- Catches all unhandled exceptions
- Returns 500 with `{"detail": "Internal server error. Please try again."}`
- Logs full traceback

---

## 6. LLM Router

**File:** `backend/llm/router.py`

### Provider Factories

| Provider | Model Class | API Key Env |
|----------|-------------|-------------|
| NVIDIA NIM | `ChatOpenAI` (OpenAI-compatible) | `NVIDIA_API_KEY` |
| OpenAI | `ChatOpenAI` | `OPENAI_API_KEY` |
| Groq | `ChatGroq` | `GROQ_API_KEY` |
| OpenRouter | `ChatOpenAI` (OpenAI-compatible) | `OPENROUTER_API_KEY` |
| Google GenAI | `ChatGoogleGenerativeAI` | `GOOGLE_API_KEY` |
| Cohere | `ChatCohere` | `COHERE_API_KEY` |

### Agent Routing Table

| Agent | Primary Model | Provider | Fallback Chain |
|-------|--------------|----------|----------------|
| risk | meta/llama-3.1-70b-instruct | NVIDIA | openai → groq |
| supply | mistralai/mixtral-8x7b-instruct | NVIDIA | openai → groq |
| logistics | microsoft/phi-3-medium-128k-instruct | NVIDIA | openai → groq |
| market | meta/llama-3.1-8b-instruct | NVIDIA | openai → groq |
| finance | mistralai/mistral-7b-instruct-v0.3 | NVIDIA | openai → groq |
| brand | microsoft/phi-3-mini-128k-instruct | NVIDIA | openai → groq |
| moderator | meta/llama-3.1-70b-instruct | NVIDIA | openai → groq |

### Features
- `invoke()` — Synchronous with automatic fallback
- `stream()` — Streaming with fallback
- Per-agent temperature and max_tokens configuration

---

## 7. Agent System

**Directory:** `backend/agents/`

### 7 Agents + 1 Supervisor + 1 Moderator

Each agent follows the same pattern:
1. Receives `CouncilState` with the query
2. Builds a specialized system prompt
3. Calls LLM router with agent-specific model
4. Returns `AgentOutput` with contribution, confidence, evidence, actions

| Agent | Icon | Specialty | Key Focus |
|-------|------|-----------|-----------|
| Risk Sentinel | 🛡️ | Threat detection | Geopolitical, natural disaster, single-source risks |
| Supply Optimizer | 🏭 | Sourcing | Alternative suppliers, dual-sourcing, cost optimization |
| Logistics Navigator | 🚢 | Transportation | Route optimization, port congestion, freight rates |
| Market Intelligence | 📈 | Market trends | Demand signals, commodity prices, competitor activity |
| Finance Guardian | 💰 | Financial | Currency exposure, insurance, contract risk |
| Brand Protector | 🏷️ | Brand/reputation | Social sentiment, PR risk, ESG compliance |
| Moderator | 🎯 | Synthesis | Merges all perspectives, resolves conflicts |

---

## 8. Council Graph

**File:** `backend/graph.py`

### LangGraph Architecture

```
START → supervisor → [risk, supply, logistics, market, finance, brand] → moderator
                ↑                                                              │
                └─────────────── debate (if confidence gap > 20%) ─────────────┘
                                       │
                                   round > 3?
                                   ┌───┴───┐
                                  Yes      No
                                   │        │
                              force       loop back
                              synthesis   to agents
```

### State (`backend/state.py`)

```python
class CouncilState(TypedDict):
    query: str
    agent_outputs: Annotated[list[AgentOutput], add_outputs]
    debate_history: Annotated[list[dict], add_debate]
    round_number: int
    confidence_gap: float
    recommendation: str
    status: str
```

### Debate Logic
- After each round, check confidence gap between agents
- If gap > 20% → debate round (agents see each other's outputs)
- After 3 rounds max → forced synthesis
- Moderator produces final recommendation

---

## 9. MCP Tool Server

**Directory:** `backend/mcp/`

### Architecture

```
Client Request → MCP Sub-App → Auth Check → Tool Lookup → Sandbox Validation
                                                       ↓
                                              Cache Check (Redis)
                                                       ↓ Miss
                                              Tool Handler Execution
                                                       ↓
                                              Audit Log (Neon PG)
                                                       ↓
                                              Cache Store (Redis, TTL)
                                                       ↓
                                              JSON Response
```

### 19 Registered Tools

| # | Tool Name | Category | Cache TTL | Description |
|---|-----------|----------|-----------|-------------|
| 1 | `news_search` | news | 1800s | Search news articles |
| 2 | `gdelt_query` | news | 3600s | Query GDELT event database |
| 3 | `supplier_financials` | news | 86400s | Get supplier financial data |
| 4 | `neo4j_query` | supplier | 600s | Execute read-only Cypher query |
| 5 | `supplier_search` | supplier | 600s | Search suppliers by product/region |
| 6 | `contract_lookup` | supplier | 3600s | Look up supplier contracts |
| 7 | `route_optimize` | shipping | 1800s | Optimize shipping routes |
| 8 | `port_status` | shipping | 300s | Check port congestion status |
| 9 | `freight_rate` | shipping | 600s | Get current freight rates |
| 10 | `commodity_price` | commodity | 300s | Get commodity prices |
| 11 | `trade_data` | commodity | 3600s | Get trade flow data |
| 12 | `tariff_lookup` | commodity | 86400s | Look up tariff rates |
| 13 | `erp_query` | finance | 600s | Query ERP financial data |
| 14 | `currency_rate` | finance | 300s | Get currency exchange rates |
| 15 | `insurance_claim` | finance | 3600s | File/query insurance claims |
| 16 | `social_sentiment` | social | 600s | Analyze social media sentiment |
| 17 | `competitor_ads` | social | 1800s | Track competitor advertising |
| 18 | `content_generate` | social | 0 | Generate social media content |
| 19 | `rag_query` | rag | 600s | Query RAG knowledge base |

### Sandbox Validation (`backend/mcp/sandbox.py`)

- **Cypher write blocking:** Blocks `CREATE`, `MERGE`, `DELETE`, `DETACH DELETE`, `SET`, `REMOVE`, `DROP`, `CALL`
- **SQL write blocking:** Blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE TABLE`
- **Prompt injection detection:** 7 regex patterns (e.g., "ignore previous instructions", "you are now")
- **PII redaction:** Email, phone, SSN, credit card patterns replaced with `[REDACTED]`

### MCP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/mcp/tools` | List all 19 tools |
| GET | `/mcp/tools/{name}` | Get tool definition |
| POST | `/mcp/tools/{name}/invoke` | Invoke tool with params |
| GET | `/mcp/audit` | Get audit log |
| GET | `/mcp/health` | MCP health check |

### LangChain Integration (`backend/mcp/langchain_integration.py`)

All 19 MCP tools are wrapped as `langchain.tools.Tool` objects with:
- Synchronous `func` wrapper
- Asynchronous `coroutine` wrapper
- Proper name, description, and docstring

---

## 10. RAG Pipeline

**Directory:** `backend/rag/`

### Pipeline Flow

```
Upload → Loader → Chunker → Embedder → VectorStore
                                        ↓
Query → Retriever → Context → Generator → Answer
              ↑
        Hybrid (Vector + BM25 + RRF Fusion)
              ↑
        Graph RAG (Neo4j entity extraction)
              ↑
        Hybrid RAG (Vector + Graph merged)
```

### Component Details

| Component | File | Description |
|-----------|------|-------------|
| Loader | `loader.py` | PDF (PyPDF), DOCX, TXT, MD, CSV, XLSX (openpyxl) |
| Chunker | `chunker.py` | `RecursiveCharacterTextSplitter` — 512 tokens, 50 overlap |
| Embedder | `embedder.py` | HuggingFace `all-MiniLM-L6-v2` (free) → OpenAI fallback |
| VectorStore | `vectorstore.py` | ChromaDB (local, primary) → Pinecone (cloud, fallback) |
| Retriever | `retriever.py` | Vector search + BM25 + Reciprocal Rank Fusion |
| Context | `context.py` | Builds context with [1],[2] citations, max token limit |
| Generator | `generator.py` | LLM answer with grounding, confidence scoring |
| Graph RAG | `graph_rag.py` | Extracts entities → queries Neo4j supplier graph |
| Hybrid RAG | `hybrid_rag.py` | Merges vector + graph context → LLM synthesis |

### RAG API Endpoints (10)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/rag/upload` | Upload documents (multipart/form-data) |
| POST | `/rag/query` | Standard RAG query |
| POST | `/rag/hybrid-query` | Hybrid vector + graph RAG |
| POST | `/rag/graph-query` | Graph-only RAG (Neo4j) |
| GET | `/rag/stats` | Document/query/collection counts |
| GET | `/rag/health` | Vectorstore + embedder health |
| GET | `/rag/documents` | List uploaded documents |
| GET | `/rag/citations/{query_id}` | Get citations for a query |
| GET | `/rag/collections` | List ChromaDB collections |
| DELETE | `/rag/collections/{name}` | Delete a collection |

---

## 11. API Routes

### 11.1 Health (`backend/routes/health.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Server status + timestamp |
| GET | `/ready` | Public | Neon + Redis connectivity check |

### 11.2 Models (`backend/routes/models.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/models/status` | API Key | LLM provider status + model list |

### 11.3 Council (`backend/routes/council.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/council/analyze` | API Key | Batch council analysis (full response) |
| POST | `/council/stream` | API Key | SSE streaming council debate |

**Batch Response:**
```json
{
  "session_id": "uuid",
  "query": "...",
  "agent_outputs": [
    {
      "agent": "risk",
      "contribution": "...",
      "confidence": 85,
      "evidence": [...],
      "actions": [...],
      "model_used": "meta/llama-3.1-70b-instruct",
      "provider": "nvidia"
    }
  ],
  "recommendation": "...",
  "confidence": 82,
  "round_number": 1,
  "latency_ms": 15234,
  "status": "complete"
}
```

**Stream Events:**
```
data: {"type": "start", "session_id": "uuid"}
data: {"type": "agent_start", "agent": "risk"}
data: {"type": "token", "agent": "risk", "content": "The..."}
data: {"type": "agent_done", "agent": "risk"}
data: {"type": "complete", "recommendation": "..."}
```

### 11.4 Risk (`backend/routes/risk.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/risk/suppliers` | API Key | All suppliers with risk scores |
| GET | `/risk/score/{supplier_id}` | API Key | Detailed risk factors for supplier |
| GET | `/risk/heatmap` | API Key | Regional risk averages |

### 11.5 Ingest (`backend/routes/ingest.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/ingest/erp` | API Key | Ingest ERP data (JSON array) |
| POST | `/ingest/news` | API Key | Ingest news articles |
| POST | `/ingest/social` | API Key | Ingest social media posts |

### 11.6 Optimize (`backend/routes/optimize.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/optimize/routes` | API Key | Route optimization (OR-Tools) |
| POST | `/optimize/allocation` | API Key | Resource allocation optimization |
| POST | `/optimize/expedite` | API Key | Expedited shipping options |
| POST | `/optimize/monte-carlo` | API Key | Monte Carlo simulation |

**Monte Carlo Response:**
```json
{
  "num_simulations": 1000,
  "target_metric": "total_cost",
  "percentiles": {"p10": 10.72, "p50": 15.46, "p90": 19.46},
  "statistics": {"mean": 15.25, "std_dev": 3.54, "min": 3.27, "max": 26.99},
  "confidence_90": [10.72, 19.46]
}
```

### 11.7 Settings (`backend/routes/settings.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/settings/app` | API Key | App settings (debug, log_level, rate limits) |
| PUT | `/settings/app` | API Key | Update app settings |
| GET | `/settings/rag` | API Key | RAG settings (chunk_size, provider, etc.) |
| PUT | `/settings/rag` | API Key | Update RAG settings |
| GET | `/settings/mcp` | API Key | MCP settings (rate limit, cache TTL) |
| PUT | `/settings/mcp` | API Key | Update MCP settings |

---

## 12. WebSocket Server

**File:** `backend/ws/server.py`

- **Endpoint:** `ws://localhost:8000/ws`
- **Connection Manager:** Tracks active connections
- **Message Types:** `ping`/`pong`, `subscribe` (topic-based)
- **Broadcast:** `broadcast()` sends to all connected clients
- **Status:** Stub implementation (basic connect/disconnect/message)

---

## 13. Docker Infrastructure

**File:** `docker-compose.yml`

| Service | Image | Port | Volume | Purpose |
|---------|-------|------|--------|---------|
| Redis | `redis:7-alpine` | 6379 | `redis_data` | MCP caching, rate limiting |
| Neo4j | `neo4j:5-community` | 7474 (HTTP), 7687 (Bolt) | `neo4j_data` | Supplier graph, Graph RAG |
| ChromaDB | `chromadb/chroma:latest` | 8001 | `./chroma_data` | RAG vector store |

**Start:** `docker compose up -d`  
**Stop:** `docker compose down`  
**Status:** `docker compose ps`

---

## 14. Authentication & Security

### API Authentication
- **Header:** `X-API-Key: dev-key`
- **Query:** `?api_key=dev-key`
- **Valid keys:** Configured in `settings.api_keys` (default: `["dev-key"]`)

### MCP Authentication
- **Header:** `X-MCP-API-Key: dev-mcp-key`
- **Query:** `?mcp_key=dev-mcp-key`
- **Valid keys:** Configured in `settings.mcp_api_keys` (default: `["dev-mcp-key"]`)

### Sandbox Security
- Read-only enforcement on Cypher and SQL queries
- Prompt injection pattern detection (7 patterns)
- PII redaction (email, phone, SSN, credit card)

### Rate Limiting
- Token bucket algorithm (in-memory)
- 60 req/min for API endpoints
- 30 req/min for MCP endpoints
- Per-key tracking

---

## 15. Testing & Verification

### E2E Test Results (21/21 PASS)

| Test | Result |
|------|--------|
| GET /health | ✅ PASS |
| GET /ready | ✅ PASS |
| GET /mcp/tools (19 tools) | ✅ PASS |
| POST /mcp invoke commodity_price | ✅ PASS |
| MCP sandbox blocks writes | ✅ PASS |
| GET /mcp/audit | ✅ PASS |
| GET /rag/health | ✅ PASS |
| GET /rag/stats | ✅ PASS |
| POST /rag/query | ✅ PASS |
| POST /rag/hybrid-query | ✅ PASS |
| GET /risk/suppliers | ✅ PASS |
| GET /risk/heatmap | ✅ PASS |
| GET /risk/score/S1 | ✅ PASS |
| POST /optimize/expedite | ✅ PASS |
| POST /optimize/monte-carlo | ✅ PASS |
| POST /ingest/erp | ✅ PASS |
| GET /settings/app | ✅ PASS |
| GET /settings/rag | ✅ PASS |
| GET /settings/mcp | ✅ PASS |
| GET /models/status | ✅ PASS |
| Auth blocks no-key requests | ✅ PASS |

### Dashboard

Accessible at `http://localhost:8000/test` — 8-tab interactive dashboard with:
- Council (batch + streaming with markdown rendering)
- MCP Tools (click-to-invoke)
- RAG (upload + query with 3 modes)
- Risk (suppliers, heatmap, score lookup)
- Optimize (expedite shipping, Monte Carlo)
- Ingest (ERP, news, social)
- Settings (app, RAG, MCP)
- Health (server, Neon, Redis status)

---

## Quick Start

```bash
# 1. Start Docker services
docker compose up -d

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install fastapi uvicorn python-dotenv pydantic-settings asyncpg redis neo4j \
  langchain-core langchain-text-splitters langchain-huggingface langchain-chroma \
  langchain-openai langchain-pinecone langchain-groq langchain-openrouter \
  langchain-google-genai langchain-cohere langgraph chromadb \
  sentence-transformers newsapi-python openpyxl

# 4. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Start server
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 6. Open dashboard
# http://localhost:8000/test
```

---

*Generated as part of Day 2 development — Phases 0–5 (48% overall project progress)*
