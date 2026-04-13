# Day 6 — Production Backend API + Observability

## Overview

Day 6 hardens the SupplyChainGPT Council backend for production with:
- **Production API** — structured JSON responses, new council endpoints
- **Observability** — LangSmith tracing, Prometheus metrics, real-time WebSocket debate streaming
- **Security** — prompt injection guardrails, PII redaction, security headers, Redis rate limiting
- **Structured Logging** — JSON-formatted logs with correlation IDs

---

## New Files

| File | Purpose |
|------|---------|
| `backend/observability/__init__.py` | Package init |
| `backend/observability/langsmith_config.py` | LangSmith tracing, CouncilTracer, metrics store, Prometheus export, cost tracking |
| `backend/middleware/security.py` | Prompt injection guard (17 patterns), PII redaction (SSN/email/phone/CC/IP), input sanitization, security headers |
| `backend/middleware/logging.py` | Structured JSON logging, request/response logging with correlation IDs |
| `backend/middleware/rate_limiter.py` | Redis sliding window rate limiter (in-memory fallback), per-endpoint limits, X-RateLimit-* headers |
| `backend/routes/observability.py` | Traces, metrics, spans, WebSocket debate streaming |

## Updated Files

| File | Changes |
|------|---------|
| `backend/config.py` | +15 settings: LangSmith, Prometheus, WebSocket, Security, Session TTL |
| `backend/graph.py` | +`human_review_node()`, +`run_council_streaming()` with astream_events, interrupt_before, Redis session storage |
| `backend/main.py` | New middleware stack (Security, RequestLogging, RedisRateLimit), `/metrics`, detailed `/health`, JSON logging, observability router |
| `backend/routes/council.py` | +`POST /council/query`, +`GET /council/history`, +`POST /council/execute-fallback` |
| `backend/middleware/auth.py` | Added `/metrics` to public endpoints |
| `backend/middleware/rate_limit.py` | Added `/metrics` to skip paths |
| `.env.example` | +20 new env vars for Day 6 features |

---

## API Endpoints

### Council (New)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/council/query` | Full graph with debate + optional SSE streaming (`stream: true`) |
| `GET` | `/council/history` | Past sessions from Redis (paginated) |
| `POST` | `/council/execute-fallback` | One-click MCP fallback execution |

### Observability

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/observability/traces` | LangSmith trace links for sessions |
| `GET` | `/observability/metrics` | Latency, token usage, confidence averages (JSON) |
| `GET` | `/observability/spans` | Detailed span breakdown |
| `WS` | `/observability/ws/debate` | Real-time debate round streaming |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/metrics` | Prometheus text-format metrics |
| `GET` | `/health` | Detailed health with uptime, component status |

---

## WebSocket Debate Protocol

Connect: `ws://localhost:8000/observability/ws/debate?api_key=dev-key`

### Client → Server

```json
{"action": "start", "query": "Taiwan chip crisis on EV battery supply"}
{"action": "approve", "session_id": "abc-123"}  // human-in-loop only
{"action": "ping"}
```

### Server → Client

```json
{"type": "start", "session_id": "abc-123", "query": "..."}
{"type": "agent_done", "data": {"agent": "risk", "session_id": "abc-123", "confidence": 85.0}}
{"type": "debate_round", "data": {"session_id": "abc-123", "debate_rounds": [...], "confidence": 0.78, "risk_score": 65.0}}
{"type": "complete", "data": {"session_id": "abc-123", "recommendation": "...", "confidence": 0.72, "risk_score": 55.0}}
{"type": "human_review_needed", "data": {...}}  // only if HUMAN_IN_LOOP=true
{"type": "heartbeat", "ts": 1712987654.321}
```

---

## Security Features

### Prompt Injection Guard
17 regex patterns block common injection attempts:
- "ignore all previous instructions"
- "you are now a..."
- "jailbreak", "DAN mode", "sudo mode"
- "reveal your system prompt"
- etc.

Returns `400` with structured error:
```json
{"success": false, "error": "Potential prompt injection detected. Please rephrase your query.", "data": null}
```

### PII Redaction
Automatic redaction of:
- SSN → `[SSN_REDACTED]`
- Email → `[EMAIL_REDACTED]`
- Phone → `[PHONE_REDACTED]`
- Credit Card → `[CC_REDACTED]`
- IP Address → `[IP_REDACTED]`

### Security Headers (all responses)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### Rate Limiting
- Redis sliding window (falls back to in-memory)
- Per-endpoint limits: `/council/query` = 10/min, `/council/stream` = 5/min
- `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers

---

## Observability

### LangSmith Tracing
- `CouncilTracer` class with span context managers for agents, debate rounds, MCP calls, RAG retrievals
- Metadata: `agent_name`, `round_number`, `confidence`, `mcp_tool_used`
- Cost tracking per model (estimated USD)
- Trace URL generation for frontend linking

### Prometheus Metrics (`/metrics`)
- `council_llm_calls_total{agent, model}`
- `council_llm_latency_ms{agent, model}`
- `council_debate_rounds_total{phase, round}`
- `council_mcp_calls_total{tool, agent}`
- `council_rag_retrievals_total{agent}`
- `council_llm_cost_usd_total{agent, model}`
- `council_info{version}`

### JSON Metrics (`/observability/metrics`)
Full summary with p50/p95/p99 latency, cache hit rates, cost estimates.

---

## Human-in-the-Loop

Set `HUMAN_IN_LOOP=true` in `.env`. The graph will pause before synthesis:
1. Graph runs through agents → debate → fallback
2. Pauses at `synthesize` node
3. WebSocket sends `human_review_needed` event
4. Client sends `{"action": "approve", "session_id": "..."}`
5. Graph resumes with synthesis

---

## Sample Usage

### Council Query (non-streaming)
```bash
curl -X POST http://localhost:8000/council/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{"query": "Taiwan chip crisis on EV battery supply", "stream": false}'
```

### Council Query (SSE streaming)
```bash
curl -N -X POST http://localhost:8000/council/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{"query": "Taiwan chip crisis on EV battery supply", "stream": true}'
```

### Session History
```bash
curl http://localhost:8000/council/history?limit=10 -H "X-API-Key: dev-key"
```

### Execute Fallback
```bash
curl -X POST http://localhost:8000/council/execute-fallback \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"session_id": "abc-123", "fallback_index": 0}'
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

---

## Environment Variables

```env
# Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=supplychaingpt-council
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_COST_TRACKING=true
LANGSMITH_TRACE_SAMPLE_RATE=1.0

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_DEBATE_BUFFER_SIZE=1000

# Security
SECURITY_HEADERS_ENABLED=true
PROMPT_INJECTION_GUARD=true
PII_REDACTION_ENABLED=true
MAX_QUERY_LENGTH=2000

# Session Storage
SESSION_STORE_TTL=86400

# Council
HUMAN_IN_LOOP=false
MAX_DEBATE_ROUNDS=3
CONFIDENCE_GAP_THRESHOLD=20.0
```

---

## Test Results

- **60/60** existing tests pass (no regressions)
- All new imports verified
- Live endpoint tests:
  - `/health` ✅ — all components OK
  - `/metrics` ✅ — Prometheus format
  - `/observability/metrics` ✅ — JSON metrics
  - `/observability/traces` ✅ — LangSmith links
  - `/council/history` ✅ — Redis session store
  - Prompt injection guard ✅ — blocks with 400
  - Security headers ✅ — all 6 headers present
  - JSON structured logging ✅ — correlation IDs
