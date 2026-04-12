# SupplyChainGPT — Phase-wise Implementation Plan with Status

Complete implementation roadmap broken into phases with task-level status tracking, dependencies, timelines, and deliverables.

---

## Status Legend

| Icon | Status | Meaning |
|------|--------|---------|
| ⬜ | Not Started | Task not yet begun |
| 🟡 | In Progress | Currently being worked on |
| 🟢 | Done | Completed and verified |
| 🔴 | Blocked | Waiting on dependency or issue |
| ⏭️ | Skipped | Deferred to later phase |
| ❌ | Cancelled | Removed from scope |

---

## Phase 0: Project Setup & Documentation

**Timeline:** Week 1 (Day 1–2)  
**Goal:** Initialize project structure, finalize all documentation, set up repos

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 0.1 | Create monorepo structure (backend/, frontend/, docs/, project/) | 🟢 | Dev | Repo skeleton | — |
| 0.2 | Write README.md consolidating all PDF data | 🟢 | Dev | `README.md` | 0.1 |
| 0.3 | Write features.md | 🟢 | Dev | `features.md` | 0.1 |
| 0.4 | Write spec.md (include OpenRouter + NVIDIA API) | 🟢 | Dev | `spec.md` | 0.1 |
| 0.5 | Write agents.md (Neon PG + free models) | 🟢 | Dev | `agents.md` | 0.1 |
| 0.6 | Write mcp.md | 🟢 | Dev | `mcp.md` | 0.1 |
| 0.7 | Write rag.md (APIs, wireframes, tech-stack, workflow) | 🟢 | Dev | `rag.md` | 0.1 |
| 0.8 | Write routing.md (all routes, APIs, wireframes) | 🟢 | Dev | `routing.md` | 0.1 |
| 0.9 | Write backend.md | 🟢 | Dev | `backend.md` | 0.1 |
| 0.10 | Write frontend.md | 🟢 | Dev | `frontend.md` | 0.1 |
| 0.11 | Write testing.md | 🟢 | Dev | `testing.md` | 0.1 |
| 0.12 | Write phasewiseplan.md (this file) | 🟢 | Dev | `phasewiseplan.md` | 0.1 |
| 0.13 | Set up GitHub repo + branch protection | 🟢 | Dev | Repo URL | 0.1 |
| 0.14 | Configure .gitignore, .env.example, pre-commit hooks | 🟢 | Dev | Config files | 0.1 |

**Phase 0 Progress:** 14/14 (100%) ✅ COMPLETE

---

## Phase 1: Backend Foundation

**Timeline:** Week 1 (Day 3–5)  
**Goal:** Stand up FastAPI server, database connections, LLM router

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 1.1 | Initialize FastAPI app with CORS + middleware | 🟢 | Dev | `backend/main.py` | 0.1 |
| 1.2 | Create `backend/config.py` with Pydantic Settings | 🟢 | Dev | Config module | 0.1 |
| 1.3 | Set up Neon PostgreSQL connection pool | 🟢 | Dev | `backend/db/neon.py` | 1.2 |
| 1.4 | Run DB migrations (council, rag, mcp tables) | 🟢 | Dev | 3 migration files | 1.3 |
| 1.5 | Set up Redis client (cache helpers) | 🟡 | Dev | `backend/db/redis_client.py` | 1.2 |
| 1.6 | Set up Neo4j driver + sample supplier graph | 🟡 | Dev | `backend/db/neo4j_client.py` | 1.2 |
| 1.7 | Build LLM router with 6 provider factories + streaming | 🟢 | Dev | `backend/llm/router.py` | 1.2 |
| 1.8 | Implement per-agent fallback chains (6 unique NVIDIA models) | 🟢 | Dev | Routing table | 1.7 |
| 1.9 | Create health + readiness endpoints | 🟢 | Dev | `backend/routes/health.py` | 1.1 |
| 1.10 | Create auth middleware (API key + query param) | 🟢 | Dev | `backend/middleware/auth.py` | 1.1 |
| 1.11 | Create rate limiting middleware | ⬜ | Dev | `backend/middleware/rate_limit.py` | 1.1 |
| 1.12 | Create error handler middleware | 🟢 | Dev | `backend/middleware/error_handler.py` | 1.1 |
| 1.13 | Verify all 6 LLM providers connect (NVIDIA verified) | 🟢 | Dev | Provider health check | 1.7 |
| 1.14 | Write backend unit tests for router + config + council | 🟢 | Dev | `tests/test_llm_router.py` | 1.7 |

