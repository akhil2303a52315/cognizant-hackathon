# SupplyChainGPT — Technical Specification

Complete technical specification for the Council of Debate AI Agents system.

---

## 1. System Overview

SupplyChainGPT is a multi-agent AI framework where 7 specialized agents debate, challenge, predict, and collectively decide the best course of action for supply chain queries and crises. The system is orchestrated by LangGraph, powered by multiple LLM providers, and exposes a FastAPI backend with a 4-page React SPA frontend.

---

## 2. AI Model Providers & Configuration

### 2.1 LLM Provider Stack

| Provider | Models | Use Case | API Base |
|----------|--------|----------|----------|
| **Groq** | Llama-3.3-70B-fast, Llama-3.1-8B-instant | Primary agent reasoning (low latency, high throughput) | `https://api.groq.com/openai/v1` |
| **Anthropic (via AWS Bedrock)** | Claude 3.5 Sonnet, Claude 3 Haiku | Complex reasoning, debate synthesis, fallback when Groq rate-limited | AWS Bedrock endpoint |
| **OpenRouter** | Multiple models via single API | Model diversity, fallback routing, cost optimization | `https://openrouter.ai/api/v1` |
| **NVIDIA NIM API** | Meta Llama 3.1 405B, Mistral Large, Mixtral 8x22B | High-accuracy agent analysis, GPU-accelerated inference | `https://integrate.api.nvidia.com/v1` |

### 2.2 OpenRouter Configuration

OpenRouter provides a unified API to access 100+ models with automatic fallback and cost optimization.

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
```

**Models available via OpenRouter for this project:**

| Model ID | Use Case | Context Window | Cost/1M tokens |
|----------|----------|----------------|----------------|
| `meta-llama/llama-3.3-70b-instruct` | General agent reasoning | 128K | $0.20 / $0.80 |
| `anthropic/claude-3.5-sonnet` | Debate synthesis, Moderator | 200K | $3.00 / $15.00 |
| `google/gemini-2.0-flash-001` | Fast agent responses | 1M | $0.10 / $0.40 |
| `deepseek/deepseek-r1` | Complex reasoning, Finance Agent | 128K | $0.55 / $2.19 |
| `qwen/qwen-2.5-72b-instruct` | Supply/Market agent analysis | 128K | $0.20 / $0.60 |

**OpenRouter request format:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Analyze supply chain risk for..."}],
    extra_headers={
        "HTTP-Referer": "https://supplychaingpt.ai",
        "X-Title": "SupplyChainGPT Council",
    },
)
```

**OpenRouter features used:**
- Automatic model fallback (if primary model is down, route to next cheapest)
- Cost tracking per request
- Provider routing preferences (cost vs latency vs quality)
- Streaming support for real-time debate

### 2.3 NVIDIA NIM API Configuration

NVIDIA NIM (NVIDIA Inference Microservices) provides GPU-accelerated inference for high-accuracy models.

```env
NVIDIA_API_KEY=nvapi-...
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
```

**Models available via NVIDIA NIM:**

| Model ID | Use Case | Context Window | Notes |
|----------|----------|----------------|-------|
| `meta/llama-3.1-405b-instruct` | High-stakes Risk Agent analysis | 128K | Largest Llama, highest accuracy |
| `mistralai/mistral-large` | Finance Agent complex calculations | 128K | Strong reasoning, multilingual |
| `mistralai/mixtral-8x22b-instruct` | Fast parallel agent processing | 64K | MoE architecture, efficient |
| `nvidia/nemotron-4-340b-instruct` | Moderator synthesis & debate | 4K | NVIDIA's flagship model |
| `google/gemma-2-27b-it` | Lightweight Brand Agent tasks | 8K | Fast, cost-effective |

**NVIDIA NIM request format:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
)

