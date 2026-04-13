# Day 6 Development — Real Data Integration + Market API + Streaming Debate

> **Date:** Day 6 (Apr 17)
> **Focus:** Replace all mock data with live APIs, build Market API for frontend, fix debate engine streaming, security hardening
> **Status:** ✅ Complete

---

## Overview

Day 6 was the most impactful day: 23 new MCP tools were added (45 total), a Market API was built to aggregate live data for the frontend, the debate engine was converted from blocking to SSE streaming, and all exposed API keys were removed from the codebase.

---

## 1. Real Data Integration — 12 Live APIs

### API Status (All Verified)

| API | Tools | Data | Sample Output |
|-----|-------|------|---------------|
| **Finnhub** | `stock_quote`, `company_profile`, `company_financials` | Real-time stocks | TSM $370.60, AAPL $260.48 |
| **Frankfurter** | `exchange_rate`, `historical_rate` | ECB forex rates | EUR=0.8539, CNY=6.8284 |
| **Yahoo Finance** | `fred_commodity_price` (fallback) | Commodity prices | Crude Oil $102.25 |
| **Open-Meteo** | `weather_forecast` | 7-day weather | Taiwan 28°C, rain 40% |
| **USGS** | `earthquake_check` | Seismic data | 10 quakes near Taiwan |
| **Wikipedia** | `wikipedia_search`, `wikipedia_summary` | Knowledge base | TSMC article, 2936 chars |
| **Reddit** | `reddit_sentiment` | Social sentiment | r/supplychain posts |
| **World Bank** | `worldbank_indicator` | Country indicators | US GDP 5 years |
| **GDACS** | `disaster_alerts` | Global disasters | 5 active alerts |
| **GDELT** | `gdelt_events`, `gdelt_tone` | Geopolitical events | Rate-limited but works |
| **SEC EDGAR** | `sec_filing` | Company filings | 10-K, 10-Q forms |
| **OpenCorporates** | `opencorporates_search` | Company registry | Entity search |

### New Tool Files

| File | Tools | Category |
|------|-------|----------|
| `gdelt_tools.py` | `gdelt_events`, `gdelt_tone` | geopolitical |
| `finnhub_tools.py` | `stock_quote`, `company_profile`, `company_financials` | financial |
| `fred_tools.py` | `fred_commodity_price`, `economic_indicator` | economic |
| `frankfurter_tools.py` | `exchange_rate`, `historical_rate` | forex |
| `weather_tools.py` | `weather_forecast`, `earthquake_check`, `disaster_alerts` | disaster |
| `knowledge_tools.py` | `wikipedia_search`, `wikipedia_summary`, `arxiv_search`, `reddit_sentiment` | knowledge |
| `trade_tools.py` | `trade_flows`, `sec_filing`, `opencorporates_search` | trade |

### Key Fixes Applied

| Issue | Fix |
|-------|-----|
| Wikipedia REST API returns 403 (bot policy) | Switched to MediaWiki API (`/w/api.php`) with User-Agent header |
| Reddit JSON unreliable | Changed to `old.reddit.com` for consistent JSON access |
| Frankfurter/Arxiv HTTP 301 redirects | Added `follow_redirects=True` to `httpx.AsyncClient` |
| GDELT 429 rate limiting | Added mock fallback on rate limit response |
| FRED API key invalid format | Added Yahoo Finance fallback for commodity prices |
| Duplicate tool name `commodity_price` | Renamed FRED version to `fred_commodity_price` |
| API keys not found | Read from `backend.config.settings` first, then `os.getenv` |

---