**Phase 1 Progress:** 12/14 (86%) — Redis/Neo4j need Docker, rate limit pending

---

## Phase 2: Agent Implementation

**Timeline:** Week 1–2 (Day 5–9)  
**Goal:** Build all 7 agents, council graph, debate logic

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 2.1 | Define `CouncilState` TypedDict + Pydantic models (Annotated reducers) | 🟢 | Dev | `backend/state.py` | 1.1 |
| 2.2 | Build Risk Sentinel agent (meta/llama-3.1-70b-instruct) | 🟢 | Dev | `backend/agents/risk_agent.py` | 1.7, 2.1 |
| 2.3 | Build Supply Optimizer agent (mistralai/mixtral-8x7b) | 🟢 | Dev | `backend/agents/supply_agent.py` | 1.7, 2.1 |
| 2.4 | Build Logistics Navigator agent (phi-3-medium-128k) | 🟢 | Dev | `backend/agents/logistics_agent.py` | 1.7, 2.1 |
| 2.5 | Build Market Intelligence agent (meta/llama-3.1-8b) | 🟢 | Dev | `backend/agents/market_agent.py` | 1.7, 2.1 |
| 2.6 | Build Finance Guardian agent (mistral-7b-instruct-v0.3) | 🟢 | Dev | `backend/agents/finance_agent.py` | 1.7, 2.1 |
| 2.7 | Build Brand Protector agent (phi-3-mini-128k) | 🟢 | Dev | `backend/agents/brand_agent.py` | 1.7, 2.1 |
| 2.8 | Build Moderator / Orchestrator node (meta/llama-3.1-70b) | 🟢 | Dev | `backend/agents/moderator.py` | 2.2–2.7 |
| 2.9 | Build supervisor graph (fan-out → debate → synthesize) | 🟢 | Dev | `backend/graph.py` | 2.8 |
| 2.10 | Implement debate routing logic (confidence gap > 20%) | 🟢 | Dev | `should_debate()` | 2.9 |
| 2.11 | Implement forced synthesis after 3 rounds | 🟢 | Dev | Round counter | 2.10 |
| 2.12 | Compile LangGraph council graph | 🟢 | Dev | `backend/graph.py` | 2.9, 1.3 |
| 2.13 | Test council graph end-to-end with real NVIDIA LLMs | 🟢 | Dev | `tests/test_council.py` | 2.12 |
| 2.14 | Test all 7 agents individually (real responses) | 🟢 | Dev | `tests/verify_e2e.py` | 2.2–2.8 |

**Phase 2 Progress:** 14/14 (100%) ✅ COMPLETE

---

## Phase 3: MCP Tool Server