response = client.chat.completions.create(
    model="meta/llama-3.1-405b-instruct",
    messages=[{"role": "system", "content": "You are a Risk Sentinel Agent..."},
              {"role": "user", "content": "Assess geopolitical risk for..."}],
    temperature=0.3,
    top_p=0.9,
    max_tokens=2048,
    stream=True,
)
```

**NVIDIA NIM features used:**
- GPU-accelerated inference (sub-200ms latency for large models)
- Curated model selection optimized for enterprise use
- Streaming responses for real-time debate
- Function calling / tool use support

### 2.4 LLM Routing Strategy

```python
LLM_ROUTING = {
    # Agent → Primary Model → Fallback Chain
    "risk": {
        "primary": "nvidia:meta/llama-3.1-405b-instruct",     # Highest accuracy for risk
        "fallback": ["groq:llama-3.3-70b-fast", "openrouter:meta-llama/llama-3.3-70b-instruct"],
    },
    "supply": {
        "primary": "groq:llama-3.3-70b-fast",                  # Fast for supplier matching
        "fallback": ["openrouter:qwen/qwen-2.5-72b-instruct", "nvidia:mistralai/mixtral-8x22b-instruct"],
    },
    "logistics": {
        "primary": "groq:llama-3.3-70b-fast",                  # Fast route optimization
        "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct", "nvidia:mistralai/mixtral-8x22b-instruct"],
    },
    "market": {
        "primary": "openrouter:deepseek/deepseek-r1",           # Complex reasoning for forecasting
        "fallback": ["nvidia:mistralai/mistral-large", "groq:llama-3.3-70b-fast"],
    },
    "finance": {
        "primary": "nvidia:mistralai/mistral-large",            # Strong numerical reasoning
        "fallback": ["openrouter:deepseek/deepseek-r1", "anthropic:claude-3.5-sonnet"],
    },
    "brand": {
        "primary": "groq:llama-3.3-70b-fast",                  # Fast content generation
        "fallback": ["openrouter:google/gemini-2.0-flash-001", "nvidia:google/gemma-2-27b-it"],
    },
    "moderator": {
        "primary": "anthropic:claude-3.5-sonnet",              # Best synthesis quality
        "fallback": ["openrouter:anthropic/claude-3.5-sonnet", "nvidia:nvidia/nemotron-4-340b-instruct"],
    },
}
```

### 2.5 Cost Optimization via Multi-Provider

| Strategy | Implementation |
|----------|---------------|
| **Redis caching** | Cache RAG results + MCP responses (60%+ cost reduction) |
| **LLM fallback chain** | Groq (cheapest) → OpenRouter (mid) → NVIDIA/Anthropic (premium) only when needed |
| **Batch processing** | Group multiple agent calls when possible |
| **Model tiering** | Fast agents use Groq, complex agents use NVIDIA/Anthropic |
| **Token budgeting** | Max token limits per agent per query |
| **OpenRouter cost routing** | Set `provider.order` to prioritize cost-effective providers |

---

## 3. Backend Specification

### 3.1 Core Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.12 |
| Web Framework | FastAPI | 0.115+ |
| Agent Orchestration | LangGraph | 0.2+ |
| LLM Framework | LangChain | 0.3+ |
| Groq Integration | langchain-groq | latest |
| Anthropic Integration | langchain-anthropic (via Bedrock) | latest |
| OpenRouter Integration | langchain-openai (custom base_url) | latest |
| NVIDIA Integration | langchain-openai (custom base_url) | latest |
| Observability | LangSmith | latest |
| Package Manager | uv | latest |

### 3.2 Project Structure

```
backend/
├── agents/
│   ├── risk_agent.py
│   ├── supply_agent.py
│   ├── logistics_agent.py
│   ├── market_agent.py
│   ├── finance_agent.py
│   ├── brand_agent.py
│   ├── moderator.py
│   └── supervisor.py
├── rag/
│   ├── chunker.py
│   ├── embedder.py
│   ├── vectorstore.py
│   └── retriever.py
├── mcp/
│   ├── server.py
│   ├── tools/
│   │   ├── news_tools.py
│   │   ├── supplier_tools.py
│   │   ├── shipping_tools.py
│   │   ├── commodity_tools.py
│   │   ├── finance_tools.py
│   │   └── social_tools.py
│   └── sandbox.py
├── tools/
│   ├── or_tools_optimizer.py
│   ├── monte_carlo.py
│   └── forecasting.py
├── llm/
│   ├── router.py              # LLM routing logic (Groq/OpenRouter/NVIDIA/Anthropic)
│   ├── providers.py           # Provider-specific client wrappers
│   ├── fallback.py            # Fallback chain implementation
│   └── config.py              # Model configs, token limits, routing table
├── api.py
├── graph.py
├── state.py
├── config.py
└── main.py

frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Chat.tsx
│   │   ├── Debate.tsx
│   │   └── Brand.tsx
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── AgentCard.tsx
│   │   ├── DebateTimeline.tsx
│   │   ├── ModalFallbacks.tsx
│   │   ├── ModalAudit.tsx
│   │   └── ModalSettings.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── socket.ts
│   ├── store/
│   │   └── councilStore.ts
│   ├── hooks/
│   │   ├── useCouncilQuery.ts
│   │   └── useWebSocket.ts
│   ├── assets/
│   └── App.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts

