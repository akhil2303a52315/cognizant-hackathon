# Day 5 Development Plan

> **Date:** Day 5  
> **Focus:** Finish Phase 5 (Backend) + Start Phase 6 (Frontend Foundation) + Firecrawl Integration  
> **Current Progress:** Phases 0–5 complete, Phase 6 at 100%, Phase 7–11 at 0%  
> **Overall Project:** 48% → **~60%** ✅

---

## Morning Block (3 hrs): Finish Phase 5 — Backend Completion

### 5.9 WebSocket Connection Manager (Upgrade from Stub)
**File:** `backend/ws/server.py`

Current state: Basic stub with connect/disconnect/message. Needs:
- [x] Topic-based subscriptions (council sessions, risk alerts, rag status)
- [x] Heartbeat/ping-pong every 30s
- [x] Message schema with `type`, `payload`, `timestamp`
- [x] Connection authentication (validate API key on WS connect)
- [x] Broadcast to specific topics, not just all clients

### 5.10 WebSocket Event Protocol
**File:** `backend/ws/events.py` (NEW)

- [x] Define event types enum: `COUNCIL_TOKEN`, `COUNCIL_COMPLETE`, `RISK_ALERT`, `RAG_INDEXED`, `MCP_TOOL_RESULT`, `SETTINGS_UPDATED`
- [x] Event schema: `{type, session_id, payload, timestamp}`
- [x] Helper functions: `emit_event()`, `subscribe_topic()`, `unsubscribe_topic()`

### 5.11 Wire WebSocket to Council Graph
**File:** `backend/routes/council.py` (modify)

- [x] Stream council tokens via WebSocket in addition to SSE
- [x] Add `ws_session_id` to council stream endpoint
- [x] On `agent_start` → emit WS event
- [x] On `token` → emit WS event
- [x] On `complete` → emit WS event + broadcast to subscribers

### 5.12 PDF Export
**File:** `backend/tools/pdf_export.py` (NEW)

- [x] Install `reportlab` in venv
- [x] Generate PDF from council session data:
  - Header with session ID, query, timestamp
  - Agent contributions with confidence bars
  - Debate history
  - Final recommendation
  - Risk scores table
- [x] Add route: `GET /council/export/{session_id}` → returns PDF file

### 5.13 Formal API Tests
**File:** `tests/test_api.py` (NEW)

- [x] pytest fixtures for API client with auth headers
- [x] Test all main endpoints (26 passed, 2 skipped LLM)
- [x] Test all MCP endpoints (tools, invoke, rag_query)
- [x] Test auth rejection (no key, wrong key)
- [x] Test rate limiting (burst requests)
- [x] Test sandbox blocking (write Cypher/SQL)

### 5.14 WebSocket Streaming Tests
**File:** `tests/test_websocket.py` (NEW)

- [x] Test WS connect/disconnect
- [x] Test subscription to topics
- [x] Test council streaming via WS
- [x] Test heartbeat

---

> ⚠️ **NOTE:** Do NOT build any custom web scraper. The user will integrate Firecrawl or another advanced scraping service for best results. All web scraping/crawling must go through a dedicated scraping API (Firecrawl, Jina Reader, etc.) — no custom BeautifulSoup/Scrapy implementations.

## Midday Block (2 hrs): Firecrawl Integration — Real Web Data

### Firecrawl MCP Tools
**File:** `backend/mcp/tools/firecrawl_tools.py` (NEW)

- [x] Install `firecrawl-py` SDK in venv
- [x] Add `FIRECRAWL_API_KEY` to `backend/config.py`
- [x] Tool: `web_scrape` — Scrape single URL → clean markdown
  - Input: `{url: string, formats?: ["markdown","html"]}`
  - Output: `{content: string, metadata: object, mock: boolean}`
  - Cache TTL: 3600s
- [x] Tool: `web_crawl` — Crawl site with depth limit
  - Input: `{url: string, max_depth?: number, max_pages?: number}`
  - Output: `{pages: [{url, content, metadata}], total_pages: number, mock: boolean}`
  - Cache TTL: 86400s
- [x] Tool: `web_search` — Search + scrape top results
  - Input: `{query: string, num_results?: number}`
  - Output: `{results: [{url, title, content}], query: string, mock: boolean}`
  - Cache TTL: 1800s
- [x] Register all 3 tools in `backend/mcp/registry.py`

### Wire Firecrawl into RAG Pipeline
**File:** `backend/rag/loader.py` (modify)