**Timeline:** Week 2 (Day 9–11)  
**Goal:** Build MCP server, register 18+ tools, sandbox, caching

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 3.1 | Create MCP FastAPI sub-app | ⬜ | Dev | `backend/mcp/server.py` | 1.1 |
| 3.2 | Build tool registry with definitions | ⬜ | Dev | `backend/mcp/registry.py` | 3.1 |
| 3.3 | Implement sandbox validation (Cypher, SQL) | ⬜ | Dev | `backend/mcp/sandbox.py` | 3.1 |
| 3.4 | Implement prompt injection sanitization | ⬜ | Dev | `backend/mcp/sanitize.py` | 3.1 |
| 3.5 | Implement PII redaction | ⬜ | Dev | Part of `sandbox.py` | 3.3 |
| 3.6 | Implement MCP audit logging to Neon PG | ⬜ | Dev | `backend/mcp/audit.py` | 1.3 |
| 3.7 | Implement Redis caching for MCP results | ⬜ | Dev | `backend/mcp/cache.py` | 1.5 |
| 3.8 | Build news_tools (news_search, gdelt_query, supplier_financials) | ⬜ | Dev | `backend/mcp/tools/news_tools.py` | 3.2 |
| 3.9 | Build supplier_tools (neo4j_query, supplier_search, contract_lookup) | ⬜ | Dev | `backend/mcp/tools/supplier_tools.py` | 3.2, 1.6 |
| 3.10 | Build shipping_tools (route_optimize, port_status, freight_rate) | ⬜ | Dev | `backend/mcp/tools/shipping_tools.py` | 3.2 |
| 3.11 | Build commodity_tools (commodity_price, trade_data, tariff_lookup) | ⬜ | Dev | `backend/mcp/tools/commodity_tools.py` | 3.2 |
| 3.12 | Build finance_tools (erp_query, currency_rate, insurance_claim) | ⬜ | Dev | `backend/mcp/tools/finance_tools.py` | 3.2 |
| 3.13 | Build social_tools (social_sentiment, competitor_ads, content_generate) | ⬜ | Dev | `backend/mcp/tools/social_tools.py` | 3.2 |
| 3.14 | Build shared rag_query tool | ⬜ | Dev | Part of registry | 3.2 |
| 3.15 | Create LangChain integration wrapper | ⬜ | Dev | `backend/mcp/langchain_integration.py` | 3.2 |
| 3.16 | Test sandbox + sanitize + registry | ⬜ | Dev | `tests/test_mcp.py` | 3.3–3.5 |
| 3.17 | Test all 18 MCP tool endpoints | ⬜ | Dev | Part of `test_mcp.py` | 3.8–3.14 |

**Phase 3 Progress:** 0/17 (0%)

---

## Phase 4: RAG Pipeline

**Timeline:** Week 2–3 (Day 11–14)  
**Goal:** Build document ingestion, embedding, retrieval, generation

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 4.1 | Build document loader (PDF, DOCX, TXT, XLSX) | ⬜ | Dev | `backend/rag/loader.py` | 1.1 |
| 4.2 | Build text chunker (512 tokens, 50 overlap) | ⬜ | Dev | `backend/rag/chunker.py` | 4.1 |
| 4.3 | Build embedding router (HuggingFace free + OpenAI quality) | ⬜ | Dev | `backend/rag/embedder.py` | 1.7 |
| 4.4 | Build ChromaDB vector store manager | ⬜ | Dev | `backend/rag/vectorstore.py` | 4.3 |
| 4.5 | Build Pinecone vector store (cloud fallback) | ⬜ | Dev | Part of `vectorstore.py` | 4.3 |
| 4.6 | Build hybrid retriever (vector + BM25) | ⬜ | Dev | `backend/rag/retriever.py` | 4.4 |
| 4.7 | Add Cohere Rerank to retriever | ⬜ | Dev | Part of `retriever.py` | 4.6 |
| 4.8 | Build context constructor with citation injection | ⬜ | Dev | `backend/rag/context.py` | 4.6 |
| 4.9 | Build RAG generator (LLM + grounding) | ⬜ | Dev | `backend/rag/generator.py` | 1.7, 4.8 |
| 4.10 | Build Graph RAG retriever (Neo4j) | ⬜ | Dev | `backend/rag/graph_rag.py` | 1.6 |
| 4.11 | Build hybrid RAG (vector + graph merged) | ⬜ | Dev | `backend/rag/hybrid_rag.py` | 4.9, 4.10 |
| 4.12 | Create RAG API router (10 endpoints) | ⬜ | Dev | `backend/rag/api.py` | 4.11 |
| 4.13 | Test chunker + context + citations | ⬜ | Dev | `tests/test_rag.py` | 4.2, 4.8 |
| 4.14 | Test full RAG pipeline end-to-end | ⬜ | Dev | Part of `test_rag.py` | 4.12 |

**Phase 4 Progress:** 0/14 (0%)

---

## Phase 5: Council API + Optimization

