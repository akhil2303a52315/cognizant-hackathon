# SupplyChainGPT — Frontend Specification

Complete frontend implementation specification: architecture, project structure, setup, dependencies, all pages, components, hooks, state management, WebSocket integration, styling, testing, and deployment.

---

## 1. Frontend Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND ARCHITECTURE (React SPA)                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         REACT 18 + VITE                             │ │
│  │                                                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │
│  │  │ Dashboard │  │  Chat    │  │  Debate  │  │  Brand   │         │ │
│  │  │  Page     │  │  Page    │  │  Page    │  │  Page    │         │ │
│  │  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘         │ │
│  │        │              │              │              │               │ │
│  │  ┌─────▼──────────────▼──────────────▼──────────────▼─────┐       │ │
│  │  │                   SHARED COMPONENTS                     │       │ │
│  │  │  Navbar | AgentCard | DebateTimeline | Modals | Toast   │       │ │
│  │  └────────────────────────┬───────────────────────────────┘       │ │
│  │                           │                                        │ │
│  │  ┌────────────────────────▼───────────────────────────────┐       │ │
│  │  │                   STATE & DATA LAYER                     │       │ │
│  │  │                                                          │       │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │       │ │
│  │  │  │ Zustand  │  │ TanStack │  │ WebSocket Hook   │     │       │ │
│  │  │  │ Stores   │  │ Query    │  │ (Socket.io)      │     │       │ │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘     │       │ │
│  │  └────────────────────────────────────────────────────────┘       │ │
│  │                           │                                        │ │
│  │  ┌────────────────────────▼───────────────────────────────┐       │ │
│  │  │                   API & WS CLIENT                        │       │ │
│  │  │  lib/api.ts (REST)  |  lib/socket.ts (WebSocket)       │       │ │
│  │  └────────────────────────────────────────────────────────┘       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                          │                               │
│                          ┌───────────────┼───────────────┐              │
│                          │               │               │              │
│                    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐     │
│                    │ FastAPI    │  │ WebSocket │  │ Static    │     │
│                    │ REST API   │  │ Server    │  │ Assets    │     │
│                    │ :8000      │  │ :8000/ws  │  │ (Vite)    │     │
│                    └───────────┘  └───────────┘  └───────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
frontend/
├── public/
│   ├── favicon.svg
│   └── apple-touch-icon.png
│
├── src/
│   ├── App.tsx                        # Root app with router
│   ├── main.tsx                       # Vite entry point
│   ├── index.css                      # Global styles + Tailwind
│   ├── vite-env.d.ts                  # Vite type declarations
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx              # / — Risk heatmap, stats, quick query
│   │   ├── Chat.tsx                   # /chat — Council conversation UI
│   │   ├── Debate.tsx                 # /debate — Debate timeline + predictions
│   │   ├── Brand.tsx                  # /brand — Brand control room
│   │   └── NotFound.tsx              # 404 page
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx             # Global fixed navbar
│   │   │   ├── Sidebar.tsx            # Chat history sidebar
│   │   │   └── PageWrapper.tsx        # Page transition wrapper
│   │   │
│   │   ├── dashboard/
│   │   │   ├── RiskScoreGauge.tsx     # Animated risk score 0-100
│   │   │   ├── StatCard.tsx           # Stat card (disruptions, savings, queries)
│   │   │   ├── RiskHeatmap.tsx        # World map with supplier nodes
│   │   │   ├── QuickQuery.tsx         # Quick query input + buttons
│   │   │   ├── RecentQueries.tsx      # Recent council queries table
│   │   │   ├── RAGUploadWidget.tsx    # Document upload widget
│   │   │   └── LLMStatusPanel.tsx     # Provider availability panel
│   │   │
│   │   ├── chat/
│   │   │   ├── CouncilMessage.tsx     # Single council message bubble
│   │   │   ├── AgentStatusPanel.tsx   # Live agent confidence bars
│   │   │   ├── QueryInput.tsx         # Chat input with options
│   │   │   ├── RecommendationCard.tsx # Final recommendation display
│   │   │   └── SavedScenarios.tsx     # Saved scenario cards
│   │   │
│   │   ├── debate/
│   │   │   ├── DebateTimeline.tsx     # Round 1 → 2 → 3 timeline
│   │   │   ├── AgentCard.tsx          # Agent role + confidence card
│   │   │   ├── PredictionChart.tsx    # Prophet/LSTM forecast chart
│   │   │   ├── MonteCarloChart.tsx    # Monte Carlo scenario chart
│   │   │   ├── BrandSentimentWidget.tsx # Real-time sentiment score
│   │   │   └── ReasoningModal.tsx     # View full agent reasoning
│   │   │
│   │   ├── brand/
│   │   │   ├── SentimentChart.tsx     # Sentiment trend chart
│   │   │   ├── CrisisCommsEditor.tsx  # Editable comms drafts
│   │   │   ├── CompetitorPanel.tsx    # Competitor ad intelligence
│   │   │   ├── AdPivotRecommendations.tsx # Ad pivot suggestions
│   │   │   ├── CrisisScenarioSelector.tsx # Scenario A/B/C/D
│   │   │   └── QuickActions.tsx       # Launch/Pause/Notify buttons
│   │   │
│   │   ├── modals/
│   │   │   ├── ModalFallbacks.tsx     # Tier 1-3 fallback options
│   │   │   ├── ModalAudit.tsx         # Audit & observability log
│   │   │   ├── ModalSettings.tsx      # Settings + MCP + RAG config
│   │   │   └── ModalReasoning.tsx     # Agent reasoning detail
│   │   │
│   │   └── shared/
│   │       ├── LoadingSkeleton.tsx    # Skeleton loading states
│   │       ├── ConfidenceBar.tsx      # Animated confidence bar
│   │       ├── EvidenceTag.tsx        # Evidence reference tag
│   │       ├── StatusBadge.tsx        # Status indicator badge
│   │       ├── Toast.tsx              # shadcn Toast notifications
│   │       └── ThemeToggle.tsx        # Dark/Light mode toggle
│   │
│   ├── hooks/
│   │   ├── useCouncilQuery.ts         # TanStack Query for council API
│   │   ├── useWebSocket.ts            # WebSocket connection hook
│   │   ├── useRAGQuery.ts             # TanStack Query for RAG API
│   │   ├── useModelsStatus.ts         # LLM provider status hook
│   │   ├── useTheme.ts               # Dark/Light theme hook
│   │   └── useDebounce.ts            # Debounce input hook
│   │
│   ├── store/
│   │   ├── councilStore.ts            # Council session state
│   │   ├── agentStore.ts             # Agent status state
│   │   ├── ragStore.ts              # RAG pipeline state
│   │   ├── settingsStore.ts          # Settings state
│   │   └── navigationStore.ts        # Navigation state
│   │
│   ├── lib/
│   │   ├── api.ts                     # Axios/fetch API client
│   │   ├── socket.ts                  # Socket.io WebSocket client
│   │   ├── utils.ts                   # Utility functions
│   │   └── constants.ts              # App constants
│   │
│   ├── types/
│   │   ├── council.ts                 # Council state types
│   │   ├── agent.ts                   # Agent types
│   │   ├── rag.ts                     # RAG types
│   │   ├── mcp.ts                     # MCP types
│   │   └── api.ts                     # API request/response types
│   │
│   └── assets/
│       ├── agent-avatars/             # Agent avatar SVGs
│       │   ├── risk.svg
│       │   ├── supply.svg
│       │   ├── logistics.svg
│       │   ├── market.svg
│       │   ├── finance.svg
│       │   ├── brand.svg
│       │   └── moderator.svg
│       └── logo.svg
│
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── components.json                     # shadcn/ui config
├── .env.example
└── Dockerfile
```

---

## 3. Setup & Configuration

### 3.1 package.json

```json
{
  "name": "supplychaingpt-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",

    "@tanstack/react-query": "^5.62.0",

    "zustand": "^5.0.0",

    "socket.io-client": "^4.8.0",

    "recharts": "^2.15.0",

    "framer-motion": "^11.15.0",

    "lucide-react": "^0.468.0",

    "date-fns": "^4.1.0",

    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",

    "@radix-ui/react-dialog": "^1.1.4",
    "@radix-ui/react-dropdown-menu": "^2.1.4",
    "@radix-ui/react-select": "^2.1.4",
    "@radix-ui/react-switch": "^1.1.2",
    "@radix-ui/react-tabs": "^1.1.2",
    "@radix-ui/react-toast": "^1.2.4",
    "@radix-ui/react-tooltip": "^1.1.6",
    "@radix-ui/react-slider": "^1.2.1",
    "@radix-ui/react-progress": "^1.1.1",
    "@radix-ui/react-separator": "^1.1.1",

    "class-variance-authority": "^0.7.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.6.0",
    "vite": "^6.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.16.0",
    "@eslint/js": "^9.16.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "eslint-plugin-react-refresh": "^0.4.16",
    "vitest": "^2.1.0",
    "@playwright/test": "^1.49.0",
    "globals": "^15.13.0"
  }
}
```

### 3.2 vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
```

