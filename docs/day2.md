# SupplyChainGPT — Day 2 Implementation Plan

Hour-by-hour plan for Day 2. Focus: **MCP Tool Server (Phase 3)** + **RAG Pipeline (Phase 4)** + remaining backend routes.

**Prerequisites (from Day 1):** FastAPI server, 7 AI agents, LLM router with streaming, Neon PG, council graph — all working.

---

## Timeline

```
09:00 ─── 10:00  Rate Limiting Middleware + Redis/Neo4j Docker Fix
10:00 ─── 11:30  MCP Tool Server (registry, sandbox, 18 tools)
11:30 ─── 12:30  MCP Audit Logging + Caching
12:30 ─── 13:00  Lunch
13:00 ─── 14:30  RAG Pipeline (loader, chunker, embedder, vectorstore)
14:30 ─── 15:30  RAG Retriever + Generator + Hybrid RAG
15:30 ─── 16:30  Remaining Backend Routes (risk, ingest, optimize, settings)
16:30 ─── 17:00  End-to-End Testing + Git Push
```

---

## 09:00–10:00 — Rate Limiting Middleware + Redis/Neo4j Fix

### 09:00 — Rate Limiting Middleware

**File:** `backend/middleware/rate_limit.py`

```python
# Token-bucket rate limiter per API key
# - Default: 60 requests/minute for API endpoints
# - MCP: 30 requests/minute for MCP endpoints
# - Uses in-memory counter (upgrade to Redis when available)
# - Returns 429 Too Many Requests when exceeded
```

**Verification:**
- Send 61 rapid requests → expect 429 on 61st
- MCP endpoint → expect 429 after 31st

### 09:20 — Start Redis + Neo4j via Docker

```bash
docker compose up -d redis neo4j
# Wait 30s for Neo4j startup
docker compose exec redis redis-cli ping  # → PONG
```

### 09:30 — Verify Redis Connection

```bash
curl http://localhost:8000/health
# Should show: redis: "connected"
```

### 09:40 — Verify Neo4j Connection + Sample Data

```bash
curl http://localhost:8000/health
# Should show: neo4j: "connected"
```

**✅ Checkpoint:** Rate limiter working, Redis + Neo4j connected

---

## 10:00–11:30 — MCP Tool Server

### 10:00 — MCP Server Skeleton

**File:** `backend/mcp/server.py`

- FastAPI sub-app mounted at `/mcp/`
- Tool registry with JSON schema definitions
- Each tool = POST endpoint with input validation
- X-MCP-API-Key auth (separate from main API key)

### 10:15 — Tool Registry

**File:** `backend/mcp/registry.py`

```python
# ToolDefinition model:
#   name: str
#   description: str
#   input_schema: dict (JSON Schema)
#   handler: Callable
#   category: str (news | supplier | shipping | commodity | finance | social | rag)
#
# Registry stores all 18+ tools
# /mcp/tools → list all available tools
# /mcp/tools/{name} → get tool definition
# /mcp/tools/{name}/invoke → execute tool
```

### 10:30 — Sandbox Validation

**File:** `backend/mcp/sandbox.py`

- Validate Cypher queries (block WRITE operations: CREATE, MERGE, DELETE, SET, REMOVE)
- Validate SQL queries (block INSERT, UPDATE, DELETE, DROP, ALTER)
- Prompt injection detection (block common injection patterns)
- PII redaction (email, phone, SSN patterns)

### 10:45 — News Tools (3 tools)

**File:** `backend/mcp/tools/news_tools.py`

| Tool | Input | Output |
|------|-------|--------|
| `news_search` | query, date_range | List of news articles |
| `gdelt_query` | event_type, country | GDELT event data |
| `supplier_financials` | supplier_name | Financial health data |

### 11:00 — Supplier Tools (3 tools)

**File:** `backend/mcp/tools/supplier_tools.py`

| Tool | Input | Output |
|------|-------|--------|
| `neo4j_query` | cypher_query | Graph query results (sandboxed) |
| `supplier_search` | product, region | Matching suppliers from Neo4j |
| `contract_lookup` | supplier_id | Contract details from Neon PG |

### 11:15 — Shipping + Commodity + Finance + Social Tools (12 tools)

**Files:**
- `backend/mcp/tools/shipping_tools.py` (route_optimize, port_status, freight_rate)
- `backend/mcp/tools/commodity_tools.py` (commodity_price, trade_data, tariff_lookup)
- `backend/mcp/tools/finance_tools.py` (erp_query, currency_rate, insurance_claim)
- `backend/mcp/tools/social_tools.py` (social_sentiment, competitor_ads, content_generate)

### 11:25 — RAG Query Tool

**File:** Part of `backend/mcp/registry.py`

- `rag_query` tool: query → vector search → return relevant chunks
- Shared across all agents for context retrieval

**✅ Checkpoint:** 18 MCP tools registered, sandbox validation working

---

## 11:30–12:30 — MCP Audit + Caching

### 11:30 — MCP Audit Logging

**File:** `backend/mcp/audit.py`