**Timeline:** Week 3 (Day 14–16)  
**Goal:** Expose council via REST + WebSocket, add OR-Tools optimizer

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 5.1 | Build council REST routes (analyze, stream) + SSE streaming | 🟢 | Dev | `backend/routes/council.py` | 2.12 |
| 5.2 | Build risk routes (suppliers, score) | ⬜ | Dev | `backend/routes/risk.py` | 2.2 |
| 5.3 | Build ingest routes (ERP, news, social) | ⬜ | Dev | `backend/routes/ingest.py` | 3.8 |
| 5.4 | Build OR-Tools route optimizer | ⬜ | Dev | `backend/tools/or_tools_optimizer.py` | 1.1 |
| 5.5 | Build optimize routes (routes, allocation, expedite) | ⬜ | Dev | `backend/routes/optimize.py` | 5.4 |
| 5.6 | Build Monte Carlo simulation engine | ⬜ | Dev | `backend/tools/monte_carlo.py` | 1.1 |
| 5.7 | Build models status endpoint | 🟢 | Dev | `backend/routes/models.py` | 1.7 |
| 5.8 | Build settings endpoints (app, rag, mcp) | ⬜ | Dev | `backend/routes/settings.py` | 1.1 |
| 5.9 | Build WebSocket connection manager | ⬜ | Dev | `backend/ws/server.py` | 1.1 |
| 5.10 | Build WebSocket event protocol | ⬜ | Dev | `backend/ws/events.py` | 5.9 |
| 5.11 | Wire WebSocket to council graph for streaming | ⬜ | Dev | Integration code | 5.1, 5.9 |
| 5.12 | Build PDF export (reportlab) | ⬜ | Dev | Export utility | 5.1 |
| 5.13 | Test all REST API endpoints | ⬜ | Dev | `tests/test_api.py` | 5.1–5.8 |
| 5.14 | Test WebSocket streaming | ⬜ | Dev | `tests/test_websocket.py` | 5.11 |

**Phase 5 Progress:** 0/14 (0%)

---

## Phase 6: Frontend Foundation

**Timeline:** Week 3–4 (Day 16–19)  
**Goal:** Set up React app, routing, layout, shared components

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 6.1 | Initialize Vite + React 18 + TypeScript project | ⬜ | Dev | `frontend/` scaffold | 0.1 |
| 6.2 | Install all dependencies (TanStack Query, Zustand, Recharts, etc.) | ⬜ | Dev | `package.json` | 6.1 |
| 6.3 | Configure Tailwind CSS with brand colors | ⬜ | Dev | `tailwind.config.ts` | 6.1 |
| 6.4 | Set up shadcn/ui (components.json + base components) | ⬜ | Dev | 17 shadcn components | 6.1 |
| 6.5 | Create type definitions (council, agent, rag, mcp, api) | ⬜ | Dev | `src/types/` | 6.1 |
| 6.6 | Build API client (Axios) | ⬜ | Dev | `src/lib/api.ts` | 6.5 |
| 6.7 | Build WebSocket client (Socket.io) | ⬜ | Dev | `src/lib/socket.ts` | 6.5 |
| 6.8 | Build Zustand stores (council, settings, rag, nav) | ⬜ | Dev | `src/store/` | 6.5 |
| 6.9 | Build custom hooks (useCouncilQuery, useWebSocket, useRAGQuery) | ⬜ | Dev | `src/hooks/` | 6.6, 6.7 |
| 6.10 | Build Navbar component | ⬜ | Dev | `src/components/layout/Navbar.tsx` | 6.3 |
| 6.11 | Build shared components (ConfidenceBar, StatusBadge, LoadingSkeleton, Toast, ThemeToggle) | ⬜ | Dev | `src/components/shared/` | 6.3 |
| 6.12 | Set up React Router with 4 pages + 404 | ⬜ | Dev | `src/App.tsx` | 6.10 |
| 6.13 | Configure Vite proxy to backend | ⬜ | Dev | `vite.config.ts` | 6.1 |
| 6.14 | Test stores + hooks | ⬜ | Dev | `src/__tests__/` | 6.8, 6.9 |

**Phase 6 Progress:** 0/14 (0%)

---

## Phase 7: Frontend Pages