infra/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── k8s/                     # Optional Kubernetes manifests

tests/
├── test_council.py
├── test_agents.py
├── test_api.py
├── test_rag.py
└── test_mcp.py

.env.example
```

### 3.3 State Definition

```python
from typing import TypedDict, List, Optional
from pydantic import BaseModel

class AgentOutput(BaseModel):
    agent: str
    confidence: float  # 0-100
    contribution: str
    key_points: List[str]
    model_used: str    # Track which LLM provider was used

class Evidence(BaseModel):
    type: str
    id: str
    tag: Optional[str] = None
    lane: Optional[str] = None
    days: Optional[int] = None

class Action(BaseModel):
    type: str
    details: str

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
    round_number: int          # Current debate round (1-3)
    llm_calls_log: List[dict]  # Track all LLM calls for audit
```

### 3.4 API Endpoints

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/health` | — | `{"status": "ok"}` |
| POST | `/ingest/erp` | `{po_data, inventory}` | `{"ingested": count}` |
| POST | `/signals/news` | `{events: [...]}` | `{"processed": count}` |
| GET | `/risk/suppliers/{id}` | — | `{risk_score, drivers, impacted}` |
| POST | `/council/analyze` | `{query, context?}` | `{recommendation, agent_outputs, evidence}` |
| POST | `/optimize/routes` | `{constraints}` | `{routes, costs, tradeoffs}` |
| POST | `/rag/ask` | `{question}` | `{answer, citations}` |
| GET | `/council/{id}/trace` | — | LangSmith trace link |
| GET | `/models/status` | — | `{providers: [{name, available, latency}]}` |

### 3.5 LLM Router Implementation

```python
# backend/llm/router.py

from openai import OpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import os

class LLMRouter:
    """Routes LLM calls across providers with fallback chains."""

    PROVIDERS = {
        "groq": {
            "client": lambda: ChatGroq(
                groq_api_key=os.environ["GROQ_API_KEY"],
                model_name="llama-3.3-70b-versatile",
            ),
        },
        "openrouter": {
            "client": lambda: ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
                model="meta-llama/llama-3.3-70b-instruct",
                default_headers={
                    "HTTP-Referer": "https://supplychaingpt.ai",
                    "X-Title": "SupplyChainGPT Council",
                },
            ),
        },
        "nvidia": {
            "client": lambda: ChatOpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.environ["NVIDIA_API_KEY"],
                model="meta/llama-3.1-405b-instruct",
            ),
        },
        "anthropic": {
            "client": lambda: ChatAnthropic(
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
                model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
        },
    }

    def __init__(self, routing_config: dict):
        self.routing = routing_config
        self._clients = {}

    def get_client(self, provider: str, model: str = None):
        key = f"{provider}:{model}"
        if key not in self._clients:
            client = self.PROVIDERS[provider]["client"]()
            if model:
                client.model_name = model
            self._clients[key] = client
        return self._clients[key]

    async def invoke_with_fallback(self, agent: str, messages: list):
        config = self.routing[agent]
        primary = config["primary"]
        fallbacks = config["fallback"]

        # Try primary
        try:
            provider, model = primary.split(":")
            client = self.get_client(provider, model)
            response = await client.ainvoke(messages)
            return response, f"{provider}:{model}"
        except Exception as e:
            logging.warning(f"Primary LLM failed for {agent}: {e}")

        # Try fallbacks in order
        for fb in fallbacks:
            try:
                provider, model = fb.split(":")
                client = self.get_client(provider, model)
                response = await client.ainvoke(messages)
                return response, f"{provider}:{model}"
            except Exception as e:
                logging.warning(f"Fallback {fb} failed for {agent}: {e}")
                continue

        raise RuntimeError(f"All LLM providers failed for agent {agent}")
```

---

## 4. Frontend Specification

### 4.1 Core Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18 |
| Build Tool | Vite | 5+ |
| Language | TypeScript | 5+ |
| Routing | React Router | v6.4+ |
| Styling | Tailwind CSS | 3+ |
| UI Components | shadcn/ui + Radix UI | latest |
| Charts | Recharts | 2+ |
| Graph Visualization | React Flow | latest (optional) |
| Data Fetching | TanStack Query | 5+ |
| Real-time | Socket.io-client | 4+ |
| State Management | Zustand | 4+ |
| Animations | Framer Motion | 11+ |
| Icons | Lucide React | latest |