### 3.3 tailwind.config.ts

```typescript
import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // SupplyChainGPT brand colors
        brand: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#bac8ff",
          300: "#91a7ff",
          400: "#748ffc",
          500: "#5c7cfa",
          600: "#4c6ef5",
          700: "#4263eb",
          800: "#3b5bdb",
          900: "#364fc7",
        },
        risk: {
          low: "#40c057",
          medium: "#fab005",
          high: "#fd7e14",
          critical: "#fa5252",
        },
        surface: {
          base: "var(--surface-base)",
          l1: "var(--surface-l1)",
          l2: "var(--surface-l2)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "confidence-fill": "confidenceFill 1s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        confidenceFill: {
          "0%": { width: "0%" },
          "100%": { width: "var(--confidence-width)" },
        },
      },
    },
  },
  plugins: [tailwindcssAnimate],
};

export default config;
```

### 3.4 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

### 3.5 .env.example

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/council
VITE_API_KEY=dev-key
```

---

## 4. Type Definitions

```typescript
// src/types/council.ts

export interface CouncilSession {
  session_id: string;
  status: "pending" | "processing" | "complete" | "error";
  query: string;
  recommendation?: string;
  confidence?: number;
  risk_score?: number;
  round_number?: number;
  agent_outputs?: AgentOutput[];
  evidence?: Evidence[];
  fallback_options?: FallbackAction[];
  total_latency_ms?: number;
}

