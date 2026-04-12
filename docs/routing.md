# SupplyChainGPT — Routing & API Specification

Complete specification for all routes, API endpoints, connections, wireframes, and requirements across backend, frontend, WebSocket, MCP, and RAG layers.

---

## 1. Routing Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ROUTING ARCHITECTURE                            │
│                                                                          │
│  ┌──────────────┐     ┌──────────────────────────────────────────────┐  │
│  │   BROWSER     │     │              FASTAPI BACKEND (:8000)         │  │
│  │   (React SPA) │     │                                              │  │
│  │               │     │  ┌─────────────┐  ┌─────────────┐          │  │
│  │  :3000        │────▶│  │ /api/*      │  │ /ws/*       │          │  │
│  │               │     │  │ REST Routes │  │ WebSocket   │          │  │
│  │  /            │     │  └──────┬──────┘  └──────┬──────┘          │  │
│  │  /chat        │     │         │                │                  │  │
│  │  /debate      │     │  ┌──────▼──────────────▼──────┐           │  │
│  │  /brand       │     │  │     INTERNAL ROUTING       │           │  │
│  │               │     │  │                              │           │  │
│  │               │     │  │  ┌────────┐ ┌────────────┐ │           │  │
│  │               │     │  │  │ Council │ │ MCP Server  │ │           │  │
│  │               │     │  │  │ Graph   │ │ /mcp/*     │ │           │  │
│  │               │     │  │  └────────┘ └────────────┘ │           │  │
│  │               │     │  │                              │           │  │
│  │               │     │  │  ┌────────┐ ┌────────────┐ │           │  │
│  │               │     │  │  │ RAG    │ │ OR-Tools   │ │           │  │
│  │               │     │  │  │ /rag/* │ │ /optimize/*│ │           │  │
│  │               │     │  │  └────────┘ └────────────┘ │           │  │
│  │               │     │  └──────────────────────────────┘           │  │
│  └──────────────┘     └──────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     EXTERNAL CONNECTIONS                          │  │
│  │                                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │ Groq    │ │OpenRouter│ │ NVIDIA  │ │ Google  │ │ Cohere  │  │  │
│  │  │ (LLM)   │ │ (LLM)   │ │ (LLM)   │ │ (LLM)  │ │ (Rerank)│  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │ Neon PG │ │ Pinecone│ │ ChromaDB│ │ Neo4j   │ │ Redis   │  │  │
│  │  │ (DB)    │ │ (Vector)│ │ (Vector)│ │ (Graph) │ │ (Cache) │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │  │
│  │  │ NewsAPI │ │ GDELT   │ │ Hugging │ │Unstruct │              │  │
│  │  │ (News)  │ │ (Events)│ │ Face    │ │ (Parse) │              │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Routes

### 2.1 Route Map

| Route | Page Component | Title | Description |
|-------|---------------|-------|-------------|
| `/` | `Dashboard.tsx` | Dashboard Home | Risk heatmap, stats, quick query |
| `/dashboard` | `Dashboard.tsx` | Dashboard Home | Alias for `/` |
| `/chat` | `Chat.tsx` | Council Chat | Conversational UI with agent status |
| `/debate` | `Debate.tsx` | Debate & Predictions | Debate timeline + forecast charts |
| `/brand` | `Brand.tsx` | Brand Control Room | Sentiment + crisis comms |
| `*` | `NotFound.tsx` | 404 | Page not found |

### 2.2 React Router Setup

```tsx
// frontend/src/App.tsx

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { Chat } from "./pages/Chat";
import { Debate } from "./pages/Debate";
import { Brand } from "./pages/Brand";
import { NotFound } from "./pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/debate" element={<Debate />} />
        <Route path="/brand" element={<Brand />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### 2.3 Route Guards & Loading

```tsx
// frontend/src/components/RouteGuard.tsx

import { Suspense } from "react";
import { LoadingSkeleton } from "./LoadingSkeleton";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // Future: Add auth check here
  return <Suspense fallback={<LoadingSkeleton />}>{children}</Suspense>;
}
```

### 2.4 Navigation State

```tsx
// frontend/src/store/navigationStore.ts

import { create } from "zustand";

interface NavigationState {
  activePage: string;
  setActivePage: (page: string) => void;
  breadcrumbs: string[];
  pushBreadcrumb: (crumb: string) => void;
  popBreadcrumb: () => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  activePage: "dashboard",
  setActivePage: (page) => set({ activePage: page }),
  breadcrumbs: [],
  pushBreadcrumb: (crumb) =>
    set((state) => ({ breadcrumbs: [...state.breadcrumbs, crumb] })),
  popBreadcrumb: () =>
    set((state) => ({ breadcrumbs: state.breadcrumbs.slice(0, -1) })),
}));
```

---

## 3. Backend API Routes

### 3.1 Complete API Route Table

| Method | Endpoint | Group | Auth | Rate Limit | Description |
|--------|----------|-------|------|-----------|-------------|
| **HEALTH** | | | | | |
| GET | `/health` | core | none | none | Health check |
| GET | `/ready` | core | none | none | Readiness probe (DB + Redis + LLM) |
| **COUNCIL** | | | | | |
| POST | `/council/analyze` | council | API key | 10/min | Run full council analysis on query |
| POST | `/council/agent/{agent_name}` | council | API key | 20/min | Run single agent analysis |
| GET | `/council/{session_id}/status` | council | API key | 60/min | Get council session status |
| GET | `/council/{session_id}/result` | council | API key | 60/min | Get council final result |
| GET | `/council/{session_id}/trace` | council | API key | 30/min | Get LangSmith trace link |
| GET | `/council/{session_id}/audit` | council | API key | 30/min | Get full audit trail |
| GET | `/council/{session_id}/export/pdf` | council | API key | 10/min | Export debate as PDF |
| GET | `/council/{session_id}/export/json` | council | API key | 30/min | Export debate as JSON |
| **RISK** | | | | | |
| GET | `/risk/suppliers/{supplier_id}` | risk | API key | 60/min | Get supplier risk score |
| GET | `/risk/suppliers` | risk | API key | 30/min | List all supplier risk scores |
| POST | `/risk/score` | risk | API key | 20/min | Compute custom risk score |
| **INGEST** | | | | | |
| POST | `/ingest/erp` | ingest | API key | 10/min | Ingest POs, inventory data |
| POST | `/ingest/signals/news` | ingest | API key | 20/min | Ingest news/events batch |
| POST | `/ingest/signals/social` | ingest | API key | 20/min | Ingest social sentiment batch |
| **OPTIMIZE** | | | | | |
| POST | `/optimize/routes` | optimize | API key | 20/min | Optimize shipping routes |
| POST | `/optimize/allocation` | optimize | API key | 10/min | Optimize supplier allocation |
| POST | `/optimize/expedite` | optimize | API key | 10/min | Compare expedite tradeoffs |
| **RAG** | | | | | |
| POST | `/rag/ask` | rag | API key | 30/min | Ask RAG a question |
| POST | `/rag/upload` | rag | API key | 10/min | Upload & index a document |
| POST | `/rag/index/directory` | rag | API key | 5/min | Index a full directory |
| GET | `/rag/search` | rag | API key | 60/min | Search only (no generation) |
| DELETE | `/rag/documents/{doc_id}` | rag | API key | 10/min | Remove a document |
| GET | `/rag/stats` | rag | API key | 30/min | Pipeline statistics |
| GET | `/rag/citations/{query_id}` | rag | API key | 30/min | Get citations for a query |
| POST | `/rag/graph/tier-map` | rag | API key | 20/min | Supplier tier dependency map |
| POST | `/rag/graph/impact` | rag | API key | 20/min | Supplier failure blast radius |
| POST | `/rag/graph/alternates` | rag | API key | 20/min | Find alternate suppliers |
| **MCP** | | | | | |
| POST | `/mcp/call` | mcp | MCP key | 30/min | Execute MCP tool call |
| GET | `/mcp/tools` | mcp | MCP key | 60/min | List all registered tools |
| GET | `/mcp/tools/{tool_name}` | mcp | MCP key | 60/min | Get tool definition |
| GET | `/mcp/health` | mcp | MCP key | 60/min | MCP health check |
| GET | `/mcp/audit/{session_id}` | mcp | MCP key | 30/min | Get MCP audit trail |
| GET | `/mcp/cache/stats` | mcp | MCP key | 30/min | Cache statistics |
| **MODELS** | | | | | |
| GET | `/models/status` | models | API key | 10/min | LLM provider availability |
| GET | `/models/routing` | models | API key | 10/min | Current routing configuration |
| **SETTINGS** | | | | | |
| GET | `/settings` | settings | API key | 30/min | Get current settings |
| PUT | `/settings` | settings | API key | 10/min | Update settings |
| GET | `/settings/rag` | settings | API key | 30/min | Get RAG settings |
| PUT | `/settings/rag` | settings | API key | 10/min | Update RAG settings |
| GET | `/settings/mcp` | settings | API key | 30/min | Get MCP settings |
| PUT | `/settings/mcp` | settings | API key | 10/min | Update MCP settings |

### 3.2 FastAPI Router Organization

```python
# backend/api.py

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="SupplyChainGPT Council API",
    version="1.0.0",
    description="Multi-agent AI system for supply chain decision-making",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
health_router = APIRouter(tags=["Health"])
council_router = APIRouter(prefix="/council", tags=["Council"])
risk_router = APIRouter(prefix="/risk", tags=["Risk"])
ingest_router = APIRouter(prefix="/ingest", tags=["Ingest"])
optimize_router = APIRouter(prefix="/optimize", tags=["Optimization"])
rag_router = APIRouter(prefix="/rag", tags=["RAG"])
mcp_router = APIRouter(prefix="/mcp", tags=["MCP"])
models_router = APIRouter(prefix="/models", tags=["Models"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])

# Register all routers
app.include_router(health_router)
app.include_router(council_router)
app.include_router(risk_router)
app.include_router(ingest_router)
app.include_router(optimize_router)
app.include_router(rag_router)
app.include_router(mcp_router)
app.include_router(models_router)
app.include_router(settings_router)
```

### 3.3 Auth Middleware

```python
# backend/middleware/auth.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEYS = os.getenv("API_KEYS", "dev-key").split(",")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health endpoints
        if request.url.path in ["/health", "/ready", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key", "")
        if api_key not in API_KEYS:
            raise HTTPException(401, "Invalid API key")

        return await call_next(request)
```

---

## 4. WebSocket Routes

### 4.1 WebSocket Endpoints

| Endpoint | Direction | Purpose |
|----------|-----------|---------|
| `ws://localhost:8000/ws/council` | Bidirectional | Real-time council debate streaming |
| `ws://localhost:8000/ws/agents` | Server → Client | Agent status updates |
| `ws://localhost:8000/ws/risk` | Server → Client | Live risk score updates |

### 4.2 WebSocket Event Protocol

```python
# backend/ws/events.py

from pydantic import BaseModel
from typing import Optional
from enum import Enum

class EventType(str, Enum):
    # Client → Server
    COUNCIL_START = "council:start"
    COUNCIL_CANCEL = "council:cancel"
    AGENT_QUERY = "agent:query"
    SETTINGS_UPDATE = "settings:update"

    # Server → Client
    AGENT_STATUS = "agent:status"
    AGENT_CONTRIBUTION = "agent:contribution"
    DEBATE_ROUND = "debate:round"
    COUNCIL_COMPLETE = "council:complete"
    COUNCIL_ERROR = "council:error"
    RISK_UPDATE = "risk:update"
    MODELS_STATUS = "models:status"

class WSMessage(BaseModel):
    event: EventType
    session_id: Optional[str] = None
    data: dict

class AgentStatusPayload(BaseModel):
    agent: str
    status: str  # "idle", "thinking", "done", "error"
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    provider: Optional[str] = None

class AgentContributionPayload(BaseModel):
    agent: str
    round_number: int
    contribution: str
    confidence: float
    key_points: list[str]
    model_used: str
    provider: str

class DebateRoundPayload(BaseModel):
    round_number: int
    agents_responded: list[str]
    conflicts_identified: int
    next_action: str  # "debate" | "synthesize" | "complete"

class CouncilCompletePayload(BaseModel):
    recommendation: str
    confidence: float
    agent_outputs: list[dict]
    evidence: list[dict]
    fallback_options: list[dict]
    total_rounds: int
    total_latency_ms: int
```

### 4.3 WebSocket Server

```python
# backend/ws/server.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_to_client(self, client_id: str, message: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json(message)

    async def broadcast_to_session(self, session_id: str, message: dict):
        subscribers = self.session_subscribers.get(session_id, set())
        for client_id in subscribers:
            await self.send_to_client(client_id, message)

    async def broadcast(self, message: dict):
        for ws in self.active_connections.values():
            try:
                await ws.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/council")
async def ws_council(websocket: WebSocket):
    client_id = str(id(websocket))
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "council:start":
                session_id = await start_council(data.get("query"), data.get("context"))
                manager.session_subscribers.setdefault(session_id, set()).add(client_id)
                await manager.send_to_client(client_id, {
                    "event": "council:started",
                    "data": {"session_id": session_id},
                })
                # Start streaming council results
                asyncio.create_task(stream_council(session_id, client_id))

            elif event == "council:cancel":
                session_id = data.get("session_id")
                await cancel_council(session_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def stream_council(session_id: str, client_id: str):
    """Stream council debate events to connected client."""
    # Round 1: Agent statuses
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        await manager.send_to_client(client_id, {
            "event": "agent:status",
            "data": {"agent": agent, "status": "thinking"},
        })

    # ... agent processing happens in background ...
    # When each agent completes:
    # await manager.send_to_client(client_id, {
    #     "event": "agent:contribution",
    #     "data": {...},
    # })

    # When council completes:
    # await manager.send_to_client(client_id, {
    #     "event": "council:complete",
    #     "data": {...},
    # })
```

### 4.4 Frontend WebSocket Hook

```tsx
// frontend/src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from "react";
import { useCouncilStore } from "../store/councilStore";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/council";

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const { addAgentStatus, addAgentContribution, setCouncilResult, setError } = useCouncilStore();

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.event) {
        case "agent:status":
          addAgentStatus(message.data);
          break;
        case "agent:contribution":
          addAgentContribution(message.data);
          break;
        case "debate:round":
          // Update debate round in store
          break;
        case "council:complete":
          setCouncilResult(message.data);
          break;
        case "council:error":
          setError(message.data);
          break;
      }
    };

    ws.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const startCouncil = useCallback((query: string, context?: dict) => {
    wsRef.current?.send(JSON.stringify({
      event: "council:start",
      data: { query, context },
    }));
  }, []);

  const cancelCouncil = useCallback((sessionId: string) => {
    wsRef.current?.send(JSON.stringify({
      event: "council:cancel",
      data: { session_id: sessionId },
    }));
  }, []);

  return { startCouncil, cancelCouncil };
}
```

---

## 5. MCP Route Details

### 5.1 MCP Tool Routing Table

| Tool | Agent | Route | Method | Input | Output |
|------|-------|-------|--------|-------|--------|
| `news_search` | risk | `/mcp/call` | POST | `{agent:"risk", tool:"news_search", params:{query}}` | News articles |
| `gdelt_query` | risk | `/mcp/call` | POST | `{agent:"risk", tool:"gdelt_query", params:{country}}` | Geopolitical events |
| `supplier_financials` | risk | `/mcp/call` | POST | `{agent:"risk", tool:"supplier_financials", params:{supplier_id}}` | Financial data |
| `neo4j_query` | supply | `/mcp/call` | POST | `{agent:"supply", tool:"neo4j_query", params:{cypher_query}}` | Graph records |
| `supplier_search` | supply | `/mcp/call` | POST | `{agent:"supply", tool:"supplier_search", params:{component}}` | Alternate suppliers |
| `contract_lookup` | supply | `/mcp/call` | POST | `{agent:"supply", tool:"contract_lookup", params:{supplier_id}}` | Contract terms |
| `route_optimize` | logistics | `/mcp/call` | POST | `{agent:"logistics", tool:"route_optimize", params:{origin,dest}}` | Optimized routes |
| `port_status` | logistics | `/mcp/call` | POST | `{agent:"logistics", tool:"port_status", params:{port_name}}` | Port congestion |
| `freight_rate` | logistics | `/mcp/call` | POST | `{agent:"logistics", tool:"freight_rate", params:{lane,mode}}` | Freight rates |
| `commodity_price` | market | `/mcp/call` | POST | `{agent:"market", tool:"commodity_price", params:{commodity}}` | Price data |
| `trade_data` | market | `/mcp/call` | POST | `{agent:"market", tool:"trade_data", params:{country}}` | Trade data |
| `tariff_lookup` | market | `/mcp/call` | POST | `{agent:"market", tool:"tariff_lookup", params:{origin,dest}}` | Tariff rates |
| `erp_query` | finance | `/mcp/call` | POST | `{agent:"finance", tool:"erp_query", params:{po_id}}` | Financial data |
| `currency_rate` | finance | `/mcp/call` | POST | `{agent:"finance", tool:"currency_rate", params:{from,to}}` | Exchange rates |
| `insurance_claim` | finance | `/mcp/call` | POST | `{agent:"finance", tool:"insurance_claim", params:{incident_id}}` | Claim status |
| `social_sentiment` | brand | `/mcp/call` | POST | `{agent:"brand", tool:"social_sentiment", params:{brand}}` | Sentiment data |
| `competitor_ads` | brand | `/mcp/call` | POST | `{agent:"brand", tool:"competitor_ads", params:{competitor}}` | Ad intelligence |
| `content_generate` | brand | `/mcp/call` | POST | `{agent:"brand", tool:"content_generate", params:{type,context}}` | Content drafts |
| `rag_query` | all | `/mcp/call` | POST | `{agent:"any", tool:"rag_query", params:{question}}` | Document answers |

---

## 6. LLM Provider Routing

### 6.1 Provider Connection Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM PROVIDER ROUTING                          │
│                                                                  │
│  ┌───────────────┐                                              │
│  │  LLM Router    │                                              │
│  │                │                                              │
│  │  Agent Request │                                              │
│  │       │        │                                              │
│  │       ▼        │                                              │
│  │  ┌─────────┐  │                                              │
│  │  │ Routing  │  │                                              │
│  │  │ Table    │  │                                              │
│  │  └────┬────┘  │                                              │
│  │       │        │                                              │
│  └───────┼────────┘                                              │
│          │                                                        │
│   ┌──────┼──────────────────────────────────────┐               │
│   │      │                                      │               │
│   ▼      ▼          ▼            ▼              ▼               │
│ ┌────┐ ┌──────┐ ┌────────┐ ┌─────────┐ ┌─────────┐            │
│ │Groq│ │Open  │ │ NVIDIA │ │ Google  │ │ Cohere  │            │
│ │    │ │Router │ │ NIM    │ │ Gemini  │ │         │            │
│ │Free│ │Free   │ │ Free   │ │ Free    │ │ Free    │            │
│ │30RPM│ │20RPM │ │1000/day│ │ 15RPM  │ │ 10RPM   │            │
│ └────┘ └──────┘ └────────┘ └─────────┘ └─────────┘            │
│                                                                  │
│  Fallback Chain: Primary → FB1 → FB2 → FB3                     │
│  On failure:    Try next in chain → Log error → Track latency   │
│  All responses:  Tagged with provider + model for audit         │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Per-Agent LLM Routing (Free Models Only)

| Agent | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|-------|---------|-----------|-----------|-----------|
| risk | `groq:llama-3.3-70b-versatile` | `nvidia:nemotron-70b` | `openrouter:llama-3.3-70b:free` | `google:gemini-2.0-flash` |
| supply | `groq:llama-3.3-70b-versatile` | `openrouter:qwen-2.5-72b:free` | `nvidia:mixtral-8x22b` | `sambanova:llama-3.3-70b` |
| logistics | `groq:llama-3.3-70b-versatile` | `openrouter:llama-3.3-70b:free` | `google:gemini-2.0-flash` | `nvidia:nemotron-70b` |
| market | `openrouter:deepseek-r1:free` | `nvidia:nemotron-70b` | `groq:llama-3.3-70b-versatile` | `google:gemini-2.0-flash` |
| finance | `nvidia:nemotron-70b` | `openrouter:deepseek-r1:free` | `groq:llama-3.3-70b-versatile` | `cohere:command-r-plus` |
| brand | `groq:llama-3.3-70b-versatile` | `google:gemini-2.0-flash` | `openrouter:gemma-2-9b:free` | `nvidia:nemotron-70b` |
| moderator | `google:gemini-2.0-flash` | `openrouter:deepseek-r1:free` | `nvidia:nemotron-70b` | `groq:llama-3.3-70b-versatile` |

### 6.3 Provider Health Check Endpoint

```python
# backend/routes/models.py

@mcp_router.get("/models/status")
async def models_status():
    """Check availability and latency of all LLM providers."""
    providers = {}

    # Groq
    try:
        start = time.time()
        client = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")
        await client.ainvoke([{"role": "user", "content": "ping"}])
        providers["groq"] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
    except:
        providers["groq"] = {"available": False, "latency_ms": None}

    # OpenRouter
    try:
        start = time.time()
        client = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"), model="meta-llama/llama-3.3-70b-instruct:free")
        await client.ainvoke([{"role": "user", "content": "ping"}])
        providers["openrouter"] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
    except:
        providers["openrouter"] = {"available": False, "latency_ms": None}

    # NVIDIA
    try:
        start = time.time()
        client = ChatOpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.getenv("NVIDIA_API_KEY"), model="nvidia/llama-3.1-nemotron-70b-instruct")
        await client.ainvoke([{"role": "user", "content": "ping"}])
        providers["nvidia"] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
    except:
        providers["nvidia"] = {"available": False, "latency_ms": None}

    # Google
    try:
        start = time.time()
        client = ChatGoogleGenerativeAI(google_api_key=os.getenv("GOOGLE_API_KEY"), model="gemini-2.0-flash")
        await client.ainvoke([{"role": "user", "content": "ping"}])
        providers["google"] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
    except:
        providers["google"] = {"available": False, "latency_ms": None}

    return {"providers": providers}
```

---

## 7. External API Connections

### 7.1 Connection Map

| Connection | Provider | Base URL | Auth | Free Tier | Used By |
|-----------|----------|----------|------|-----------|---------|
| **LLM** | Groq | `https://api.groq.com/openai/v1` | API Key | 30 RPM | All agents |
| **LLM** | OpenRouter | `https://openrouter.ai/api/v1` | API Key | 20 RPM (free models) | All agents |
| **LLM** | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | API Key | 1000/day | Risk, Finance, Moderator |
| **LLM** | Google AI | Generative AI SDK | API Key | 15 RPM | Moderator, Brand |
| **LLM** | Cohere | Cohere SDK | API Key | 10 RPM | Finance fallback |
| **LLM** | SambaNova | `https://api.sambanova.ai/v1` | API Key | 10 RPM | Supply fallback |
| **Embeddings** | HuggingFace | `https://api-inference.huggingface.co` | API Key | 1000/day | RAG pipeline |
| **Embeddings** | OpenAI | OpenAI SDK | API Key | Paid | RAG quality fallback |
| **Reranker** | Cohere | Cohere SDK | API Key | 1000/mo | RAG retriever |
| **Vector DB** | Pinecone | Pinecone SDK | API Key | 100K vectors | RAG storage |
| **Vector DB** | ChromaDB | Local (no API) | None | Unlimited | RAG storage (local) |
| **Graph DB** | Neo4j | bolt://localhost:7687 | Password | Community free | Graph RAG |
| **Graph DB** | Neo4j AuraDB | `neo4j+s://xxx.databases.neo4j.io` | Password | 1 instance free | Graph RAG (cloud) |
| **SQL DB** | Neon | `postgresql://...neon.tech` | Password | 0.5 GB free | State, audit, checkpointer |
| **Cache** | Redis | `redis://localhost:6379` | None | Local free | Caching |
| **Cache** | Upstash | `https://xxx.upstash.io` | Token | 10K cmds/day | Caching (cloud) |
| **News** | NewsAPI | `https://newsapi.org/v2` | API Key | 100 req/day | Risk agent |
| **Events** | GDELT | `https://api.gdeltproject.org/api/v2` | None | Free | Risk agent |
| **Observability** | LangSmith | LangChain SDK | API Key | 5K traces/mo | All agents |
| **Document Parse** | Unstructured | `https://api.unstructured.io` | API Key | 1000 pages/mo | RAG loader |

### 7.2 Connection Error Handling

```python
# backend/connections/health.py

CONNECTION_CHECKS = {
    "groq": {"url": "https://api.groq.com/openai/v1/models", "method": "GET", "headers": "Authorization"},
    "openrouter": {"url": "https://openrouter.ai/api/v1/models", "method": "GET", "headers": "Authorization"},
    "nvidia": {"url": "https://integrate.api.nvidia.com/v1/models", "method": "GET", "headers": "Authorization"},
    "pinecone": {"check": "pinecone_client.list_indexes"},
    "neo4j": {"check": "driver.verify_connectivity"},
    "neon": {"check": "asyncpg.connect"},
    "redis": {"check": "redis_client.ping"},
}

async def check_all_connections() -> dict:
    """Check health of all external connections."""
    results = {}
    for name, config in CONNECTION_CHECKS.items():
        try:
            if "url" in config:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(config["url"])
                    results[name] = {"status": "ok" if resp.status_code < 400 else "error", "code": resp.status_code}
            else:
                # Custom check
                results[name] = {"status": "ok"}
        except Exception as e:
            results[name] = {"status": "error", "message": str(e)[:100]}
    return results
```

---

## 8. Frontend Wireframes

### 8.1 Page 1: Dashboard (`/`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🏠 SupplyChainGPT                              [🌙] [⚙️] [👤]       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ ⚠️ Risk Score │  │ 🔴 Active    │  │ 💰 Predicted │  │ 📊 Council │ │
│  │    72/100     │  │  Disruptions │  │   Savings    │  │   Queries  │ │
│  │   HIGH ▲     │  │      3       │  │   $2.4M      │  │     47     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────┐  ┌──────────────────────────┐│
│  │ 🗺️ Risk Heatmap                      │  │ 📚 RAG Knowledge Base   ││
│  │                                       │  │                          ││
│  │    ┌─────────────────────┐            │  │  📂 Drag & drop files   ││
│  │    │  🌍 World Map       │            │  │     here to upload      ││
│  │    │  📍 Taiwan 🔴       │            │  │                          ││
│  │    │  📍 India 🟡        │            │  │  24 docs | 1,247 chunks ││
│  │    │  📍 Vietnam 🟢      │            │  │  [Index] [Clear]        ││
│  │    │  📍 Germany 🟢      │            │  └──────────────────────────┘│
│  │    └─────────────────────┘            │                              │
│  │  Click supplier node for details      │  ┌──────────────────────────┐│
│  └──────────────────────────────────────┘  │ 🤖 LLM Providers Status  ││
│                                              │                          ││
│  ┌──────────────────────────────────────┐  │  Groq    🟢 45ms        ││
│  │ 🔍 Quick Query                        │  │  OpenRouter 🟢 120ms    ││
│  │                                       │  │  NVIDIA  🟢 200ms      ││
│  │  [Ask about your supply chain...   ] │  │  Google  🟢 80ms       ││
│  │                                       │  │  Cohere  🟡 150ms      ││
│  │  [⚡ Convene Council]  [📄 Ask RAG]   │  └──────────────────────────┘│
│  └──────────────────────────────────────┘                              │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 📋 Recent Queries                                                 │  │
│  │ ┌────────────────────┬──────────┬────────────┬─────────┐        │  │
│  │ │ Query              │ Status   │ Confidence │ Time    │        │  │
│  │ ├────────────────────┼──────────┼────────────┼─────────┤        │  │
│  │ │ Taiwan chip crisis │ Complete │ 87%        │ 6.2s    │        │  │
│  │ │ S1 lead time +2wk  │ Complete │ 92%        │ 5.8s    │        │  │
│  │ │ Port Shanghai delay│ Complete │ 78%        │ 7.1s    │        │  │
│  │ └────────────────────┴──────────┴────────────┴─────────┘        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Page 2: Council Chat (`/chat`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🏠 SupplyChainGPT  > Council Chat              [🌙] [⚙️] [👤]         │
├────────────┬─────────────────────────────────────────────────────────────┤
│            │                                                              │
│ 📂 History │  ┌───────────────────────────────────────────────────────┐ │
│            │  │  🤖 Moderator                                          │ │
│ ▶ Taiwan   │  │  Council convened for: "Taiwan chip crisis impact"   │ │
│   Crisis   │  │  Running 6 agents in parallel...                      │ │
│ ▶ Port     │  │                                                        │ │
│   Strike   │  │  ┌─────────────────────────────────────────────────┐ │ │
│ ▶ S2 Delay │  │  │ 🤖 Risk Sentinel (87% confidence)              │ │ │
│ ▶ Lithium  │  │  │ Taiwan geopolitical risk: CRITICAL. Score: 82.  │ │ │
│   Price     │  │  │ Key drivers: China tensions, earthquake risk.  │ │ │
│            │  │  │ Model: Groq Llama-3.3-70B                       │ │ │
│ 💾 Saved   │  │  └─────────────────────────────────────────────────┘ │ │
│            │  │                                                        │ │
│ ▶ Taiwan   │  │  ┌─────────────────────────────────────────────────┐ │ │
│   v2       │  │  │ 🤖 Supply Optimizer (91% confidence)            │ │ │
│            │  │  │ 2 alternate suppliers identified: S2 (India),   │ │ │
│            │  │  │ S3 (Vietnam). Onboarding: 7-14 days.            │ │ │
│            │  │  │ Model: Groq Llama-3.3-70B                       │ │ │
│            │  │  └─────────────────────────────────────────────────┘ │ │
│            │  │                                                        │ │
│            │  │  ⚡ Debate Round 2: Supply challenges Logistics     │ │
│            │  │  on reroute timeline...                               │ │
│            │  │                                                        │ │
│            │  │  ┌─────────────────────────────────────────────────┐ │ │
│            │  │  │ 🏆 FINAL RECOMMENDATION (89% confidence)        │ │ │
│            │  │  │ 1. Activate S2 (India) for C1 immediately       │ │ │
│            │  │  │ 2. Air freight bridge for 2-week gap            │ │ │
│            │  │  │ 3. Launch "Pre-order" campaign                  │ │ │
│            │  │  │ Fallbacks: Tier 1 → Tier 2 → Tier 3            │ │ │
│            │  │  └─────────────────────────────────────────────────┘ │ │
│            │  │                                                        │ │
│            │  │  [📋 View Audit] [📄 Export PDF] [📧 Email Leadership]│ │
│            │  └───────────────────────────────────────────────────────┘ │
│            │                                                              │
│            │  ┌───────────────────────────────────────────────────────┐ │
│ 🤖 Agents  │  │  Ask the Council...                    [⚡ Convene]  │ │
│            │  │  [📄 Ask RAG] [🎯 Single Agent ▼]                    │ │
│ ⚠️ Risk 87%│  └───────────────────────────────────────────────────────┘ │
│ 📦 Supply91│                                                             │
│ 🚛 Logis 85│  ┌───────────────────────────────────────────────────────┐ │
│ 📈 Market78│  │  🤖 Agent Status (Live)                                │ │
│ 💰 Finance │  │  ⚠️ Risk ████████░░ 87%  ✅ Done                     │ │
│   82%      │  │  📦 Supply █████████░ 91%  ✅ Done                   │ │
│ 🏷️ Brand 75│  │  🚛 Logis ████████░░ 85%  ✅ Done                   │ │
│ 🎯 Mod 89% │  │  📈 Market ███████░░░ 78%  ✅ Done                  │ │
│            │  │  💰 Finance████████░░ 82%  ✅ Done                    │ │
│            │  │  🏷️ Brand ███████░░░ 75%  ✅ Done                   │ │
│            │  │  🎯 Moderator████████░ 89%  ✅ Done                  │ │
│            │  └───────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────┘
```

### 8.3 Page 3: Debate & Predictions (`/debate`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🏠 SupplyChainGPT  > Debate & Predictions       [🌙] [⚙️] [👤]       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Query: "Taiwan chip crisis impact"          Overall Confidence: 89%    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 🔄 Debate Timeline                                               │  │
│  │                                                                   │  │
│  │  ● Round 1 ─── Parallel Analysis ──── All 6 agents responded     │  │
│  │  │                                                                │  │
│  │  ● Round 2 ─── Challenges ──── Supply ↔ Logistics conflict      │  │
│  │  │              (7-day onboarding vs 3-day air freight gap)       │  │
│  │  │                                                                │  │
│  │  ● Round 3 ─── Final Synthesis ──── Moderator resolved          │  │
│  │                 Confidence-weighted vote: 89%                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────┐  ┌──────────────────────────────┐│
│  │ 🤖 Agent Cards                   │  │ 📈 Predictions (30/60/90d)  ││
│  │                                  │  │                              ││
│  │ ⚠️ Risk    87%  │ View Reasoning │  │  ┌──────────────────────┐  ││
│  │ 📦 Supply  91%  │ View Reasoning │  │  │ 📊 Prophet + LSTM    │  ││
│  │ 🚛 Logis   85%  │ View Reasoning │  │  │    forecast chart    │  ││
│  │ 📈 Market  78%  │ View Reasoning │  │  │ 30d: Risk → Medium   │  ││
│  │ 💰 Finance 82%  │ View Reasoning │  │  │ 60d: Risk → Low      │  ││
│  │ 🏷️ Brand   75%  │ View Reasoning │  │  │ 90d: Risk → Low      │  ││
│  └─────────────────────────────────┘  │  └──────────────────────┘  ││
│                                        │                              ││
│  ┌─────────────────────────────────┐  │  ┌──────────────────────┐  ││
│  │ 🎲 Monte Carlo Scenarios        │  │  │ 🏷️ Brand Sentiment   │  ││
│  │                                  │  │  │                      │  ││
│  │  10,000 scenarios simulated      │  │  │  Score: 62/100      │  ││
│  │  P10: $800K exposure             │  │  │  Trend: ▼ declining │  ││
│  │  P50: $1.2M exposure             │  │  │  Alert: ⚠️ Crisis   │  ││
│  │  P90: $2.4M exposure             │  │  └──────────────────────┘  ││
│  └─────────────────────────────────┘  └──────────────────────────────┘│
│                                                                          │
│  [📋 View Full Audit] [📄 Export PDF] [📊 Export JSON]                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Page 4: Brand Control Room (`/brand`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🏠 SupplyChainGPT  > Brand Control Room         [🌙] [⚙️] [👤]       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐│
│  │ 🏷️ Live Sentiment             │  │ 📰 Auto-Generated Comms          ││
│  │                               │  │                                   ││
│  │  Score: 62/100  ▼ declining   │  │  📝 Press Release [DRAFT]        ││
│  │                               │  │  ┌────────────────────────────┐ ││
│  │  ┌─────────────────────────┐ │  │  │ Company Statement on...    │ ││
│  │  │ 📊 Sentiment Trend Chart│ │  │  │ [Edit] [Approve] [Reject] │ ││
│  │  │ 7-day rolling average   │ │  │  └────────────────────────────┘ ││
│  │  └─────────────────────────┘ │  │                                   ││
│  │                               │  │  🐦 Social Posts [DRAFT]        ││
│  │  Negative topics:             │  │  ┌────────────────────────────┐ ││
│  │  • "delivery delays" (2.4K)   │  │  │ Twitter: We're committed..│ ││
│  │  • "stock shortage" (1.8K)    │  │  │ LinkedIn: As a company...  │ ││
│  │  • "price increase" (1.2K)    │  │  │ [Edit] [Approve] [Reject] │ ││
│  └──────────────────────────────┘  │  └────────────────────────────┘ ││
│                                      │                                   ││
│  ┌──────────────────────────────┐  │  📧 Customer Email [DRAFT]       ││
│  │ 🏢 Competitor Intelligence    │  │  ┌────────────────────────────┐ ││
│  │                               │  │  │ Dear Valued Customer...    │ ││
│  │  CompetitorX:                 │  │  │ [Edit] [Approve] [Send]   │ ││
│  │  • Ad spend ▲ increasing      │  │  └────────────────────────────┘ ││
│  │  • Targeting our keywords ✅  │  └──────────────────────────────────┘│
│  │  • "Always in Stock" campaign │                                      │
│  │                               │  ┌──────────────────────────────────┐│
│  │  ⚠️ ALERT: CompetitorX is     │  │ 📢 Ad Pivot Recommendations      ││
│  │  exploiting our disruption!    │  │                                   ││
│  └──────────────────────────────┘  │  ✅ Pause product availability ads│
│                                      │  ✅ Launch "Pre-order Now" campaign│
│  ┌──────────────────────────────┐  │  ✅ Push substitute products       ││
│  │ ⚡ Quick Actions               │  │  ❌ Do NOT increase ad spend      ││
│  │                               │  └──────────────────────────────────┘│
│  │ [🚀 Launch Campaign]          │                                      │
│  │ [⏸️ Pause All Ads]            │  ┌──────────────────────────────────┐│
│  │ [📧 Notify Stakeholders]      │  │ 🎯 Crisis Scenario               ││
│  │ [📊 View Full Report]         │  │  Active: Scenario A (Shortage)    ││
│  └──────────────────────────────┘  │  Switch: [A] [B] [C] [D]         ││
│                                      └──────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.5 Modal: Fallback & Action Plan

```
┌──────────────────────────────────────────────────────────────────┐
│  📋 Fallback & Action Plan                                [✕]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🟢 TIER 1 — IMMEDIATE (0-48 Hours)                       │ │
│  │                                                            │ │
│  │ ✅ Activate backup supplier S2 (India)                     │ │
│  │    Cost: $45K  |  Time: 24h  |  Risk: Low                 │ │
│  │    [Execute ⚡]                                             │ │
│  │                                                            │ │
│  │ ✅ Emergency air freight bridge                            │ │
│  │    Cost: $185K  |  Time: 3 days  |  Risk: Low             │ │
│  │    [Execute ⚡]                                             │ │
│  │                                                            │ │
│  │ ✅ Pause product ads → Launch "Coming Soon"               │ │
│  │    Cost: $0  |  Time: 1h  |  Risk: None                   │ │
│  │    [Execute ⚡]                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🟡 TIER 2 — SHORT-TERM (2-4 Weeks)                       │ │
│  │                                                            │ │
│  │ ○ Multi-source procurement split (S2 + S3)                │ │
│  │    Cost: $120K  |  Time: 14 days  |  Risk: Medium         │ │
│  │                                                            │ │
│  │ ○ Contract manufacturing exploration                       │ │
│  │    Cost: $200K  |  Time: 21 days  |  Risk: Medium         │ │
│  │                                                            │ │
│  │ ○ Activate cargo insurance claim                           │ │
│  │    Cost: $0  |  Payout: ~$85K  |  Time: 10-15 biz days    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🔴 TIER 3 — STRATEGIC (1-6 Months)                       │ │
│  │                                                            │ │
│  │ ○ Geographic diversification (Vietnam + India sourcing)    │ │
│  │    Cost: $500K  |  Time: 90 days  |  Risk: Medium         │ │
│  │                                                            │ │
│  │ ○ Near-shoring / Friend-shoring strategy                   │ │
│  │    Cost: $1.2M  |  Time: 180 days  |  Risk: High         │ │
│  │                                                            │ │
│  │ ○ Safety stock policy revision (AI-optimized buffers)      │ │
│  │    Cost: $80K  |  Time: 30 days  |  Risk: Low             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 💰 ROI Calculator                                          │ │
│  │                                                            │ │
│  │  Disruption exposure:    $2.4M                             │ │
│  │  Mitigation cost (T1):   $230K                             │ │
│  │  Net savings:            $2.17M                            │ │
│  │  ROI:                    943%                              │ │
│  │  Time saved:             14 days                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [✅ Execute Approved Steps]  [📄 Export PDF]  [📧 Email]       │
└──────────────────────────────────────────────────────────────────┘
```

### 8.6 Modal: Audit & Observability Log

```
┌──────────────────────────────────────────────────────────────────┐
│  🔍 Audit & Observability Log                             [✕]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Session: sess_abc123  |  Query: "Taiwan chip crisis"            │
│  Duration: 6.2s  |  Rounds: 3  |  Confidence: 89%              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🔗 LangSmith Trace                                         │ │
│  │  [Open in LangSmith ↗]  [Share Public Link 📋]            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🤖 Agent Call Log                                          │ │
│  │                                                            │ │
│  │ ┌──────────┬────────────┬─────────┬────────┬─────────┐    │ │
│  │ │ Agent    │ Model      │ Provider│ Tokens │ Latency │    │ │
│  │ ├──────────┼────────────┼─────────┼────────┼─────────┤    │ │
│  │ │ Risk     │ Llama-3.3  │ Groq    │ 1,247  │ 1.2s    │    │ │
│  │ │ Supply   │ Llama-3.3  │ Groq    │ 1,892  │ 1.5s    │    │ │
│  │ │ Logistics│ Llama-3.3  │ Groq    │ 1,056  │ 0.9s    │    │ │
│  │ │ Market   │ DeepSeek-R1│ OpenRoutr│ 2,341 │ 2.1s    │    │ │
│  │ │ Finance  │ Nemotron-70│ NVIDIA  │ 1,678  │ 1.8s    │    │ │
│  │ │ Brand    │ Llama-3.3  │ Groq    │ 987    │ 0.8s    │    │ │
│  │ │ Moderator│ Gemini-2.0 │ Google  │ 2,105  │ 1.4s    │    │ │
│  │ └──────────┴────────────┴─────────┴────────┴─────────┘    │ │
│  │                                                            │ │
│  │ Total tokens: 11,306  |  Total cost: $0.00 (free tier)    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🔧 MCP Tool Calls                                          │ │
│  │                                                            │ │
│  │ ┌──────────────────┬──────────┬─────────┬─────────┐       │ │
│  │ │ Tool             │ Agent    │ Cached  │ Latency │       │ │
│  │ ├──────────────────┼──────────┼─────────┼─────────┤       │ │
│  │ │ news_search      │ risk     │ No      │ 450ms   │       │ │
│  │ │ gdelt_query      │ risk     │ Yes     │ 0ms     │       │ │
│  │ │ neo4j_query      │ supply   │ No      │ 120ms   │       │ │
│  │ │ supplier_search  │ supply   │ No      │ 200ms   │       │ │
│  │ │ route_optimize   │ logistics│ No      │ 350ms   │       │ │
│  │ │ port_status      │ logistics│ Yes     │ 0ms     │       │ │
│  │ │ commodity_price  │ market   │ Yes     │ 0ms     │       │ │
│  │ │ erp_query        │ finance  │ No      │ 180ms   │       │ │
│  │ │ social_sentiment │ brand    │ No      │ 280ms   │       │ │
│  │ └──────────────────┴──────────┴─────────┴─────────┘       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🔍 Search logs...                                               │
│  [📄 Export PDF]  [📊 Export JSON]  [🗑️ Clear]                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Requirements

### 9.1 Functional Requirements

| ID | Requirement | Priority | Route/API |
|----|-------------|----------|-----------|
| FR-01 | User can submit a supply chain query and receive multi-agent analysis | High | `POST /council/analyze` |
| FR-02 | System runs 6 domain agents in parallel, then synthesizes | High | Council Graph |
| FR-03 | Agents debate when confidence gap > 20% | High | Council Graph |
| FR-04 | Maximum 3 debate rounds before forced synthesis | High | Council Graph |
| FR-05 | Each agent returns structured output with confidence score | High | Agent nodes |
| FR-06 | Final recommendation includes actions + fallbacks + confidence | High | Moderator |
| FR-07 | User can upload documents for RAG-grounded Q&A | High | `POST /rag/upload` |
| FR-08 | RAG answers cite internal document IDs | High | `POST /rag/ask` |
| FR-09 | MCP tools provide real data to agents | High | `POST /mcp/call` |
| FR-10 | MCP tools are sandboxed per agent | High | MCP sandbox |
| FR-11 | User can optimize shipping routes | Medium | `POST /optimize/routes` |
| FR-12 | System provides 30/60/90-day predictions | Medium | Council output |
| FR-13 | Brand agent generates crisis comms drafts | Medium | Brand agent |
| FR-14 | All generated comms require human review | High | Brand agent |
| FR-15 | User can export debate trail as PDF/JSON | Medium | `GET /council/{id}/export/*` |
| FR-16 | Real-time debate streaming via WebSocket | Medium | `ws://*/ws/council` |
| FR-17 | LLM provider fallback on failure | High | LLM Router |
| FR-18 | Redis caching for RAG and MCP results | Medium | Cache layer |
| FR-19 | Full audit trail stored in Neon PostgreSQL | High | Audit tables |
| FR-20 | LangSmith tracing for all agent runs | Medium | LangSmith SDK |

### 9.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Council query end-to-end latency | < 8 seconds |
| NFR-02 | Single agent response latency | < 2 seconds |
| NFR-03 | RAG query (cached) | < 500ms |
| NFR-04 | RAG query (uncached) | < 5 seconds |
| NFR-05 | WebSocket message latency | < 100ms |
| NFR-06 | Frontend first paint | < 1.5 seconds |
| NFR-07 | System availability | 99% (best effort) |
| NFR-08 | Concurrent users supported | 10 (hackathon demo) |
| NFR-09 | Total operating cost | $0 (free tier only) |
| NFR-10 | API authentication | API key required |
| NFR-11 | CORS restricted to whitelisted origins | Configured |
| NFR-12 | Rate limiting per endpoint | As per route table |
| NFR-13 | Prompt injection protection | LlamaGuard + sanitization |
| NFR-14 | PII redaction in Brand Agent outputs | Enabled |
| NFR-15 | MCP sandboxing with least-privilege | Enabled |

### 9.3 Technical Requirements

| ID | Requirement | Implementation |
|----|-------------|---------------|
| TR-01 | Python 3.12 backend | FastAPI + LangGraph |
| TR-02 | React 18 + TypeScript frontend | Vite + Tailwind + shadcn/ui |
| TR-03 | Neon PostgreSQL for state | Cloud serverless DB |
| TR-04 | Redis for caching | Docker local or Upstash |
| TR-05 | Neo4j for supplier graph | Docker community or AuraDB |
| TR-06 | ChromaDB + Pinecone for RAG | Local + cloud vector stores |
| TR-07 | All LLM calls use free models | Groq + OpenRouter + NVIDIA + Google |
| TR-08 | Docker Compose for local dev | Multi-container setup |
| TR-09 | LangSmith for observability | Free tier tracing |
| TR-10 | WebSocket for real-time updates | FastAPI + Socket.io |

---

## 10. Request/Response Schemas

### 10.1 Council Analyze

```python
# POST /council/analyze