### 4.2 Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` or `/dashboard` | Dashboard | Risk heatmap, stats, quick query |
| `/chat` | Council Chat | Conversational UI with agent status |
| `/debate` | Debate Viewer | Debate timeline + predictions |
| `/brand` | Brand Control Room | Sentiment + crisis comms |

### 4.3 WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `council:start` | Client → Server | `{query, context?}` |
| `agent:status` | Server → Client | `{agent, status, confidence}` |
| `agent:contribution` | Server → Client | `{agent, contribution, confidence, model_used}` |
| `debate:round` | Server → Client | `{round_number, agents_responded}` |
| `council:complete` | Server → Client | `{recommendation, agent_outputs, evidence}` |
| `council:error` | Server → Client | `{error, agent?}` |

---

## 5. Data Layer Specification

### 5.1 Databases

| Database | Technology | Purpose |
|----------|-----------|---------|
| PostgreSQL 16 | Primary store | State persistence, POs, contracts, KPIs, checkpointer |
| Neo4j | Graph DB | Supplier relationship graph, n-tier mapping |
| Pinecone | Vector DB | Document + news embeddings for RAG |
| InfluxDB | Time-series | Sensor, price, demand data |
| Redis 7 | Cache | Real-time caching, risk scores, agent states, session |

### 5.2 Redis Caching Strategy

```
Key Pattern                    | TTL    | Purpose
------------------------------ | ------ | ----------------------------
rag:{query_hash}              | 1h     | RAG query results cache
mcp:{tool}:{params_hash}     | 30m    | MCP tool response cache
risk:{supplier_id}            | 15m    | Supplier risk score cache
council:{session_id}:state    | 24h    | Council session state
models:status                 | 5m     | LLM provider availability
```

---

## 6. RAG Pipeline Specification

### 6.1 Document Processing

```python
CHUNK_SIZE = 512          # tokens per chunk
CHUNK_OVERLAP = 50        # token overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-large"  # OpenAI
VECTOR_DB = "pinecone"
TOP_K = 5                 # chunks retrieved per query
```

### 6.2 Document Types Supported
- SOPs (Standard Operating Procedures)
- Contracts (SLAs, penalties, force majeure clauses)
- Past incident reports
- Supplier onboarding checklists
- Internal policy documents

### 6.3 RAG Flow
1. Upload document → chunk (512 tokens, 50 overlap) → embed (text-embedding-3-large) → store (Pinecone)
2. On query: embed query → retrieve top-5 chunks from Pinecone
3. LLM answers using retrieved context + citations to internal doc IDs
4. Cache result in Redis (1h TTL, keyed by query hash)

---

## 7. MCP Specification

### 7.1 MCP Tools per Agent

| Agent | MCP Tools |
|-------|-----------|
| Risk | `news_search`, `gdelt_query`, `supplier_financials` |
| Supply | `neo4j_query`, `supplier_search`, `contract_lookup` |
| Logistics | `route_optimize`, `port_status`, `freight_rate` |
| Market | `commodity_price`, `trade_data`, `tariff_lookup` |
| Finance | `erp_query`, `currency_rate`, `insurance_claim` |
| Brand | `social_sentiment`, `competitor_ads`, `content_generate` |

### 7.2 MCP Security
- Sandboxed execution with least-privilege scopes
- External content sanitization before RAG context injection
- Tool permissions restricted per agent
- Rate limiting per tool (max 100 QPS)

---

## 8. Optimization Specification (OR-Tools)

### 8.1 Supported Problem Types

| Type | Objective | Constraints |
|------|-----------|-------------|
| Routing | Minimize cost | Lead time ≤ target, delivery deadline |
| Allocation | Minimize risk-weighted cost | Supplier capacity ≤ available, MOQ, budget ≤ limit |
| Expedite | Minimize total impact | Service level targets, time windows |

### 8.2 Constraint Specification

```python
CONSTRAINTS = {
    "lead_time_max": 30,        # days
    "budget_max": 500000,        # USD
    "supplier_capacity": {},     # per supplier
    "moq": {},                   # per supplier-component pair
    "service_level_target": 0.95,
}
```

---

## 9. Security Specification

### 9.1 Authentication & Access