export interface AgentOutput {
  agent: AgentName;
  confidence: number;
  contribution: string;
  key_points: string[];
  model_used: string;
  provider: string;
}

export type AgentName = "risk" | "supply" | "logistics" | "market" | "finance" | "brand" | "moderator";

export interface Evidence {
  type: string;
  id: string;
  tag?: string;
  lane?: string;
  days?: number;
}

export interface FallbackAction {
  type: string;
  details: string;
  cost_estimate?: number;
  time_to_implement?: string;
  risk_score?: number;
}

export interface DebateEntry {
  round_number: number;
  challenger: string;
  challenged: string;
  challenge_text: string;
  response_text?: string;
}

export interface CouncilAnalyzeRequest {
  query: string;
  context?: Record<string, string>;
  max_rounds?: number;
  human_in_loop?: boolean;
}
```

```typescript
// src/types/agent.ts

export interface AgentStatus {
  agent: AgentName;
  status: "idle" | "thinking" | "done" | "error";
  confidence?: number;
  model_used?: string;
  provider?: string;
}

export const AGENT_CONFIG: Record<AgentName, { label: string; icon: string; color: string; emoji: string }> = {
  risk:      { label: "Risk Sentinel",     icon: "shield-alert",   color: "text-red-500",    emoji: "⚠️" },
  supply:    { label: "Supply Optimizer",   icon: "package",        color: "text-blue-500",   emoji: "📦" },
  logistics: { label: "Logistics Navigator",icon: "truck",          color: "text-green-500",  emoji: "🚛" },
  market:    { label: "Market Intelligence",icon: "trending-up",   color: "text-purple-500", emoji: "📈" },
  finance:   { label: "Finance Guardian",   icon: "dollar-sign",   color: "text-yellow-500", emoji: "💰" },
  brand:     { label: "Brand Protector",    icon: "shield-check",  color: "text-pink-500",   emoji: "🏷️" },
  moderator: { label: "Moderator",          icon: "gavel",          color: "text-brand-500",  emoji: "🎯" },
};
```

```typescript
// src/types/rag.ts

export interface RAGQuery {
  question: string;
  context?: Record<string, string>;
  use_quality_model?: boolean;
  rerank?: boolean;
}

export interface RAGResponse {
  answer: string;
  citations: Citation[];
  graph_context?: Record<string, unknown>;
  confidence: number;
  model_used: string;
  cached: boolean;
}

export interface Citation {
  id: string;
  source: string;
  page: string | number;
  relevance_score?: number;
}

export interface RAGStats {
  total_chunks: number;
  embedding_model: string;
  vector_store: string;
  reranker: string;
}
```

---

## 5. API Client

```typescript
// src/lib/api.ts

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-key";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
  },
  timeout: 30000,
});

// Council
export const councilApi = {
  analyze: (data: CouncilAnalyzeRequest) =>
    api.post<CouncilSession>("/council/analyze", data),
  getStatus: (sessionId: string) =>
    api.get(`/council/${sessionId}/status`),
  getResult: (sessionId: string) =>
    api.get<CouncilSession>(`/council/${sessionId}/result`),
  getAudit: (sessionId: string) =>
    api.get(`/council/${sessionId}/audit`),
  exportJson: (sessionId: string) =>
    api.get(`/council/${sessionId}/export/json`),
  exportPdf: (sessionId: string) =>
    api.get(`/council/${sessionId}/export/pdf`, { responseType: "blob" }),
  runSingleAgent: (agent: string, data: CouncilAnalyzeRequest) =>
    api.post<CouncilSession>(`/council/agent/${agent}`, data),
};

// Risk
export const riskApi = {
  getSupplier: (supplierId: string) =>
    api.get(`/risk/suppliers/${supplierId}`),
  listSuppliers: () =>
    api.get("/risk/suppliers"),
};

// RAG
export const ragApi = {
  ask: (data: RAGQuery) =>
    api.post<RAGResponse>("/rag/ask", data),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/rag/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  search: (query: string, k = 5) =>
    api.get("/rag/search", { params: { query, k } }),
  getStats: () =>
    api.get<RAGStats>("/rag/stats"),
};

// Optimize
export const optimizeApi = {
  routes: (data: { origin: string; destination: string; constraints?: Record<string, unknown> }) =>
    api.post("/optimize/routes", data),
  allocation: (data: Record<string, unknown>) =>
    api.post("/optimize/allocation", data),
};

// Models
export const modelsApi = {
  getStatus: () =>
    api.get("/models/status"),
};

// Settings
export const settingsApi = {
  get: () =>
    api.get("/settings"),
  update: (data: Record<string, unknown>) =>
    api.put("/settings", data),
};

// Health
export const healthApi = {
  check: () => api.get("/health"),
  ready: () => api.get("/ready"),
};

export default api;
```

---

## 6. WebSocket Client

```typescript
// src/lib/socket.ts

import { io, Socket } from "socket.io-client";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/council";

class CouncilSocket {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();

  connect(): void {
    if (this.socket?.connected) return;

    this.socket = io(WS_URL, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 3000,
    });