- Log every tool invocation to Neon PG `mcp_audit_log` table
- Fields: tool_name, agent, input_hash, output_hash, latency_ms, timestamp
- Queryable via `/mcp/audit` endpoint

### 11:50 — MCP Redis Caching

**File:** `backend/mcp/cache.py`

- Cache tool results by input hash
- TTL: configurable per tool (default 1 hour for commodity/shipping, 5 min for news)
- Cache hit → return cached result + `cached: true` flag
- Cache miss → execute tool + store result

### 12:10 — LangChain Integration Wrapper

**File:** `backend/mcp/langchain_integration.py`

- Wrap MCP tools as LangChain `Tool` objects
- Agents can call tools via `tool.run()` in their system prompts
- Auto-inject tool results into agent context

### 12:20 — Test MCP Server

```bash
# List tools
curl -H "X-MCP-API-Key: dev-mcp-key" http://localhost:8000/mcp/tools

# Invoke a tool
curl -X POST -H "X-MCP-API-Key: dev-mcp-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "semiconductor"}' \
  http://localhost:8000/mcp/tools/news_search/invoke

# Test sandbox (should block)
curl -X POST -H "X-MCP-API-Key: dev-mcp-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "CREATE (n:Hack) RETURN n"}' \
  http://localhost:8000/mcp/tools/neo4j_query/invoke
# Expected: 403 - Write operations not allowed
```

**✅ Checkpoint:** MCP server with 18 tools, audit, caching, sandbox — all working

---

## 13:00–14:30 — RAG Pipeline

### 13:00 — Document Loader

**File:** `backend/rag/loader.py`

- Support: PDF, DOCX, TXT, XLSX, CSV
- Use `unstructured` library for PDF/DOCX parsing
- Fallback: `PyPDFLoader` for PDFs if unstructured unavailable
- Return: List of `Document` objects with metadata

### 13:20 — Text Chunker

**File:** `backend/rag/chunker.py`

- Recursive character text splitter
- Config: chunk_size=512 tokens, chunk_overlap=50 tokens
- Preserve metadata across chunks
- Return: List of `Document` chunks

### 13:35 — Embedding Router

**File:** `backend/rag/embedder.py`

- Primary: HuggingFace free embeddings (sentence-transformers/all-MiniLM-L6-v2)
- Fallback: OpenAI embeddings (if API key available)
- Router pattern similar to LLM router
- Return: List of embedding vectors

### 13:50 — Vector Store Manager

**File:** `backend/rag/vectorstore.py`

- Primary: ChromaDB (local, persistent, free)
- Fallback: Pinecone (cloud, if API key available)
- Methods: `add_documents()`, `similarity_search()`, `delete_collection()`
- Auto-create collection on first upload

### 14:10 — Hybrid Retriever

**File:** `backend/rag/retriever.py`

- Vector similarity search (ChromaDB/Pinecone)
- BM25 keyword search (using Neon PG full-text or in-memory)
- Reciprocal Rank Fusion (RRF) to merge results
- Optional: Cohere Rerank for better ordering
- Return: Ranked list of chunks with scores

### 14:20 — Context Constructor

**File:** `backend/rag/context.py`

- Take top-K retrieved chunks
- Inject citations [1], [2], etc.
- Build structured context string for LLM
- Include source metadata (filename, page, chunk_id)

**✅ Checkpoint:** RAG pipeline: load → chunk → embed → store → retrieve → context

---

## 14:30–15:30 — RAG Generator + Hybrid RAG

### 14:30 — RAG Generator

**File:** `backend/rag/generator.py`

- Take query + context → LLM generation
- Grounding: instruct LLM to only use provided context
- Citation extraction: match [1], [2] back to sources
- Return: answer + citations + confidence

### 14:50 — Graph RAG Retriever

**File:** `backend/rag/graph_rag.py`

- Query Neo4j supplier graph for relationship data
- E.g., "Who supplies Company X?" → traverse supply chain graph
- Return: Structured graph data as context

### 15:10 — Hybrid RAG (Vector + Graph)

**File:** `backend/rag/hybrid_rag.py`

- Merge vector RAG results + graph RAG results
- Deduplicate overlapping information
- Prioritize by relevance score
- Return: Combined context for LLM

### 15:20 — RAG API Router

**File:** `backend/rag/api.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/upload` | POST | Upload documents (multipart) |
| `/rag/query` | POST | Query RAG pipeline |
| `/rag/collections` | GET | List all collections |
| `/rag/collections/{name}` | DELETE | Delete a collection |
| `/rag/documents` | GET | List all uploaded documents |
| `/rag/stats` | GET | Get RAG pipeline stats |
| `/rag/graph-query` | POST | Query Neo4j graph |
| `/rag/hybrid-query` | POST | Vector + Graph hybrid query |
| `/rag/citations/{query_id}` | GET | Get citations for a query |
| `/rag/health` | GET | RAG pipeline health check |

### 15:25 — Wire RAG into main.py

```python
from backend.rag.api import router as rag_router
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
```

**✅ Checkpoint:** Full RAG pipeline with 10 API endpoints

---