## 2. Market API — Frontend Aggregation

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     MARKET API ROUTER                             │
│                   /market (FastAPI)                               │
│                                                                   │
│  /ticker ──► asyncio.gather(                                     │
│      stock_quote ×4,    # TSM, INTC, AAPL, NVDA                 │
│      exchange_rate,     # USD → EUR,CNY,JPY,TWD,KRW,GBP        │
│      fred_commodity_price ×2  # crude_oil, copper                │
│  )                                                                │
│                                                                   │
│  /company/{symbol} ──► asyncio.gather(                           │
│      company_profile,                                             │
│      stock_quote,                                                 │
│      company_financials,                                          │
│      wikipedia_summary,                                           │
│  )                                                                │
│                                                                   │
│  /risk-dashboard ──► asyncio.gather(                             │
│      earthquake_check ×3,  # Taiwan, Japan, China               │
│      weather_forecast ×3,  # same regions                        │
│      disaster_alerts,      # global                               │
│  )                                                                │
│                                                                   │
│  /brand-intel ──► asyncio.gather(                                │
│      reddit_sentiment ×2,  # r/supplychain, r/logistics          │
│      wikipedia_search,                                             │
│      arxiv_search,                                                 │
│  )                                                                │
└──────────────────────────────────────────────────────────────────┘
```

### Endpoints

| Endpoint | Method | Data Sources | Frontend Page |
|----------|--------|-------------|---------------|
| `GET /market/ticker` | GET | Finnhub + Frankfurter + Yahoo Finance | Dashboard |
| `GET /market/company/{symbol}` | GET | Finnhub + Wikipedia | Brand (company search) |
| `GET /market/risk-dashboard` | GET | USGS + Open-Meteo + GDACS | Dashboard (risk section) |
| `GET /market/brand-intel` | GET | Reddit + Wikipedia + Arxiv | Brand |

### File: `backend/routes/market.py`

- Uses `asyncio.gather` for parallel MCP tool invocations
- Each endpoint aggregates 4-7 MCP tool calls into a single response
- Graceful error handling: individual tool failures don't crash the endpoint
- All endpoints are **public** (no API key required) — configured in auth middleware

### Auth Configuration

```python
# backend/middleware/auth.py
PUBLIC_ENDPOINTS = {
    "/health", "/ready", "/docs", "/openapi.json", "/redoc", "/test",
    "/market/ticker", "/market/risk-dashboard", "/market/brand-intel",
}
PUBLIC_PREFIXES = ("/market/company/",)
```

### Vite Proxy

```typescript
// frontend/vite.config.ts
proxy: {
  '/market': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

### Frontend Hooks

```typescript
// frontend/src/hooks/useMarketQuery.ts
export const useMarketTicker = () => useQuery({
  queryKey: ['market-ticker'],
  queryFn: () => marketApi.ticker(),
  refetchInterval: 60000,  // refresh every 60s
})

export const useCompanyOverview = (symbol: string) => useQuery({
  queryKey: ['company', symbol],
  queryFn: () => marketApi.companyOverview(symbol),
  enabled: !!symbol,
})

export const useRiskDashboard = () => useQuery({
  queryKey: ['risk-dashboard'],
  queryFn: () => marketApi.riskDashboard(),
  refetchInterval: 300000,  // refresh every 5 min
})

export const useBrandIntel = () => useQuery({
  queryKey: ['brand-intel'],
  queryFn: () => marketApi.brandIntel(),
})
```

---

## 3. SSE Streaming Debate Engine

### Problem

The debate engine used a blocking `/council/analyze` endpoint that:
- Waited for all 7 agents + moderator to finish before returning
- Timed out at 30s (frontend Axios timeout)
- No real-time feedback — user saw nothing until completion

### Solution

Converted to SSE (Server-Sent Events) streaming via `/council/stream`:

```
┌──────────────────────────────────────────────────────────────────┐
│                 SSE STREAMING PIPELINE                            │
│                                                                   │
│  POST /council/stream {query}                                    │
│      │                                                            │
│      ▼                                                            │
│  event_generator():                                               │
│      yield start event (session_id)                              │
│      for each agent:                                             │
│          yield agent_start                                       │
│          async for token in llm_router.stream_with_fallback():   │
│              yield token event                                   │
│          yield agent_done                                        │
│      yield agent_start (moderator)                               │
│      async for token in llm_router.stream_with_fallback():       │
│          yield token event                                       │
│      yield agent_done (moderator)                                │
│      yield complete event (recommendation)                       │
└──────────────────────────────────────────────────────────────────┘
```

### SSE Event Schema

```json
{"type": "start", "session_id": "uuid"}
{"type": "agent_start", "agent": "risk"}
{"type": "token", "agent": "risk", "content": "Risk Analysis..."}
{"type": "agent_done", "agent": "risk"}
{"type": "agent_start", "agent": "supply"}
{"type": "token", "agent": "supply", "content": "Supply Analysis..."}
...
{"type": "agent_start", "agent": "moderator"}
{"type": "token", "agent": "moderator", "content": "Recommendation..."}
{"type": "agent_done", "agent": "moderator"}
{"type": "complete", "session_id": "uuid", "recommendation": "..."}
```

### Backend: `council_stream()`

```python
@router.post("/stream")
async def council_stream(request: CouncilRequest):
    session_id = str(uuid.uuid4())

    async def event_generator():
        yield start event

        for agent_name, system_prompt in AGENT_PROMPTS.items():
            yield agent_start event
            async for token in llm_router.stream_with_fallback(agent_name, messages):
                yield token event
            yield agent_done event

        yield moderator_start + tokens + done
        yield complete event

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Frontend: `useCouncilStream` Hook

```typescript
export function useCouncilStream() {
  const startStream = useCallback(async (query: string) => {
    const response = await fetch('/council/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({ query }),
      signal: abortController.signal,
    })

    const reader = response.body.getReader()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      // Parse SSE lines → dispatch to Zustand store
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6))
          handleStreamEvent(event)
        }
      }
    }
  }, [])

  const stopStream = () => abortController.abort()

  return { startStream, stopStream, isStreaming, agentOutputs, currentSession }
}
```

### Debate Page UI

- Real-time agent output cards (color-coded per agent)
- Stop button during streaming
- PDF export button after completion
- Confidence bar for moderator
- Markdown rendering for agent outputs

### Verified Performance

- **4029 events** streamed in a single test query
- **Groq LLM** as primary: ~2s per agent
- **OpenRouter + NVIDIA** as fallbacks
- **Zero timeouts** with 120s frontend timeout

---

## 4. LLM Router Refactoring

### Before (Day 5)

- All agents used NVIDIA as primary provider
- No Groq or OpenRouter in routing
- NVIDIA API key often missing → all agents failed
- No timeout handling in streaming

### After (Day 6)

```python
ROUTING = {
    "risk":      {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "supply":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "logistics": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "market":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "finance":   {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "brand":     {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
    "moderator": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:...", "nvidia:..."]},
}
```

- **Groq** as primary (fast, reliable, free tier)
- **OpenRouter** as first fallback (free models)
- **NVIDIA** as second/third fallback
- Added `asyncio.TimeoutError` handling in `stream_with_fallback`

---

## 5. Security Fixes

### API Key Exposure

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY` exposed in `.env.example` | Removed from `.env.example`, cleared value |
| `google_api_key` in `config.py` | Removed field from `Settings` class |
| `gemini_api_key` in `config.py` | Removed field from `Settings` class |
| `.env` file still has `GOOGLE_API_KEY` | Added `extra = "ignore"` to `Config` class |
| All API key values in `.env.example` | Cleared — only placeholders remain |

### Config Fix

```python
# backend/config.py
class Settings(BaseModel):
    # ... (no google_api_key or gemini_api_key)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Prevents crash from leftover .env vars
```

### Frontend Timeout Fix

| Client | Before | After |
|--------|--------|-------|
| `api` (main) | 30,000ms | 120,000ms |
| `mcpApi` (MCP) | 30,000ms | 120,000ms |

---

## 6. Frontend Pages Updated

### Dashboard (`Dashboard.tsx`)
- Live stock tickers (TSM, INTC, AAPL, NVDA) from Finnhub
- Live forex rates (EUR, CNY, JPY, TWD, KRW, GBP) from Frankfurter
- Live commodity prices (Crude Oil, Copper) from Yahoo Finance
- Earthquake alerts from USGS (Taiwan, Japan, China)
- Weather forecasts from Open-Meteo
- Global disaster alerts from GDACS
- `mock: true/false` indicators on each data card

### Brand (`Brand.tsx`)
- Live Reddit feeds (r/supplychain, r/logistics)
- Wikipedia knowledge search
- Arxiv research papers
- Company profile search (via `/market/company/{symbol}`)
- Interactive search controls

### Debate (`Debate.tsx`)
- SSE streaming via `useCouncilStream` hook
- Real-time agent output cards (7 agents + moderator)
- Color-coded agent labels
- Stop button during streaming
- PDF export after completion
- Markdown rendering for agent outputs
- Confidence bar for moderator

### Settings (`Settings.tsx`)
- Live API status indicators (green/red) for 10 APIs
- API key management UI
- RAG configuration settings
- No dummy data

---

## 7. Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `backend/routes/market.py` | Market API router (4 endpoints) |
| `frontend/src/hooks/useMarketQuery.ts` | React Query hooks for market data |
| `frontend/src/hooks/useCouncilStream.ts` | SSE streaming hook |

### Modified Files

| File | Changes |
|------|---------|
| `backend/main.py` | Added `market_router` import + include |
| `backend/config.py` | Removed `google_api_key`/`gemini_api_key`, added `extra = "ignore"` |
| `backend/llm/router.py` | Groq primary, OpenRouter fallback, timeout handling |
| `backend/middleware/auth.py` | Added `/market/*` public endpoints + prefixes |
| `backend/mcp/tools/fred_tools.py` | Added Yahoo Finance fallback |
| `frontend/vite.config.ts` | Added `/market` proxy |
| `frontend/src/lib/api.ts` | Added `marketApi` methods, timeout 120s |
| `frontend/src/pages/Dashboard.tsx` | Live market data + risk dashboard |
| `frontend/src/pages/Brand.tsx` | Live brand intelligence |
| `frontend/src/pages/Debate.tsx` | SSE streaming debate |
| `frontend/src/pages/Settings.tsx` | Live API status indicators |
| `.env.example` | Cleared all API key values |

---

## Day 6 Deliverables ✅

- [x] 23 new MCP tools (45 total) — all 12 APIs verified LIVE
- [x] Market API: 4 aggregation endpoints for frontend
- [x] Dashboard: Live stocks, forex, commodities, earthquakes, weather, disasters
- [x] Brand: Live Reddit, Wikipedia, Arxiv, company search
- [x] Debate: SSE streaming (4029 events verified)
- [x] LLM Router: Groq primary + OpenRouter/NVIDIA fallbacks
- [x] Security: Removed exposed API keys, added `extra = "ignore"`
- [x] Frontend timeout: 30s → 120s
- [x] Yahoo Finance fallback for commodity prices
- [x] Settings: Live API status indicators
- [x] All dummy data removed from frontend