    this.socket.on("connect", () => {
      console.log("✅ WebSocket connected");
    });

    this.socket.on("disconnect", () => {
      console.log("🛑 WebSocket disconnected");
    });

    this.socket.on("connect_error", (err) => {
      console.error("WebSocket error:", err.message);
    });

    // Forward all events to listeners
    const events = [
      "agent:status",
      "agent:contribution",
      "debate:round",
      "council:complete",
      "council:error",
      "risk:update",
      "models:status",
    ];

    events.forEach((event) => {
      this.socket?.on(event, (data: unknown) => {
        this.emit(event, data);
      });
    });
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }

  startCouncil(query: string, context?: Record<string, string>): void {
    this.socket?.emit("council:start", { query, context });
  }

  cancelCouncil(sessionId: string): void {
    this.socket?.emit("council:cancel", { session_id: sessionId });
  }

  on(event: string, callback: Function): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach((cb) => cb(data));
  }
}

export const councilSocket = new CouncilSocket();
```

---

## 7. State Management (Zustand)

### 7.1 Council Store

```typescript
// src/store/councilStore.ts

import { create } from "zustand";
import type { CouncilSession, AgentOutput, AgentStatus, DebateEntry } from "@/types/council";

interface CouncilStore {
  // Current session
  currentSession: CouncilSession | null;
  isProcessing: boolean;
  error: string | null;

  // Agent status
  agentStatuses: Record<string, AgentStatus>;

  // Debate
  debateHistory: DebateEntry[];
  currentRound: number;

  // History
  sessionHistory: CouncilSession[];

  // Actions
  setCurrentSession: (session: CouncilSession | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setError: (error: string | null) => void;
  addAgentStatus: (status: AgentStatus) => void;
  addAgentContribution: (output: AgentOutput) => void;
  setCouncilResult: (result: Partial<CouncilSession>) => void;
  addToHistory: (session: CouncilSession) => void;
  reset: () => void;
}

export const useCouncilStore = create<CouncilStore>((set) => ({
  currentSession: null,
  isProcessing: false,
  error: null,
  agentStatuses: {},
  debateHistory: [],
  currentRound: 0,
  sessionHistory: [],

  setCurrentSession: (session) => set({ currentSession: session }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setError: (error) => set({ error, isProcessing: false }),
  addAgentStatus: (status) =>
    set((state) => ({
      agentStatuses: { ...state.agentStatuses, [status.agent]: status },
    })),
  addAgentContribution: (output) =>
    set((state) => ({
      currentSession: state.currentSession
        ? {
            ...state.currentSession,
            agent_outputs: [...(state.currentSession.agent_outputs || []), output],
          }
        : null,
    })),
  setCouncilResult: (result) =>
    set((state) => ({
      currentSession: state.currentSession
        ? { ...state.currentSession, ...result }
        : null,
      isProcessing: false,
    })),
  addToHistory: (session) =>
    set((state) => ({
      sessionHistory: [session, ...state.sessionHistory],
    })),
  reset: () =>
    set({
      currentSession: null,
      isProcessing: false,
      error: null,
      agentStatuses: {},
      debateHistory: [],
      currentRound: 0,
    }),
}));
```

### 7.2 Settings Store

```typescript
// src/store/settingsStore.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SettingsStore {
  theme: "light" | "dark";
  ragSettings: {
    embeddingModel: string;
    vectorStore: string;
    topK: number;
    reranking: boolean;
    cacheTTL: number;
    strictGrounding: boolean;
  };
  mcpSettings: {
    sandboxEnabled: boolean;
    rateLimit: number;
  };
  setTheme: (theme: "light" | "dark") => void;
  updateRagSettings: (settings: Partial<SettingsStore["ragSettings"]>) => void;
  updateMcpSettings: (settings: Partial<SettingsStore["mcpSettings"]>) => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      theme: "dark",
      ragSettings: {
        embeddingModel: "nomic-embed-text-v1.5",
        vectorStore: "ChromaDB",
        topK: 5,
        reranking: true,
        cacheTTL: 3600,
        strictGrounding: true,
      },
      mcpSettings: {
        sandboxEnabled: true,
        rateLimit: 30,
      },
      setTheme: (theme) => {
        document.documentElement.classList.toggle("dark", theme === "dark");
        set({ theme });
      },
      updateRagSettings: (settings) =>
        set((state) => ({
          ragSettings: { ...state.ragSettings, ...settings },
        })),
      updateMcpSettings: (settings) =>
        set((state) => ({
          mcpSettings: { ...state.mcpSettings, ...settings },
        })),
    }),
    { name: "supplychaingpt-settings" }
  )
);
```

---

## 8. Custom Hooks

### 8.1 useCouncilQuery

```typescript
// src/hooks/useCouncilQuery.ts

import { useMutation, useQuery } from "@tanstack/react-query";
import { councilApi } from "@/lib/api";
import { useCouncilStore } from "@/store/councilStore";
import type { CouncilAnalyzeRequest } from "@/types/council";