- [x] Add `load_from_url(url)` function using Firecrawl
- [x] Add `load_from_crawl(url, max_depth)` for bulk ingestion
- [x] Returns `Document` objects with URL metadata
- [x] Integrate into `/rag/upload-url` endpoint (POST with URL parameter)

### Wire Firecrawl into News/Social Tools
- [x] `news_tools.py`: Replace mock `news_search` with Firecrawl web_search
- [x] `social_tools.py`: Replace mock `social_sentiment` with Firecrawl web_search
- [x] Keep mock fallbacks when Firecrawl API key is not configured

---

## Afternoon Block (4 hrs): Phase 6 — Frontend Foundation

### 6.1 Initialize Vite + React 18 + TypeScript
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

### 6.2 Install Dependencies
```bash
npm install @tanstack/react-query zustand react-router-dom
npm install recharts lucide-react clsx tailwind-merge
npm install axios socket.io-client
npm install -D tailwindcss @tailwindcss/vite postcss autoprefixer
npm install -D @types/node
```

### 6.3 Configure Tailwind CSS
**File:** `frontend/tailwind.config.ts`

- [x] Brand colors: `supply-blue`, `council-purple`, `risk-red`, `success-green`
- [x] Dark mode class strategy
- [x] Custom fonts (Inter)
- [x] Extend with shadcn-compatible tokens

### 6.4 Set Up shadcn/ui
```bash
npx shadcn@latest init
npx shadcn@latest add button card input textarea badge tabs
npx shadcn@latest add dialog dropdown tooltip separator
npx shadcn@latest add scroll-area skeleton avatar progress
npx shadcn@latest add sheet command popover
```

### 6.5 Type Definitions
**File:** `frontend/src/types/` (NEW)

- [x] `council.ts` — `CouncilSession`, `AgentOutput`, `DebateRound`, `Recommendation`
- [x] `rag.ts` — `RAGQuery`, `RAGResponse`, `Document`, `Collection`
- [x] `mcp.ts` — `MCPTool`, `MCPInvokeRequest`, `MCPInvokeResponse`
- [x] `api.ts` — `APIError`, `PaginatedResponse`, `HealthStatus`
- [x] `risk.ts` — `SupplierRisk`, `RiskHeatmap`, `RiskScore`

### 6.6 API Client
**File:** `frontend/src/lib/api.ts`

- [x] Axios instance with base URL (Vite proxy)
- [x] Request interceptor: attach `X-API-Key` header
- [x] Response interceptor: handle 401, 429, 500
- [x] Endpoints: `council`, `rag`, `risk`, `optimize`, `ingest`, `settings`, `health`, `models`
- [x] MCP client: separate instance with `X-MCP-API-Key`

### 6.7 WebSocket Client
**File:** `frontend/src/lib/socket.ts`

- [x] Native WebSocket client connecting to `ws://localhost:8000/ws`
- [x] Auto-reconnect with exponential backoff
- [x] Topic subscription helpers
- [x] Event handlers for council tokens, risk alerts

### 6.8 Zustand Stores
**File:** `frontend/src/store/`

- [x] `councilStore.ts` — Current session, agent outputs, streaming state
- [x] `settingsStore.ts` — App/RAG/MCP settings cache (persisted to localStorage)
- [x] `ragStore.ts` — Collections, stats, upload progress
- [x] `navStore.ts` — Active page, sidebar state

### 6.9 Custom Hooks
**File:** `frontend/src/hooks/`

- [x] `useCouncilQuery.ts` — TanStack Query mutation for council analyze
- [x] `useCouncilStream.ts` — SSE stream with markdown accumulation
- [x] `useWebSocket.ts` — WebSocket connection + event dispatch
- [x] `useRAGQuery.ts` — Query with mode selection
- [x] `useMCPTools.ts` — Tool list + invoke

### 6.10 Navbar Component
**File:** `frontend/src/components/layout/Navbar.tsx`

- [x] Logo + app name
- [x] Navigation links: Dashboard, Chat, Debate, Brand, Settings
- [x] Server status indicator (green/red dot, polls /health every 15s)
- [x] Settings button

### 6.11 Shared Components
**File:** `frontend/src/components/shared/`

- [x] `ConfidenceBar.tsx` — Animated confidence percentage bar
- [x] `StatusBadge.tsx` — Online/offline/error badge
- [x] `LoadingSkeleton.tsx` — Card/table/message skeletons
- [x] `Toast.tsx` — Notification toasts with auto-dismiss
- [x] `ThemeToggle.tsx` — Dark/light mode switch
- [x] `MarkdownRenderer.tsx` — Rendered markdown with fallback (marked)