**Timeline:** Week 4–5 (Day 19–23)  
**Goal:** Build all 4 pages with full interactivity

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 7.1 | Build Dashboard page (stats, heatmap, quick query, upload, LLM status) | ⬜ | Dev | `src/pages/Dashboard.tsx` | 6.12 |
| 7.2 | Build RiskScoreGauge component | ⬜ | Dev | SVG animated gauge | 7.1 |
| 7.3 | Build StatCard component | ⬜ | Dev | Reusable stat card | 7.1 |
| 7.4 | Build RiskHeatmap component | ⬜ | Dev | World map + nodes | 7.1 |
| 7.5 | Build RAGUploadWidget component | ⬜ | Dev | Drag & drop upload | 7.1 |
| 7.6 | Build Chat page (messages, agent status, input, recommendation) | ⬜ | Dev | `src/pages/Chat.tsx` | 6.12 |
| 7.7 | Build CouncilMessage component | ⬜ | Dev | Agent message bubble | 7.6 |
| 7.8 | Build AgentStatusPanel component | ⬜ | Dev | Live confidence bars | 7.6 |
| 7.9 | Build QueryInput component | ⬜ | Dev | Chat input + buttons | 7.6 |
| 7.10 | Build RecommendationCard component | ⬜ | Dev | Final recommendation | 7.6 |
| 7.11 | Build Debate page (timeline, agent cards, predictions, Monte Carlo) | ⬜ | Dev | `src/pages/Debate.tsx` | 6.12 |
| 7.12 | Build DebateTimeline component | ⬜ | Dev | Round 1→2→3 visual | 7.11 |
| 7.13 | Build PredictionChart component (Recharts) | ⬜ | Dev | 30/60/90d forecast | 7.11 |
| 7.14 | Build MonteCarloChart component | ⬜ | Dev | P10/P50/P90 scenarios | 7.11 |
| 7.15 | Build Brand page (sentiment, comms editor, competitor, actions) | ⬜ | Dev | `src/pages/Brand.tsx` | 6.12 |
| 7.16 | Build SentimentChart component | ⬜ | Dev | 7-day trend | 7.15 |
| 7.17 | Build CrisisCommsEditor component | ⬜ | Dev | Editable drafts | 7.15 |
| 7.18 | Build CompetitorPanel component | ⬜ | Dev | Ad intelligence | 7.15 |
| 7.19 | Build modal components (Fallbacks, Audit, Settings, Reasoning) | ⬜ | Dev | `src/components/modals/` | 6.4 |
| 7.20 | Test all pages with Vitest | ⬜ | Dev | Component tests | 7.1–7.19 |

**Phase 7 Progress:** 0/20 (0%)

---

## Phase 8: Integration & End-to-End

**Timeline:** Week 5 (Day 23–25)  
**Goal:** Connect frontend ↔ backend, test full user flows

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 8.1 | Verify frontend API client connects to backend | ⬜ | Dev | API integration | 5.1, 6.6 |
| 8.2 | Verify WebSocket streaming from council graph | ⬜ | Dev | WS integration | 5.11, 6.7 |
| 8.3 | Test full council query flow (query → agents → debate → recommendation) | ⬜ | Dev | E2E flow | 8.1, 8.2 |
| 8.4 | Test RAG upload → ask → citations flow | ⬜ | Dev | RAG E2E | 8.1 |
| 8.5 | Test MCP tool calls from agent nodes | ⬜ | Dev | MCP E2E | 8.1 |
| 8.6 | Test brand crisis comms generation + approval flow | ⬜ | Dev | Brand E2E | 8.1 |
| 8.7 | Test route optimization with constraints | ⬜ | Dev | Optimize E2E | 8.1 |
| 8.8 | Test PDF export of debate trail | ⬜ | Dev | Export E2E | 8.1 |
| 8.9 | Test LLM provider fallback (simulate Groq down) | ⬜ | Dev | Fallback E2E | 8.1 |
| 8.10 | Test Redis caching (RAG + MCP repeated queries) | ⬜ | Dev | Cache E2E | 8.1 |
| 8.11 | Run Playwright E2E test suite | ⬜ | Dev | 6 browser tests | 8.3 |
| 8.12 | Fix integration bugs | ⬜ | Dev | Bug fixes | 8.1–8.11 |

**Phase 8 Progress:** 0/12 (0%)

---

## Phase 9: Security Hardening & Polish