| Layer | Mechanism |
|-------|-----------|
| API | API key authentication (FastAPI middleware) |
| CORS | Whitelisted origins only |
| Rate Limiting | Per-endpoint, per-key limits |
| RBAC | Procurement / Finance / Comms roles |

### 9.2 AI Safety

| Concern | Mitigation |
|---------|-----------|
| Prompt injection | LlamaGuard / custom guardrails on every agent input |
| PII exposure | Redaction in Brand Agent outputs |
| Ungrounded responses | RAG grounding with doc ID citations |
| Tool misuse | MCP sandboxing, least-privilege scopes |
| External content | Sanitize before adding to RAG context |

### 9.3 Data Protection

- Data minimization: ingest only fields needed for scoring and planning
- PII handling: avoid storing unnecessary personal data; mask where required
- Auditability: store all agent outputs and evidence references for review
- Secrets: `.env` only, never committed

---

## 10. Observability Specification

### 10.1 LangSmith Tracing

```python
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<key>
LANGCHAIN_PROJECT=supplychaingpt-council
```

Custom metadata per run:
- `agent_name`: which agent is running
- `confidence`: agent confidence score
- `mcp_calls`: list of MCP tool calls made
- `model_used`: which LLM provider/model was used
- `provider`: groq / openrouter / nvidia / anthropic

### 10.2 Prometheus Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `council_query_duration_seconds` | Histogram | agent, model, provider |
| `council_llm_tokens_total` | Counter | agent, model, provider, type (input/output) |
| `council_errors_total` | Counter | agent, provider, error_type |
| `council_cache_hits_total` | Counter | cache_type (rag/mcp/risk) |

### 10.3 Grafana Dashboard

Pre-built JSON stub for:
- Council query latency (p50, p95, p99)
- Token usage by provider
- Error rate by agent
- Cache hit rate
- LLM provider availability

---

## 11. Deployment Specification

### 11.1 Docker Compose

```yaml
services:
  api:
    build:
      context: .
      dockerfile: infra/Dockerfile.backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, neo4j]

  web:
    build:
      context: .
      dockerfile: infra/Dockerfile.frontend
    ports: ["3000:80"]
    depends_on: [api]

  postgres:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: supplychaingpt
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  neo4j:
    image: neo4j:5
    volumes: [neo4jdata:/data]
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}

  redis:
    image: redis:7
    volumes: [redisdata:/data]

volumes:
  pgdata:
  neo4jdata:
  redisdata:
```

### 11.2 AWS Deployment

- **Compute**: ECS/Fargate for API + Web containers
- **Database**: RDS PostgreSQL, ElastiCache Redis
- **Secrets**: AWS Secrets Manager for API keys
- **CDN**: CloudFront for frontend static assets

---

## 12. Environment Variables

```env
# === LLM Providers ===
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
NVIDIA_API_KEY=nvapi-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# === LangSmith ===
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=supplychaingpt-council

# === Databases ===
POSTGRES_URI=postgresql://user:pass@localhost:5432/supplychaingpt
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=...
PINECONE_API_KEY=...
REDIS_URL=redis://localhost:6379

# === External APIs ===
NEWSAPI_KEY=...
GDELT_API_KEY=...
MARINE_TRAFFIC_API_KEY=...
FREIGHTOS_API_KEY=...

# === App ===
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_PER_MINUTE=60
```

---

## 13. Testing Specification

### 13.1 Backend Tests

| Test Type | Framework | Coverage |
|-----------|-----------|----------|
| Unit | pytest | All agents, tools, router |
| API | httpx + pytest | All endpoints |
| Integration | pytest | Full Council flow end-to-end |
| Load | locust | 50 concurrent queries |

### 13.2 Frontend Tests

| Test Type | Framework | Coverage |
|-----------|-----------|----------|
| Unit | vitest | Components, hooks, store |
| E2E | Playwright | All 4 pages + modals |

### 13.3 Edge Case Tests

- Low confidence → self-reflection loop
- MCP tool failure → cached fallback
- LLM provider down → fallback chain activation
- Human-in-loop interrupt
- Empty RAG results → graceful degradation
- Rate limit hit → queue + retry

---

## 14. Performance Targets

| Metric | Target |
|--------|--------|
| Council query end-to-end | < 8 seconds |
| Single agent response | < 2 seconds |
| RAG query with cache | < 500ms |
| RAG query without cache | < 3 seconds |
| WebSocket message latency | < 100ms |
| API health check | < 50ms |
| Frontend first paint | < 1.5 seconds |