### 6.12 React Router Setup
**File:** `frontend/src/App.tsx`

- [x] Routes: `/` (Dashboard), `/chat` (Chat), `/debate` (Debate), `/brand` (Brand), `/settings` (Settings)
- [x] 404 fallback page (NotFound)
- [x] Layout wrapper with Navbar + QueryClientProvider + ToastContainer

### 6.13 Vite Proxy Config
**File:** `frontend/vite.config.ts`

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/council': 'http://localhost:8000',
    '/rag': 'http://localhost:8000',
    '/risk': 'http://localhost:8000',
    '/optimize': 'http://localhost:8000',
    '/ingest': 'http://localhost:8000',
    '/settings': 'http://localhost:8000',
    '/health': 'http://localhost:8000',
    '/ready': 'http://localhost:8000',
    '/models': 'http://localhost:8000',
    '/mcp': 'http://localhost:8000',
    '/ws': { target: 'ws://localhost:8000', ws: true }
  }
}
```

---

## Day 5 Deliverables Summary

| Block | Deliverable | Files | Status |
|-------|-------------|-------|--------|
| Morning | WebSocket upgrade | `ws/server.py`, `ws/events.py`, `council.py` | ✅ Phase 5: 100% |
| Morning | PDF export | `tools/pdf_export.py`, route | ✅ Phase 5: 100% |
| Morning | Formal tests | `tests/test_api.py` (26 pass), `tests/test_websocket.py` | ✅ Phase 5: 100% |
| Midday | Firecrawl tools | `mcp/tools/firecrawl_tools.py` | ✅ 3 new MCP tools (22 total) |
| Midday | RAG URL ingestion | `rag/loader.py`, `/rag/upload-url` endpoint | ✅ Real web data |
| Midday | News/Social real data | `news_tools.py`, `social_tools.py` | ✅ Firecrawl + mock fallback |
| Afternoon | React scaffold | `frontend/` with Vite + TS | ✅ Phase 6: 6.1–6.3 |
| Afternoon | Types + API + WS client | `src/types/`, `src/lib/` | ✅ Phase 6: 6.5–6.7 |
| Afternoon | Stores + Hooks | `src/store/`, `src/hooks/` | ✅ Phase 6: 6.8–6.9 |
| Afternoon | Layout + Shared components | `src/components/`, pages, router | ✅ Phase 6: 6.10–6.13 |
| Afternoon | Production build | `npm run build` → 311KB JS, 17KB CSS | ✅ Zero TS errors |

---

## Expected Progress After Day 5

| Phase | Before | After |
|-------|--------|-------|
| Phase 5: Council API + Optimization | 64% | **100%** ✅ |
| Phase 6: Frontend Foundation | 0% | **100%** ✅ |
| MCP Tool Count | 19 | **22** (+ Firecrawl) ✅ |
| API Test Pass Rate | 0% | **26/28** (93%, 2 LLM-skipped) ✅ |
| Frontend Build | N/A | **Zero TS errors, production OK** ✅ |
| Overall Project | 48% | **~60%** ✅ |

---

## Dependencies to Install

```bash
# Backend (in .venv)
pip install reportlab firecrawl-py pytest pytest-asyncio httpx

# Frontend (new)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query zustand react-router-dom recharts \
  lucide-react clsx tailwind-merge axios socket.io-client marked highlight.js
npm install -D tailwindcss @tailwindcss/vite postcss autoprefixer @types/node
npx shadcn@latest init
```

---

## Risk / Notes

- **Firecrawl API key** required — free tier gives 500 credits/month. If no key, tools fall back to mock data. ✅ Mock fallbacks implemented.
- **ReportLab** PDF generation is synchronous — wrapped in `asyncio.to_thread()` for FastAPI. ✅ Done.
- **WebSocket** tested — SSE streaming works, WS is additive. ✅ Native WS client (not socket.io).
- **Frontend** scaffold is solid — Day 6+ depends on it. ✅ Zero TS errors, production build passes.
- **Virtual environment** — Backend uses `project/venv/` with Python 3.12. Activate with `venv\Scripts\Activate.ps1` or use `& "path/to/venv/Scripts/python.exe"`.
- **Ports** — Backend: 8000, Frontend: 3001 (3000 may be in use).