**Timeline:** Week 5–6 (Day 25–27)  
**Goal:** Harden security, add observability, polish UI

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 9.1 | Verify API key auth on all protected endpoints | ⬜ | Dev | Security audit | 5.1 |
| 9.2 | Verify MCP sandbox blocks write Cypher/SQL | ⬜ | Dev | Sandbox audit | 3.3 |
| 9.3 | Verify prompt injection filtering on all external content | ⬜ | Dev | Injection audit | 3.4 |
| 9.4 | Verify PII redaction in Brand Agent outputs | ⬜ | Dev | PII audit | 3.5 |
| 9.5 | Verify CORS restricted to whitelisted origins | ⬜ | Dev | CORS audit | 1.1 |
| 9.6 | Verify rate limiting per endpoint | ⬜ | Dev | Rate limit audit | 1.11 |
| 9.7 | Set up LangSmith tracing for all agent runs | ⬜ | Dev | LangSmith integration | 2.12 |
| 9.8 | Add LlamaGuard prompt injection protection | ⬜ | Dev | Guard integration | 9.3 |
| 9.9 | Polish dark/light theme transitions | ⬜ | Dev | Theme polish | 7.1–7.19 |
| 9.10 | Add loading skeletons + error boundaries | ⬜ | Dev | UX polish | 7.1–7.19 |
| 9.11 | Add responsive mobile layout | ⬜ | Dev | Mobile polish | 7.1–7.19 |
| 9.12 | Run security test suite | ⬜ | Dev | `tests/test_security.py` | 9.1–9.6 |

**Phase 9 Progress:** 0/12 (0%)

---

## Phase 10: Testing & Load Validation

**Timeline:** Week 6 (Day 27–28)  
**Goal:** Achieve coverage targets, validate under load

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 10.1 | Run full backend test suite | ⬜ | Dev | pytest report | All backend |
| 10.2 | Run full frontend test suite | ⬜ | Dev | vitest report | All frontend |
| 10.3 | Achieve 75% backend coverage | ⬜ | Dev | Coverage report | 10.1 |
| 10.4 | Achieve 60% frontend coverage | ⬜ | Dev | Coverage report | 10.2 |
| 10.5 | Run Playwright E2E suite (all browsers) | ⬜ | Dev | E2E report | 10.1, 10.2 |
| 10.6 | Run Locust load test (50 concurrent users) | ⬜ | Dev | Load report | 10.1 |
| 10.7 | Validate < 8s council query latency | ⬜ | Dev | Latency report | 10.6 |
| 10.8 | Validate < 5s RAG uncached latency | ⬜ | Dev | Latency report | 10.6 |
| 10.9 | Validate $0 total operating cost (free tier) | ⬜ | Dev | Cost report | 10.6 |
| 10.10 | Fix all failing tests | ⬜ | Dev | Green test suite | 10.1–10.5 |

**Phase 10 Progress:** 0/10 (0%)

---

## Phase 11: Deployment & Demo

**Timeline:** Week 6–7 (Day 28–30)  
**Goal:** Deploy, create demo, submit

| # | Task | Status | Owner | Deliverable | Depends On |
|---|------|--------|-------|-------------|------------|
| 11.1 | Create Docker Compose (api, web, redis, neo4j) | ⬜ | Dev | `docker-compose.yml` | 10.10 |
| 11.2 | Build backend Docker image | ⬜ | Dev | Backend Dockerfile | 11.1 |
| 11.3 | Build frontend Docker image (nginx) | ⬜ | Dev | Frontend Dockerfile | 11.1 |
| 11.4 | Deploy to cloud (Render/Railway/Fly.io) | ⬜ | Dev | Live URL | 11.2, 11.3 |
| 11.5 | Set up Neon PostgreSQL production DB | ⬜ | Dev | Prod DB | 11.4 |
| 11.6 | Configure production environment variables | ⬜ | Dev | Prod .env | 11.4 |
| 11.7 | Run smoke tests on production | ⬜ | Dev | Smoke report | 11.4 |
| 11.8 | Create 3-minute demo video | ⬜ | Dev | Demo video | 11.4 |
| 11.9 | Create demo script (3 queries: crisis, risk, brand) | ⬜ | Dev | Demo script | 11.4 |
| 11.10 | Final README polish with live demo link | ⬜ | Dev | Updated README | 11.4 |
| 11.11 | Submit hackathon entry | ⬜ | Dev | Submission | 11.8, 11.10 |