export function useCouncilAnalyze() {
  const { setCurrentSession, setIsProcessing, setError, addToHistory } = useCouncilStore();

  return useMutation({
    mutationFn: async (request: CouncilAnalyzeRequest) => {
      setIsProcessing(true);
      setError(null);
      const { data } = await councilApi.analyze(request);
      return data;
    },
    onSuccess: (data) => {
      setCurrentSession(data);
      addToHistory(data);
      setIsProcessing(false);
    },
    onError: (error) => {
      setError(error.message);
    },
  });
}

export function useCouncilStatus(sessionId: string | null) {
  return useQuery({
    queryKey: ["council", sessionId, "status"],
    queryFn: async () => {
      if (!sessionId) return null;
      const { data } = await councilApi.getStatus(sessionId);
      return data;
    },
    enabled: !!sessionId,
    refetchInterval: (query) => {
      if (query.state.data?.status === "complete" || query.state.data?.status === "error") {
        return false;
      }
      return 1000; // Poll every second while processing
    },
  });
}

export function useCouncilAudit(sessionId: string | null) {
  return useQuery({
    queryKey: ["council", sessionId, "audit"],
    queryFn: async () => {
      if (!sessionId) return null;
      const { data } = await councilApi.getAudit(sessionId);
      return data;
    },
    enabled: !!sessionId,
  });
}
```

### 8.2 useWebSocket

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from "react";
import { councilSocket } from "@/lib/socket";
import { useCouncilStore } from "@/store/councilStore";

export function useWebSocket() {
  const { addAgentStatus, addAgentContribution, setCouncilResult, setError } = useCouncilStore();
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    councilSocket.connect();

    const unsubStatus = councilSocket.on("agent:status", (data: any) => {
      addAgentStatus(data);
    });

    const unsubContribution = councilSocket.on("agent:contribution", (data: any) => {
      addAgentContribution(data);
    });

    const unsubComplete = councilSocket.on("council:complete", (data: any) => {
      setCouncilResult(data);
    });

    const unsubError = councilSocket.on("council:error", (data: any) => {
      setError(data.message || "Council error");
    });

    return () => {
      unsubStatus();
      unsubContribution();
      unsubComplete();
      unsubError();
    };
  }, []);

  const startCouncil = useCallback((query: string, context?: Record<string, string>) => {
    useCouncilStore.getState().reset();
    useCouncilStore.getState().setIsProcessing(true);
    councilSocket.startCouncil(query, context);
  }, []);

  const cancelCouncil = useCallback((sessionId: string) => {
    councilSocket.cancelCouncil(sessionId);
  }, []);

  return { startCouncil, cancelCouncil };
}
```

### 8.3 useRAGQuery

```typescript
// src/hooks/useRAGQuery.ts

import { useMutation } from "@tanstack/react-query";
import { ragApi } from "@/lib/api";
import type { RAGQuery, RAGResponse } from "@/types/rag";

export function useRAGAsk() {
  return useMutation<RAGResponse, Error, RAGQuery>({
    mutationFn: async (query) => {
      const { data } = await ragApi.ask(query);
      return data;
    },
  });
}

export function useRAGUpload() {
  return useMutation({
    mutationFn: async (file: File) => {
      const { data } = await ragApi.upload(file);
      return data;
    },
  });
}
```

---

## 9. Page Implementations

### 9.1 App.tsx (Root)

```tsx
// src/App.tsx

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/shared/Toast";
import { Navbar } from "@/components/layout/Navbar";
import { Dashboard } from "@/pages/Dashboard";
import { Chat } from "@/pages/Chat";
import { Debate } from "@/pages/Debate";
import { Brand } from "@/pages/Brand";
import { NotFound } from "@/pages/NotFound";
import { useWebSocket } from "@/hooks/useWebSocket";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 2 },
  },
});

export default function App() {
  useWebSocket(); // Initialize WebSocket connection

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-surface-base text-fg-primary">
          <Navbar />
          <main className="pt-16">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/debate" element={<Debate />} />
              <Route path="/brand" element={<Brand />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Toaster />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

### 9.2 Dashboard Page

```tsx
// src/pages/Dashboard.tsx

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { RiskScoreGauge } from "@/components/dashboard/RiskScoreGauge";
import { StatCard } from "@/components/dashboard/StatCard";
import { RiskHeatmap } from "@/components/dashboard/RiskHeatmap";
import { QuickQuery } from "@/components/dashboard/QuickQuery";
import { RecentQueries } from "@/components/dashboard/RecentQueries";
import { RAGUploadWidget } from "@/components/dashboard/RAGUploadWidget";
import { LLMStatusPanel } from "@/components/dashboard/LLMStatusPanel";
import { useCouncilAnalyze } from "@/hooks/useCouncilQuery";
import { ShieldAlert, Activity, DollarSign, MessageSquare } from "lucide-react";

