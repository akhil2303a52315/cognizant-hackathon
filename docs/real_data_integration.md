# Real Data Integration Plan — APIs & MCPs

> **Goal:** Replace all mock data with live APIs for hackathon demo
> **Total APIs:** 15 | **API Keys Needed:** 4 | **No-Key APIs:** 11
> **Estimated Integration Time:** ~3 hours

---

## 🔑 Required API Keys

| Key | Service | Get It | Free Tier |
|-----|---------|--------|-----------|
| `FINNHUB_API_KEY` | Finnhub (Stocks/Forex) | https://finnhub.io/register | 60 req/min |
| `FRED_API_KEY` | FRED (Economic Data) | https://fred.stlouisfed.org/docs/api/api_key.html | Unlimited |
| `FIRECRAWL_API_KEY` | Firecrawl (Web Scraping) | https://firecrawl.dev | 500 credits/mo |
| `NEWSAPI_KEY` | NewsAPI (Headlines) | https://newsapi.org | 100 req/day |

---

## 📊 Data APIs — By Domain

### 1. News & Geopolitical Events

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **GDELT** | `https://api.gdeltproject.org/api/v2/doc/doc` | ❌ None | `gdelt_query` | Custom MCP |
| **NewsAPI** | `https://newsapi.org/v2/` | ✅ `NEWSAPI_KEY` | `news_search` | Already integrated via Firecrawl |
| **ACLED** | `https://api.acleddata.com/acled/read/` | ❌ None (academic) | Conflict data | Custom MCP |

**GDELT Integration Details:**
- Query: `https://api.gdeltproject.org/api/v2/doc/doc?query=supply chain disruption&mode=artlist&maxrecords=10&format=json`
- Returns: Article title, URL, date, tone, country, themes
- Use for: Risk Sentinel agent — real-time geopolitical risk scoring

---

### 2. Financial & Supplier Data

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **Finnhub** | `https://finnhub.io/api/v1/` | ✅ `FINNHUB_API_KEY` | `supplier_financials` | Custom MCP |
| **Alpha Vantage** | `https://www.alphavantage.co/query` | ✅ Free key | `commodity_price` backup | Custom MCP |
| **SEC EDGAR** | `https://efts.sec.gov/LATEST/` | ❌ None | Supplier filings | Custom MCP |
| **Yahoo Finance** | `yfinance` Python package | ❌ None | Stock data backup | Custom MCP |

**Finnhub Integration Details:**
- Quote: `GET /quote?symbol=TSM&token=KEY` → current price, change, high/low
- Company: `GET /stock/profile2?symbol=TSM&token=KEY` → name, industry, market cap
- Financials: `GET /stock/financials?symbol=TSM&statement=bs&token=KEY` → balance sheet
- Use for: Finance Agent — real supplier financial health scoring

---

### 3. Commodity & Economic Data

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **FRED** | `https://api.stlouisfed.org/fred/` | ✅ `FRED_API_KEY` | `commodity_price` | Custom MCP |
| **World Bank** | `https://api.worldbank.org/v2/` | ❌ None | Country indicators | Custom MCP |
| **OECD** | `https://data.oecd.org/api/` | ❌ None | Trade/industry data | Custom MCP |

**FRED Integration Details:**
- Series: `GET /series/observations?series_id=PSOUSD&api_key=KEY&file_type=json`
- Key series: `PSOUSD` (crude oil), `WPU102` (industrial commodities), `DEXJPUS` (JPY/USD)
- Search: `GET /series/search?search_words=supply chain&api_key=KEY`
- Use for: Market Agent — real commodity prices, economic indicators

---

### 4. Currency & Forex

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **Frankfurter** | `https://api.frankfurter.app/` | ❌ None | `currency_rate` | Custom MCP |
| **ExchangeRate-API** | `https://open.er-api.com/v6/latest/USD` | ❌ None (1500/mo) | Backup | Custom MCP |

**Frankfurter Integration Details:**
- Latest: `GET /latest?from=USD&to=EUR,CNY,JPY,TWD`
- Historical: `GET /2024-01-15?from=USD&to=EUR`
- ECB-sourced, daily updates, no API key
- Use for: Finance Agent — real forex rates for international supplier costing

---

### 5. Weather & Natural Disasters

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **Open-Meteo** | `https://api.open-meteo.com/v1/forecast` | ❌ None | New tool | Custom MCP |
| **USGS Earthquake** | `https://earthquake.usgs.gov/fdsnws/event/1/` | ❌ None | New tool | Custom MCP |
| **GDACS** | `https://www.gdacs.org/xml/rss.xml` | ❌ None | Disaster alerts | Custom MCP |

**Open-Meteo Integration Details:**
- Forecast: `GET /v1/forecast?latitude=25.0&longitude=121.5&daily=temperature_2m_max,precipitation_sum,windspeed_10m_max&timezone=Asia/Taipei`
- Historical: `GET /v1/forecast?latitude=25.0&longitude=121.5&past_days=30&...`
- Use for: Risk Agent — weather disruption at supplier locations

**USGS Earthquake Integration Details:**
- Query: `GET /query?format=geojson&minmagnitude=5&lat=25.0&lon=121.5&maxradiuskm=500&starttime=2024-01-01`
- Returns: Magnitude, location, depth, time, tsunami warning
- Use for: Risk Agent — seismic risk near semiconductor fabs (Taiwan/Japan)

---

### 6. Trade & Tariffs

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **UN Comtrade** | `https://comtradeapi.un.org/` | ❌ None (registered) | `trade_data` | Custom MCP |
| **WITS** | `https://wits.worldbank.org/APIs/` | ❌ None | Tariff data | Custom MCP |