**Phase 11 Progress:** 0/11 (0%)

---

## Overall Progress Summary

| Phase | Name | Tasks | Done | In Progress | Blocked | Not Started | % Complete |
|-------|------|-------|------|-------------|---------|-------------|------------|
| 0 | Setup & Docs | 14 | 14 | 0 | 0 | 0 | 100% |
| 1 | Backend Foundation | 14 | 12 | 2 | 0 | 0 | 86% |
| 2 | Agent Implementation | 14 | 14 | 0 | 0 | 0 | 100% |
| 3 | MCP Tool Server | 17 | 0 | 0 | 0 | 17 | 0% |
| 4 | RAG Pipeline | 14 | 0 | 0 | 0 | 14 | 0% |
| 5 | Council API + Optimization | 14 | 2 | 0 | 0 | 12 | 14% |
| 6 | Frontend Foundation | 14 | 0 | 0 | 0 | 14 | 0% |
| 7 | Frontend Pages | 20 | 0 | 0 | 0 | 20 | 0% |
| 8 | Integration & E2E | 12 | 0 | 0 | 0 | 12 | 0% |
| 9 | Security & Polish | 12 | 0 | 0 | 0 | 12 | 0% |
| 10 | Testing & Load | 10 | 0 | 0 | 0 | 10 | 0% |
| 11 | Deployment & Demo | 11 | 0 | 0 | 0 | 11 | 0% |
| **TOTAL** | | **166** | **42** | **2** | **0** | **122** | **25%** |

---

## Dependency Graph (Critical Path)

```
Phase 0: Docs
    │
    ▼
Phase 1: Backend Foundation ─────────────────────────────────┐
    │                                                          │
    ├─────────► Phase 2: Agents ──────┐                       │
    │                                  │                       │
    ├─────────► Phase 3: MCP Tools ───┤                       │
    │                                  │                       │
    ├─────────► Phase 4: RAG ─────────┤                       │
    │                                  │                       │
    ▼                                  ▼                       │
Phase 5: Council API + Optimize ◄──────┘                       │
    │                                                          │
    ▼                                                          │
Phase 6: Frontend Foundation ◄─────────────────────────────────┘
    │
    ▼
Phase 7: Frontend Pages
    │
    ▼
Phase 8: Integration & E2E
    │
    ├─────────► Phase 9: Security & Polish
    │
    ├─────────► Phase 10: Testing & Load
    │
    ▼
Phase 11: Deployment & Demo
```

**Critical Path:** Phase 0 → 1 → 2 → 5 → 6 → 7 → 8 → 11

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Free LLM rate limits hit during demo | High | Medium | Cache aggressively, use multiple providers |
| Neon PG free tier storage exhausted | Medium | Low | Monitor usage, clean old sessions |
| Pinecone free tier vector limit | Medium | Low | Use ChromaDB as primary, Pinecone as backup |
| WebSocket connection drops | Medium | Medium | Auto-reconnect with 3s backoff |
| Provider API key not available | High | Low | Support all 6 providers, fallback chains |
| Hackathon deadline pressure | High | High | Prioritize critical path, skip Phase 9 if needed |

---

## Timeline Gantt (30 Days)

```
Day  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
     ├───┤  Phase 0: Docs
        ├───────┤  Phase 1: Backend Foundation
              ├─────────┤  Phase 2: Agents
                    ├───────┤  Phase 3: MCP
                          ├───────┤  Phase 4: RAG
                                ├───────┤  Phase 5: API + Optimize
                                      ├───────┤  Phase 6: Frontend Foundation
                                            ├─────────┤  Phase 7: Frontend Pages
                                                  ├───────┤  Phase 8: Integration
                                                        ├───────┤  Phase 9: Security
                                                        ├───────┤  Phase 10: Testing
                                                              ├───────┤  Phase 11: Deploy
```