export function Dashboard() {
  const navigate = useNavigate();
  const councilAnalyze = useCouncilAnalyze();
  const [quickQuery, setQuickQuery] = useState("");

  const handleQuickQuery = async (query: string) => {
    const result = await councilAnalyze.mutateAsync({ query });
    if (result.session_id) {
      navigate(`/chat?session=${result.session_id}`);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
          <RiskScoreGauge score={72} level="High" />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <StatCard title="Active Disruptions" value={3} icon={Activity} trend="up" color="text-red-500" />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <StatCard title="Predicted Savings" value="$2.4M" icon={DollarSign} trend="up" color="text-green-500" />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <StatCard title="Council Queries" value={47} icon={MessageSquare} trend="stable" color="text-brand-500" />
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Heatmap */}
        <div className="lg:col-span-2">
          <RiskHeatmap />
        </div>

        {/* Right Sidebar */}
        <div className="space-y-4">
          <RAGUploadWidget />
          <LLMStatusPanel />
        </div>
      </div>

      {/* Quick Query */}
      <QuickQuery
        value={quickQuery}
        onChange={setQuickQuery}
        onSubmit={() => handleQuickQuery(quickQuery)}
        isLoading={councilAnalyze.isPending}
      />

      {/* Recent Queries */}
      <RecentQueries />
    </div>
  );
}
```

### 9.3 Chat Page

```tsx
// src/pages/Chat.tsx

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useCouncilStore } from "@/store/councilStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useCouncilStatus } from "@/hooks/useCouncilQuery";
import { Sidebar } from "@/components/layout/Sidebar";
import { CouncilMessage } from "@/components/chat/CouncilMessage";
import { AgentStatusPanel } from "@/components/chat/AgentStatusPanel";
import { QueryInput } from "@/components/chat/QueryInput";
import { RecommendationCard } from "@/components/chat/RecommendationCard";
import type { AgentName } from "@/types/council";