class CouncilAnalyzeRequest(BaseModel):
    query: str
    context: Optional[dict] = None  # {supplier_id, component_id, region}
    max_rounds: int = 3
    human_in_loop: bool = False

class CouncilAnalyzeResponse(BaseModel):
    session_id: str
    status: str  # "processing" | "complete" | "error"
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    agent_outputs: Optional[list[AgentOutput]] = None
    evidence: Optional[list[Evidence]] = None
    fallback_options: Optional[list[Action]] = None
    debate_summary: Optional[dict] = None
    total_latency_ms: Optional[int] = None
    models_used: Optional[list[str]] = None
```

### 10.2 RAG Ask

```python
# POST /rag/ask

class RAGAskRequest(BaseModel):
    question: str
    context: Optional[dict] = None
    use_quality_model: bool = False
    rerank: bool = True

class RAGAskResponse(BaseModel):
    answer: str
    citations: list[dict]
    graph_context: Optional[dict] = None
    confidence: float
    model_used: str
    cached: bool
```

### 10.3 Optimize Routes

```python
# POST /optimize/routes

class OptimizeRoutesRequest(BaseModel):
    origin: str
    destination: str
    constraints: Optional[dict] = None  # {lead_time_max, budget_max, ...}

class OptimizeRoutesResponse(BaseModel):
    routes: list[dict]
    recommended: Optional[dict] = None
    optimization_constraints: dict
```

---

## 11. Complete Route Summary

| Layer | Routes | Count |
|-------|--------|-------|
| Frontend Pages | `/`, `/chat`, `/debate`, `/brand` | 4 |
| Backend REST API | `/health`, `/council/*`, `/risk/*`, `/ingest/*`, `/optimize/*`, `/rag/*`, `/mcp/*`, `/models/*`, `/settings/*` | 35 |
| WebSocket | `/ws/council`, `/ws/agents`, `/ws/risk` | 3 |
| MCP Tools | 18 tools across 6 agents + 1 shared | 19 |
| LLM Providers | Groq, OpenRouter, NVIDIA, Google, Cohere, SambaNova | 6 |
| External APIs | NewsAPI, GDELT, HuggingFace, Unstructured, Pinecone, Neon, Neo4j, Redis, LangSmith | 9 |
| **Total** | | **76** |