---

### 7. Social & Sentiment

| API | Endpoint | Key? | Replaces Mock | MCP? |
|-----|----------|------|---------------|------|
| **Reddit** | `https://www.reddit.com/r/supplychain.json` | ❌ None (100/min) | `social_sentiment` | Custom MCP |
| **Google Trends** | `https://trends.google.com/trending?geo=US` | ❌ None (unofficial) | Brand trends | Custom MCP |

---

### 8. Knowledge & Research

| API | Endpoint | Key? | Adds | MCP? |
|-----|----------|------|------|------|
| **Wikipedia** | `https://api.wikimedia.org/` | ❌ None | Company/country profiles | `npx -y @anthropic/mcp-server-wikipedia` |
| **Arxiv** | `http://export.arxiv.org/api/query` | ❌ None | Supply chain research | `npx -y @anthropic/mcp-server-arxiv` |
| **Semantic Scholar** | `https://api.semanticscholar.org/graph/v1/` | ❌ None | Academic citations | Custom MCP |
| **Wikidata** | `https://query.wikidata.org/sparql` | ❌ None | Structured entity data | Custom MCP |

---

## 🔧 Pre-Built MCP Servers (Install Now)

| MCP Server | Purpose | Install |
|------------|---------|---------|
| **Fetch MCP** | HTTP requests to any API | `npx -y @anthropic/mcp-server-fetch` |
| **Wikipedia MCP** | Wikipedia search & articles | `npx -y @anthropic/mcp-server-wikipedia` |
| **Arxiv MCP** | Research paper search | `npx -y @anthropic/mcp-server-arxiv` |
| **Sequential Thinking MCP** | Structured agent reasoning | `npx -y @anthropic/mcp-server-sequential-thinking` |
| **Memory MCP** | Persistent agent memory | `npx -y @anthropic/mcp-server-memory` |
| **Filesystem MCP** | Local file access | `npx -y @anthropic/mcp-server-filesystem` |
| **Brave Search MCP** | Web search (backup) | `npx -y @anthropic/mcp-server-brave-search` |
| **SQLite MCP** | Local DB queries | `npx -y @anthropic/mcp-server-sqlite` |

---

## 🏗️ Custom MCPs to Build

| MCP Name | Wraps | Tools Added | Priority | Est. Time |
|----------|-------|-------------|----------|-----------|
| `gdelt_mcp` | GDELT API | `gdelt_events`, `gdelt_tone` | 🥇 P0 | 30 min |
| `finnhub_mcp` | Finnhub API | `stock_quote`, `company_profile`, `financials` | 🥇 P0 | 30 min |
| `fred_mcp` | FRED API | `economic_series`, `commodity_price` | 🥇 P0 | 30 min |
| `frankfurter_mcp` | Frankfurter API | `exchange_rate`, `historical_rate` | 🥈 P1 | 15 min |
| `weather_mcp` | Open-Meteo + USGS | `weather_forecast`, `earthquake_check` | 🥈 P1 | 25 min |
| `comtrade_mcp` | UN Comtrade API | `trade_flows`, `tariff_rates` | 🥉 P2 | 45 min |
| `reddit_mcp` | Reddit API | `reddit_sentiment`, `reddit_search` | 🥉 P2 | 20 min |
| `worldbank_mcp` | World Bank API | `country_indicators`, `gdp_data` | 🥉 P2 | 25 min |

---

## 📋 Integration Priority Order

### Phase A: Replace Mocks (P0) — ~90 min
1. `gdelt_mcp` → replaces `gdelt_query` mock
2. `finnhub_mcp` → replaces `supplier_financials` mock
3. `fred_mcp` → replaces `commodity_price` mock
4. `frankfurter_mcp` → replaces `currency_rate` mock

### Phase B: New Capabilities (P1) — ~45 min
5. `weather_mcp` → adds disaster risk assessment
6. Install pre-built MCPs (fetch, wikipedia, sequential-thinking, memory)

### Phase C: Extended Data (P2) — ~90 min
7. `comtrade_mcp` → adds trade flow data
8. `reddit_mcp` → adds social sentiment
9. `worldbank_mcp` → adds country indicators

---

## 🔒 Environment Variables to Add

```env
# Real Data APIs
FINNHUB_API_KEY=...
FRED_API_KEY=...
FIRECRAWL_API_KEY=fc-...
NEWSAPI_KEY=...

# No key needed (but listed for reference)
# GDELT_API_KEY= (none)
# FRANKFURTER_API_KEY= (none)
# OPEN_METEO_API_KEY= (none)
# USGS_API_KEY= (none)
# WIKIPEDIA_API_KEY= (none)
# ARXIV_API_KEY= (none)
# COMTRADE_API_KEY= (none, but register)
# REDDIT_CLIENT_ID= (optional, for higher limits)
```

---

## 📈 Expected MCP Tool Count After Integration

| Current | After Phase A | After Phase B | After Phase C |
|---------|---------------|---------------|---------------|
| 22 tools | 28 tools (+6) | 34 tools (+6) | 40 tools (+6) |

---

## ✅ Mock Fallback Strategy

Every custom MCP tool will follow this pattern:

```python
async def tool_function(params):
    api_key = os.getenv("API_KEY")
    if not api_key:
        return mock_response(params)  # Graceful fallback
    
    try:
        response = await httpx_async_client.get(url, params={...})
        return response.json()
    except Exception:
        return mock_response(params)  # Fallback on error
```

This ensures the demo **never breaks** — if an API is down or key is missing, mock data is returned with a `mock: true` flag so the UI can show a warning.