export function Chat() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session");
  const { startCouncil } = useWebSocket();
  const { currentSession, isProcessing, agentStatuses } = useCouncilStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Poll for status if we have a session ID
  useCouncilStatus(sessionId);

  const handleSubmit = (query: string) => {
    startCouncil(query);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentSession?.agent_outputs]);

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {currentSession?.agent_outputs?.map((output, i) => (
              <motion.div
                key={`${output.agent}-${i}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <CouncilMessage output={output} />
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Final Recommendation */}
          {currentSession?.recommendation && (
            <RecommendationCard
              recommendation={currentSession.recommendation}
              confidence={currentSession.confidence || 0}
              sessionId={currentSession.session_id}
            />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <QueryInput onSubmit={handleSubmit} isLoading={isProcessing} />

        {/* Agent Status Panel (collapsible) */}
        <AgentStatusPanel statuses={agentStatuses} />
      </div>
    </div>
  );
}
```

### 9.4 Debate Page

```tsx
// src/pages/Debate.tsx

import { useCouncilStore } from "@/store/councilStore";
import { DebateTimeline } from "@/components/debate/DebateTimeline";
import { AgentCard } from "@/components/debate/AgentCard";
import { PredictionChart } from "@/components/debate/PredictionChart";
import { MonteCarloChart } from "@/components/debate/MonteCarloChart";
import { BrandSentimentWidget } from "@/components/debate/BrandSentimentWidget";
import { AGENT_CONFIG } from "@/types/agent";
import type { AgentName } from "@/types/council";

export function Debate() {
  const { currentSession } = useCouncilStore();

  const agents: AgentName[] = ["risk", "supply", "logistics", "market", "finance", "brand"];

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {currentSession?.query || "No active debate"}
          </h1>
          <p className="text-muted-foreground">
            Overall Confidence: {currentSession?.confidence?.toFixed(0) || "—"}%
          </p>
        </div>
      </div>

      {/* Debate Timeline */}
      <DebateTimeline
        rounds={currentSession?.round_number || 0}
        currentRound={currentSession?.round_number || 0}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Cards */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Agent Analysis</h2>
          {agents.map((agent) => {
            const output = currentSession?.agent_outputs?.find((o) => o.agent === agent);
            const config = AGENT_CONFIG[agent];
            return (
              <AgentCard
                key={agent}
                agent={agent}
                label={config.label}
                emoji={config.emoji}
                confidence={output?.confidence || 0}
                contribution={output?.contribution || ""}
                modelUsed={output?.model_used || ""}
              />
            );
          })}
        </div>

        {/* Charts */}
        <div className="space-y-4">
          <PredictionChart />
          <MonteCarloChart />
          <BrandSentimentWidget score={62} trend="declining" />
        </div>
      </div>
    </div>
  );
}
```

### 9.5 Brand Page

```tsx
// src/pages/Brand.tsx

import { useState } from "react";
import { SentimentChart } from "@/components/brand/SentimentChart";
import { CrisisCommsEditor } from "@/components/brand/CrisisCommsEditor";
import { CompetitorPanel } from "@/components/brand/CompetitorPanel";
import { AdPivotRecommendations } from "@/components/brand/AdPivotRecommendations";
import { CrisisScenarioSelector } from "@/components/brand/CrisisScenarioSelector";
import { QuickActions } from "@/components/brand/QuickActions";

type CrisisScenario = "shortage" | "price_increase" | "competitor_exploiting" | "sustainability";

export function Brand() {
  const [activeScenario, setActiveScenario] = useState<CrisisScenario>("shortage");

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-4">
          <SentimentChart score={62} trend="declining" />
          <CompetitorPanel competitor="CompetitorX" />
          <QuickActions />
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          <CrisisCommsEditor scenario={activeScenario} />
          <AdPivotRecommendations scenario={activeScenario} />
          <CrisisScenarioSelector
            active={activeScenario}
            onChange={setActiveScenario}
          />
        </div>
      </div>
    </div>
  );
}
```

---

## 10. Key Component Implementations

### 10.1 Navbar

```tsx
// src/components/layout/Navbar.tsx

import { Link, useLocation } from "react-router-dom";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { Home, MessageSquare, GitBranch, Shield, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: Home },
  { path: "/chat", label: "Council Chat", icon: MessageSquare },
  { path: "/debate", label: "Debate", icon: GitBranch },
  { path: "/brand", label: "Brand", icon: Shield },
];

export function Navbar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 border-b bg-surface-l1/80 backdrop-blur-md">
      <div className="container mx-auto h-full flex items-center justify-between px-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="text-brand-500">SupplyChain</span>GPT
        </Link>

        {/* Nav Items */}
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                location.pathname === path
                  ? "bg-brand-500/10 text-brand-500"
                  : "text-muted-foreground hover:text-foreground hover:bg-surface-l2"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden md:inline">{label}</span>
            </Link>
          ))}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
```

### 10.2 AgentCard

```tsx
// src/components/debate/AgentCard.tsx

import { motion } from "framer-motion";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { AGENT_CONFIG } from "@/types/agent";
import type { AgentName } from "@/types/council";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface AgentCardProps {
  agent: AgentName;
  label: string;
  emoji: string;
  confidence: number;
  contribution: string;
  modelUsed: string;
}

export function AgentCard({ agent, label, emoji, confidence, contribution, modelUsed }: AgentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = AGENT_CONFIG[agent];

  return (
    <motion.div
      layout
      className="rounded-xl border bg-surface-l1 p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{emoji}</span>
          <div>
            <h3 className="font-semibold">{label}</h3>
            <p className="text-xs text-muted-foreground">{modelUsed}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceBar value={confidence} />
          <button onClick={() => setExpanded(!expanded)} className="p-1 hover:bg-surface-l2 rounded">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          className="text-sm text-muted-foreground border-t pt-3"
        >
          {contribution}
        </motion.div>
      )}
    </motion.div>
  );
}
```

### 10.3 ConfidenceBar

```tsx
// src/components/shared/ConfidenceBar.tsx

interface ConfidenceBarProps {
  value: number; // 0-100
  className?: string;
}

export function ConfidenceBar({ value, className = "" }: ConfidenceBarProps) {
  const color =
    value >= 80 ? "bg-green-500" :
    value >= 60 ? "bg-yellow-500" :
    value >= 40 ? "bg-orange-500" : "bg-red-500";

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="w-24 h-2 bg-surface-l2 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-1000`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs font-mono text-muted-foreground">{value.toFixed(0)}%</span>
    </div>
  );
}
```

### 10.4 RiskScoreGauge

```tsx
// src/components/dashboard/RiskScoreGauge.tsx

import { motion } from "framer-motion";

interface RiskScoreGaugeProps {
  score: number;
  level: string;
}

export function RiskScoreGauge({ score, level }: RiskScoreGaugeProps) {
  const color =
    level === "Critical" ? "text-red-600" :
    level === "High" ? "text-orange-500" :
    level === "Medium" ? "text-yellow-500" : "text-green-500";

  const strokeColor =
    level === "Critical" ? "#dc2626" :
    level === "High" ? "#f97316" :
    level === "Medium" ? "#eab308" : "#22c55e";

  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="rounded-xl border bg-surface-l1 p-6 flex flex-col items-center">
      <svg width="120" height="120" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-surface-l2" />
        <motion.circle
          cx="50" cy="50" r="40" fill="none"
          stroke={strokeColor} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="45" textAnchor="middle" className={`text-2xl font-bold ${color}`}>
          {score}
        </text>
        <text x="50" y="60" textAnchor="middle" className="text-xs fill-muted-foreground">
          /100
        </text>
      </svg>
      <div className="mt-2 text-center">
        <p className="text-sm text-muted-foreground">Risk Score</p>
        <p className={`font-semibold ${color}`}>{level}</p>
      </div>
    </div>
  );
}
```

---

## 11. Styling

### 11.1 Global CSS

```css
/* src/index.css */

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --surface-base: 0 0% 100%;
    --surface-l1: 0 0% 98%;
    --surface-l2: 0 0% 96%;
    --fg-primary: 0 0% 9%;
    --fg-muted: 0 0% 45%;
  }

  .dark {
    --surface-base: 0 0% 5%;
    --surface-l1: 0 0% 9%;
    --surface-l2: 0 0% 13%;
    --fg-primary: 0 0% 98%;
    --fg-muted: 0 0% 63%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-surface-base text-fg-primary;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  @apply bg-surface-l2 rounded-full;
}

/* Animations */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(90deg, var(--surface-l1) 25%, var(--surface-l2) 50%, var(--surface-l1) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

---

## 12. Dockerfile

```dockerfile
# frontend/Dockerfile

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing — all paths → index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://api:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static assets cache
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 13. Testing

### 13.1 Unit Tests (Vitest)

```typescript
// src/components/shared/__tests__/ConfidenceBar.test.tsx

import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ConfidenceBar } from "../ConfidenceBar";