## 15:30–16:30 — Remaining Backend Routes

### 15:30 — Risk Routes

**File:** `backend/routes/risk.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/risk/suppliers` | GET | Get all suppliers with risk scores |
| `/risk/score/{supplier_id}` | GET | Get detailed risk score for supplier |
| `/risk/heatmap` | GET | Get risk heatmap data |

### 15:50 — Ingest Routes

**File:** `backend/routes/ingest.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ingest/erp` | POST | Ingest ERP data (JSON) |
| `/ingest/news` | POST | Ingest news feed data |
| `/ingest/social` | POST | Ingest social media data |

### 16:05 — OR-Tools Route Optimizer

**File:** `backend/tools/or_tools_optimizer.py`

- Vehicle routing problem solver
- Constraints: capacity, time windows, cost
- Return: Optimized routes with cost estimates

### 16:10 — Optimize Routes

**File:** `backend/routes/optimize.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/optimize/routes` | POST | Optimize shipping routes |
| `/optimize/allocation` | POST | Optimize inventory allocation |
| `/optimize/expedite` | POST | Find expedited shipping options |

### 16:20 — Monte Carlo Simulation

**File:** `backend/tools/monte_carlo.py`

- Run N simulations with random variables
- Calculate P10/P50/P90 scenarios
- Return: Distribution + confidence intervals

### 16:25 — Settings + WebSocket Stub

**File:** `backend/routes/settings.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/settings/app` | GET/PUT | App settings |
| `/settings/rag` | GET/PUT | RAG settings |
| `/settings/mcp` | GET/PUT | MCP settings |

**File:** `backend/ws/server.py` (stub for Day 3)

- WebSocket connection manager skeleton
- Event protocol definition
- Will be wired to council graph on Day 3

**✅ Checkpoint:** All backend routes implemented

---

## 16:30–17:00 — Testing + Push

### 16:30 — Run All Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Specific test suites
pytest tests/test_api.py -v
pytest tests/test_llm_router.py -v
pytest tests/test_council.py -v
pytest tests/test_mcp.py -v
pytest tests/test_rag.py -v
```

### 16:45 — End-to-End Verification

```bash
# Full council analysis
curl -X POST -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "semiconductor shortage risk"}' \
  http://localhost:8000/council/analyze

# MCP tool invocation
curl -X POST -H "X-MCP-API-Key: dev-mcp-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "TSMC"}' \
  http://localhost:8000/mcp/tools/supplier_search/invoke

# RAG query
curl -X POST -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "supply chain risk factors"}' \
  http://localhost:8000/rag/query
```

### 16:55 — Git Commit + Push

```bash
git add .
git commit -m "feat: Day 2 - MCP tools, RAG pipeline, remaining routes, rate limiting"
git push origin main
```

---

## Day 2 Deliverables Summary

| Component | Files | Status Target |
|-----------|-------|---------------|
| Rate Limiting Middleware | `middleware/rate_limit.py` | 🟢 |
| MCP Server + Registry | `mcp/server.py`, `mcp/registry.py` | 🟢 |
| MCP Sandbox + Sanitize | `mcp/sandbox.py` | 🟢 |
| MCP Audit Logging | `mcp/audit.py` | 🟢 |
| MCP Redis Caching | `mcp/cache.py` | 🟢 |
| 18 MCP Tools | `mcp/tools/*.py` (6 files) | 🟢 |
| LangChain MCP Integration | `mcp/langchain_integration.py` | 🟢 |
| RAG Loader + Chunker | `rag/loader.py`, `rag/chunker.py` | 🟢 |
| RAG Embedder + VectorStore | `rag/embedder.py`, `rag/vectorstore.py` | 🟢 |
| RAG Retriever + Context | `rag/retriever.py`, `rag/context.py` | 🟢 |
| RAG Generator + Hybrid | `rag/generator.py`, `rag/hybrid_rag.py` | 🟢 |
| RAG API (10 endpoints) | `rag/api.py` | 🟢 |
| Risk Routes | `routes/risk.py` | 🟢 |
| Ingest Routes | `routes/ingest.py` | 🟢 |
| OR-Tools Optimizer | `tools/or_tools_optimizer.py` | 🟢 |
| Optimize Routes | `routes/optimize.py` | 🟢 |
| Monte Carlo Simulation | `tools/monte_carlo.py` | 🟢 |
| Settings Routes | `routes/settings.py` | 🟢 |
| WebSocket Stub | `ws/server.py` | 🟡 |

**Total new files: ~25** | **Total new endpoints: ~35** | **Phase 3 + 4 + partial 5 complete**

---

## Phase Progress After Day 2

| Phase | Before | After |
|-------|--------|-------|
| Phase 0: Setup & Docs | 100% | 100% |
| Phase 1: Backend Foundation | 86% | 100% |
| Phase 2: Agent Implementation | 100% | 100% |
| Phase 3: MCP Tool Server | 0% | 100% |
| Phase 4: RAG Pipeline | 0% | 100% |
| Phase 5: Council API + Optimization | 14% | 71% |
| **Overall** | **25%** | **~55%** |