describe("ConfidenceBar", () => {
  it("renders with correct percentage", () => {
    const { container } = render(<ConfidenceBar value={87} />);
    expect(container.textContent).toContain("87%");
  });

  it("applies green color for high confidence", () => {
    const { container } = render(<ConfidenceBar value={90} />);
    const bar = container.querySelector(".bg-green-500");
    expect(bar).toBeTruthy();
  });

  it("applies red color for low confidence", () => {
    const { container } = render(<ConfidenceBar value={20} />);
    const bar = container.querySelector(".bg-red-500");
    expect(bar).toBeTruthy();
  });
});
```

### 13.2 E2E Tests (Playwright)

```typescript
// e2e/app.spec.ts

import { test, expect } from "@playwright/test";

test("Dashboard loads with stat cards", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("text=Risk Score")).toBeVisible();
  await expect(page.locator("text=Active Disruptions")).toBeVisible();
});

test("Navigate to Chat page", async ({ page }) => {
  await page.goto("/");
  await page.click("text=Council Chat");
  await expect(page).toHaveURL("/chat");
});

test("Submit a council query", async ({ page }) => {
  await page.goto("/chat");
  await page.fill("[placeholder*='Ask the Council']", "What if Supplier S1 is delayed?");
  await page.click("text=Convene");
  // Should show agent status updates
  await expect(page.locator("text=Risk Sentinel")).toBeVisible({ timeout: 15000 });
});

test("Debate page shows timeline", async ({ page }) => {
  await page.goto("/debate");
  await expect(page.locator("text=Debate Timeline")).toBeVisible();
});

test("Brand page shows sentiment", async ({ page }) => {
  await page.goto("/brand");
  await expect(page.locator("text=Live Sentiment")).toBeVisible();
});
```

### 13.3 Run Tests

```bash
# Unit tests
npm run test

# E2E tests
npx playwright install
npm run test:e2e

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

---

## 14. Run Commands

```bash
# Install dependencies
cd frontend/
npm install

# Development server (with hot reload)
npm run dev
# → http://localhost:3000

# Production build
npm run build

# Preview production build
npm run preview

# Docker
docker compose up --build
```

---

## 15. Frontend Performance Targets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.2s |
| Largest Contentful Paint | < 2.0s |
| Time to Interactive | < 3.0s |
| Bundle size (gzipped) | < 300KB |
| Lighthouse Performance | > 90 |
| Lighthouse Accessibility | > 95 |

---

## 16. shadcn/ui Components Used

| Component | Usage |
|-----------|-------|
| `Button` | All action buttons |
| `Card` | Stat cards, agent cards |
| `Dialog` | Modals (Fallbacks, Audit, Settings, Reasoning) |
| `Input` | Query input, settings fields |
| `Textarea` | Comms editor |
| `Select` | Model selector, scenario selector |
| `Switch` | Toggle settings (sandbox, grounding, etc.) |
| `Slider` | Cache TTL, Top-K, temperature |
| `Tabs` | Settings modal tabs |
| `Toast` | Notifications |
| `Tooltip` | Agent info, evidence tags |
| `Progress` | Confidence bars |
| `Separator` | Section dividers |
| `Badge` | Status badges, risk levels |
| `DropdownMenu` | Agent selector, export options |
| `Sheet` | Mobile sidebar |
| `Skeleton` | Loading states |

---

## 17. Component Dependency Map

```
App.tsx
  ├── Navbar.tsx
  │   ├── ThemeToggle.tsx
  │   └── Nav links (react-router-dom)
  │
  ├── Dashboard.tsx
  │   ├── RiskScoreGauge.tsx
  │   ├── StatCard.tsx
  │   ├── RiskHeatmap.tsx
  │   ├── QuickQuery.tsx
  │   ├── RecentQueries.tsx
  │   ├── RAGUploadWidget.tsx ── ragApi
  │   └── LLMStatusPanel.tsx ── modelsApi
  │
  ├── Chat.tsx
  │   ├── Sidebar.tsx
  │   ├── CouncilMessage.tsx ── councilStore
  │   ├── AgentStatusPanel.tsx ── councilStore
  │   ├── QueryInput.tsx ── useWebSocket
  │   ├── RecommendationCard.tsx
  │   └── SavedScenarios.tsx
  │
  ├── Debate.tsx
  │   ├── DebateTimeline.tsx
  │   ├── AgentCard.tsx ── ConfidenceBar
  │   ├── PredictionChart.tsx ── Recharts
  │   ├── MonteCarloChart.tsx ── Recharts
  │   ├── BrandSentimentWidget.tsx
  │   └── ReasoningModal.tsx ── Dialog
  │
  ├── Brand.tsx
  │   ├── SentimentChart.tsx ── Recharts
  │   ├── CrisisCommsEditor.tsx ── Textarea
  │   ├── CompetitorPanel.tsx
  │   ├── AdPivotRecommendations.tsx
  │   ├── CrisisScenarioSelector.tsx ── Tabs
  │   └── QuickActions.tsx ── Button
  │
  └── Modals (shared across pages)
      ├── ModalFallbacks.tsx ── councilApi
      ├── ModalAudit.tsx ── councilApi
      ├── ModalSettings.tsx ── settingsStore
      └── ModalReasoning.tsx
```
