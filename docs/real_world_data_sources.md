# SupplyChainGPT — Real-World Data Sources Master Document

> **Last Updated**: 13 April 2026 | **Total MCP Tools**: 96 | **Live APIs**: 26 | **Mock Fallbacks**: 5
>
> Reference: [public-apis/public-apis](https://github.com/public-apis/public-apis) — 1,400+ free APIs catalogued

---

## Table of Contents

1. [Currently Integrated Sources (19 Live + 8 Mock)](#1-currently-integrated-sources)
2. [Newly Integrated Sources — Day 7 (7 APIs, 27 MCP Tools)](#2-newly-integrated-sources--day-7)
3. [Complete MCP Tool Inventory (75 Tools)](#3-complete-mcp-tool-inventory-75-tools)
4. [Agent ↔ Source Coverage Matrix](#4-agent--source-coverage-matrix)
5. [API Key Reference](#5-api-key-reference)
6. [Recommended Additional Sources (from public-apis)](#6-recommended-additional-sources)
7. [Sources by Essential Category Gaps](#7-sources-by-essential-category-gaps)
8. [Integration Status Summary](#8-integration-status-summary)

---

## 1. Currently Integrated Sources

### ✅ LIVE Data Sources (Real API calls, confirmed working)

| # | Source | Category | API Endpoint | Tool File | API Key | Auth | Rate Limit |
|---|--------|----------|-------------|-----------|---------|------|------------|
| 1 | **Finnhub** | Financial | `finnhub.io/api/v1` | `finnhub_tools.py` | `FINNHUB_API_KEY` | apiKey | 60/min |
| 2 | **Frankfurter** | Forex | `frankfurter.app` | `frankfurter_tools.py` | None | None | Unlimited |
| 3 | **Open-Meteo** | Weather | `api.open-meteo.com` | `weather_tools.py` | None | None | 10K/day |
| 4 | **USGS** | Earthquake | `earthquake.usgs.gov` | `weather_tools.py` | None | None | Unlimited |
| 5 | **Wikipedia/MediaWiki** | Knowledge | `en.wikipedia.org/w/api.php` | `knowledge_tools.py` | None | None | Unlimited |
| 6 | **Reddit** | Social | `old.reddit.com` | `knowledge_tools.py` | Optional | OAuth | 60/min |
| 7 | **World Bank** | Economic | `api.worldbank.org/v2` | `knowledge_tools.py` | None | None | Unlimited |
| 8 | **GDACS** | Disaster | `gdacs.org` | `gdelt_tools.py` | None | None | Unlimited |
| 9 | **GDELT** | Geopolitical | `api.gdeltproject.org` | `gdelt_tools.py` | None | None | Rate-limited (429) |
| 10 | **SEC EDGAR** | Regulatory | `sec.gov/edgar` | `knowledge_tools.py` | None | None | 10/sec |
| 11 | **OpenCorporates** | Corporate | `api.opencorporates.com` | `knowledge_tools.py` | Optional | apiKey | 100/day |
| 12 | **NewsAPI** | News | `newsapi.org/v2` | `news_tools.py` | `NEWSAPI_KEY` | apiKey | 100/day |
| 13 | **Alpha Vantage** | Commodity/Economic | `alphavantage.co/query` | `alpha_vantage_tools.py` | `ALPHA_VANTAGE_API_KEY` | apiKey | 25/day |
| 14 | **Polygon.io** | Financial/Market | `api.polygon.io` | `polygon_tools.py` | `POLYGON_API_KEY` | apiKey | 5/min |
| 15 | **OpenWeatherMap** | Weather/Alerts | `api.openweathermap.org` | `openweather_tools.py` | `OPENWEATHERMAP_API_KEY` | apiKey | 60/min |
| 16 | **Mediastack** | News (435+ feeds) | `api.mediastack.com/v1` | `mediastack_tools.py` | `MEDIASTACK_API_KEY` | apiKey | 100/mo |
| 17 | **NOAA** | Climate/Storms | `ncdc.noaa.gov/cdo-web/api/v2` | `noaa_tools.py` | `NOAA_API_KEY` | token | 5/sec |
| 18 | **NIST NVD** | Cyber/Vuln | `services.nvd.nist.gov/rest/json` | `nvd_tools.py` | `NIST_NVD_API_KEY` | apiKey | 5/sec |
| 19 | **Currents API** | News/Sentiment | `api.currentsapi.services/v1` | `currents_tools.py` | `CURRENTS_API_KEY` | apiKey | 200/day |

### ⚠️ MOCK-Only Sources (Return hardcoded data, no real API connected)

| # | Source | Category | Tool File | Issue | Fix Needed |
|---|--------|----------|-----------|-------|------------|
| 1 | **FRED** | Economic | `fred_tools.py` | `FRED_API_KEY` invalid format (needs 32-char lowercase) | Get new key from [fred.stlouisfed.org](https://fred.stlouisfed.org) |
| 2 | **ERP/Inventory** | Business | `finance_tools.py` | `_erp_query` → mock procurement data | Connect to real Neon PG or SAP sandbox |
| 3 | **Currency (basic)** | Finance | `finance_tools.py` | `_currency_rate` → hardcoded 0.92 | Superseded by Frankfurter + Alpha Vantage |
| 4 | **Shipping/Route** | Logistics | `shipping_tools.py` | `_route_optimize`, `_port_status`, `_freight_rate` all mock | Need MarineTraffic or similar |
| 5 | **Commodity prices** | Market | `commodity_tools.py` | `_commodity_price`, `_trade_data`, `_tariff_lookup` all mock | Superseded by Alpha Vantage |
| 6 | **Social Sentiment** | Brand | `social_tools.py` | Tries Firecrawl, then mock | Need real sentiment API |
| 7 | **Arxiv** | Knowledge | `knowledge_tools.py` | HTTPS redirect issue | Add `follow_redirects=True` |
| 8 | **UN Comtrade** | Trade | `trade_tools.py` | Tries real API, often falls back | Needs registration for high volume |

### 🔧 Internal Data Sources (Not external APIs)

| # | Source | Type | Tool File | Status |
|---|--------|------|-----------|--------|
| 1 | **Neo4j** | Graph DB | `supplier_tools.py` | Real if Neo4j running |
| 2 | **Firecrawl** | Web scraping | `firecrawl_tools.py` | Needs `FIRECRAWL_API_KEY` |
| 3 | **ChromaDB** | Vector store | RAG pipeline | Local, always available |
| 4 | **Neon PostgreSQL** | Primary DB | Various | Cloud, always available |

---

## 2. Newly Integrated Sources — Day 7

### Alpha Vantage (`alpha_vantage_tools.py`) — 4 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `av_commodity_price` | Real-time commodity prices (WTI, Brent, natural gas, copper, aluminum, wheat, corn, iron ore, lithium) | Market, Finance | 300s |
| `av_stock_time_series` | Daily stock price time-series (30 days) | Market, Finance | 1800s |
| `av_economic_indicator` | GDP, CPI, inflation, unemployment, PMI per country | Market, Finance | 86400s |
| `av_currency_exchange` | Real-time currency exchange rate | Finance | 1800s |

**API Key**: `ALPHA_VANTAGE_API_KEY=<configured>` ✅ Configured

### Polygon.io (`polygon_tools.py`) — 5 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `polygon_stock_aggregate` | Stock OHLCV aggregate bars (price history) | Market, Finance | 1800s |
| `polygon_stock_snapshot` | Real-time stock snapshot (price, change, volume) | Market, Finance | 60s |
| `polygon_forex_rate` | Real-time forex exchange rate | Finance | 1800s |
| `polygon_market_status` | Current market status for all exchanges | Market | 300s |
| `polygon_ticker_news` | News articles for a stock ticker | Market, Brand | 3600s |

**API Key**: `POLYGON_API_KEY=<configured>` ✅ Configured

### OpenWeatherMap (`openweather_tools.py`) — 4 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `owm_current_weather` | Current weather conditions for a location | Risk, Logistics | 600s |
| `owm_weather_forecast` | 24-hour weather forecast (3h intervals) | Logistics | 1800s |
| `owm_weather_alerts` | Severe weather alerts (One Call API) | Risk | 300s |
| `owm_air_quality` | Air quality index (AQI, PM2.5, PM10) | Risk | 3600s |

**API Key**: `OPENWEATHERMAP_API_KEY=<configured>` ✅ Configured

### Mediastack (`mediastack_tools.py`) — 3 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `mediastack_news_search` | Search 435+ curated news feeds across 15 categories | Brand, Market | 1800s |
| `mediastack_sources` | List available news sources | Brand | 86400s |
| `mediastack_historical_news` | Search historical news by date range | Market | 86400s |

**API Key**: `MEDIASTACK_API_KEY=<configured>` ✅ Configured

### NOAA (`noaa_tools.py`) — 4 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `noaa_climate_data` | Climate data (temperature, precipitation, snow) | Risk | 86400s |
| `noaa_storm_events` | Severe storm events (tornado, flood, hurricane) | Risk, Logistics | 86400s |
| `noaa_sea_level` | Sea level rise trends (port disruption risk) | Logistics, Risk | 86400s |
| `noaa_drought_monitor` | US Drought Monitor data (agricultural risk) | Risk, Supply | 86400s |

**API Key**: `NOAA_API_KEY=<configured>` ✅ Configured

### NIST NVD (`nvd_tools.py`) — 4 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `nvd_cve_search` | Search CVEs by keyword (supply chain, SCADA) | Risk | 3600s |
| `nvd_cve_by_cpe` | Search CVEs by CPE name (vendor/product) | Risk | 3600s |
| `nvd_cve_details` | Full details for a specific CVE | Risk | 86400s |
| `nvd_recent_cves` | Recently published CVEs (last N days) | Risk | 3600s |

**API Key**: `NIST_NVD_API_KEY=<configured>` ✅ Configured

### Currents API (`currents_tools.py`) — 3 MCP Tools

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `currents_news_search` | Search news from 200+ sources | Market, Brand | 1800s |
| `currents_latest_news` | Latest news headlines by category | Market | 600s |
| `currents_brand_sentiment` | Brand/company sentiment analysis from news | Brand | 1800s |

**API Key**: `CURRENTS_API_KEY=<configured>` ✅ Configured

### Twelve Data (`twelvedata_tools.py`) — 4 MCP Tools ✅ LIVE

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `td_time_series` | Stock/forex/crypto time series (OHLCV) from 80+ exchanges | Market, Finance | 300s |
| `td_price_quote` | Real-time price quote | Market | 60s |
| `td_forex_rate` | Real-time forex rate | Finance | 300s |
| `td_market_movers` | Top market gainers/losers | Market | 300s |

**API Key**: `TWELVEDATA_API_KEY=<configured>` ✅ Configured

### Financial Modeling Prep (`fmp_tools.py`) — 4 MCP Tools ✅ LIVE

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `fmp_company_profile` | Company profile (sector, market cap, description) | Market, Finance | 3600s |
| `fmp_key_metrics` | Key financial metrics (P/E, ROE, debt/equity) | Finance | 86400s |
| `fmp_dcf_valuation` | DCF valuation (undervalued/overvalued) | Finance | 1800s |
| `fmp_income_statement` | Income statement (revenue, profit, EPS) | Finance | 86400s |

**API Key**: `FMP_API_KEY=<configured>` ✅ Configured
**Note**: Uses FMP `/stable/` API (v3 endpoints are legacy/403)

### Shodan (`shodan_tools.py`) — 3 MCP Tools ✅ LIVE (InternetDB)

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `shodan_device_search` | Search IoT/ICS/SCADA devices (requires paid plan) | Risk | 1800s |
| `shodan_host_info` | Host info via InternetDB (free, no key needed) | Risk | 3600s |
| `shodan_exploit_search` | Search exploit DB (requires paid plan) | Risk | 86400s |

**API Key**: `SHODAN_API_KEY=<configured>` ✅ Configured
**Note**: `shodan_host_info` uses free InternetDB API; search/exploit require paid membership

### ExchangeRate-API (`exchangerate_tools.py`) — 2 MCP Tools ✅ LIVE

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `exr_latest_rates` | Latest exchange rates for 166+ currencies | Finance | 3600s |
| `exr_pair_conversion` | Convert amount between two currencies | Finance | 1800s |

**API Key**: `EXCHANGERATE_API_KEY=<configured>` ✅ Configured

### GNews (`gnews_tools.py`) — 2 MCP Tools ⚠️ Needs Activation

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `gnews_search` | Search news articles | Brand, Market | 600s |
| `gnews_top_headlines` | Top headlines by category | Brand | 600s |

**API Key**: `GNEWS_API_KEY=<configured>` ⚠️ Needs email activation

### MarketAux (`marketaux_tools.py`) — 3 MCP Tools ✅ LIVE

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `marketaux_news` | Financial news filtered by tickers with sentiment | Market, Brand | 600s |
| `marketaux_sentiment` | Market sentiment scores for tickers | Market | 1800s |
| `marketaux_trending` | Trending/most mentioned tickers | Market | 600s |

**API Key**: `MARKETAUX_API_KEY=<configured>` ✅ Configured

### GraphHopper (`graphhopper_tools.py`) — 3 MCP Tools ✅ LIVE

| Tool Name | Function | Best Agent | Cache TTL |
|-----------|----------|------------|-----------|
| `gh_route_optimize` | Optimized route (distance, ETA) | Logistics, Supply | 3600s |
| `gh_distance_matrix` | Distance/duration matrix between multiple points | Logistics | 3600s |
| `gh_geocode` | Geocode address to coordinates | Logistics | 86400s |

**API Key**: `GRAPHHOPPER_API_KEY=<configured>` ✅ Configured

---

## 3. Complete MCP Tool Inventory (96 Tools)

### By Category

| Category | Count | Tools |
|----------|-------|-------|
| **financial** | 22 | `stock_quote`, `company_profile`, `company_financials`, `forex_rate_finnhub`, `polygon_stock_aggregate`, `polygon_stock_snapshot`, `polygon_forex_rate`, `polygon_market_status`, `polygon_ticker_news`, `td_time_series`, `td_price_quote`, `td_forex_rate`, `td_market_movers`, `fmp_company_profile`, `fmp_key_metrics`, `fmp_dcf_valuation`, `fmp_income_statement`, `marketaux_news`, `marketaux_sentiment`, `marketaux_trending` |
| **commodity** | 7 | `av_commodity_price`, `av_stock_time_series`, `av_economic_indicator`, `av_currency_exchange`, `commodity_price`, `trade_data`, `tariff_lookup` |
| **news** | 13 | `mediastack_news_search`, `mediastack_sources`, `mediastack_historical_news`, `currents_news_search`, `currents_latest_news`, `currents_brand_sentiment`, `news_search`, `newsapi_top_headlines`, `gnews_search`, `gnews_top_headlines` |
| **weather** | 4 | `owm_current_weather`, `owm_weather_forecast`, `owm_weather_alerts`, `owm_air_quality` |
| **climate** | 4 | `noaa_climate_data`, `noaa_storm_events`, `noaa_sea_level`, `noaa_drought_monitor` |
| **cyber** | 7 | `nvd_cve_search`, `nvd_cve_by_cpe`, `nvd_cve_details`, `nvd_recent_cves`, `shodan_device_search`, `shodan_host_info`, `shodan_exploit_search` |
| **geopolitical** | 2 | `gdelt_search_events`, `gdelt_search_gkg` |
| **disaster** | 3 | `gdacs_disaster_alerts`, `weather_current`, `usgs_earthquakes` |
| **economic** | 3 | `fred_commodity_price`, `fred_economic_data`, `worldbank_indicators` |
| **forex** | 5 | `frankfurter_latest_rates`, `frankfurter_historical_rates`, `currency_rate`, `exr_latest_rates`, `exr_pair_conversion` |
| **knowledge** | 6 | `wikipedia_search`, `arxiv_search`, `sec_edgar_search`, `opencorporates_search`, `reddit_search`, `comtrade_trade_data` |
| **shipping** | 3 | `route_optimize`, `port_status`, `freight_rate` |
| **logistics** | 3 | `gh_route_optimize`, `gh_distance_matrix`, `gh_geocode` |
| **supplier** | 3 | `neo4j_query`, `supplier_search`, `contract_lookup` |
| **finance** | 3 | `erp_query`, `insurance_claim` |
| **social** | 3 | `social_sentiment`, `competitor_intel`, `firecrawl_search` |
| **firecrawl** | 3 | `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_search` |
| **rag** | 3 | `rag_query`, `agentic_rag_query`, `graph_rag_v2` |
| **trade** | 3 | `comtrade_trade_data`, `trade_flows`, `tariff_lookup` |

### By MCP Server Group (14 Servers)

| Server Group | Tools | Allowed Agents |
|-------------|-------|---------------|
| `news_geopolitical` | 7 | risk, brand, moderator |
| `shipping_logistics` | 7 | logistics, supply, moderator |
| `erp_inventory` | 6 | supply, finance, moderator |
| `finance_market` | 9 | finance, market, moderator |
| `web_intel` | 6 | brand, risk, market, moderator |
| `rag` | 3 | ALL agents |
| `commodity_prices` | 6 | market, finance, moderator |
| `market_radar` | 15 | market, finance, brand, moderator |
| `climate_risk` | 8 | risk, logistics, moderator |
| `cyber_vulnerability` | 7 | risk, moderator |
| `enhanced_finance` | 11 | market, finance, brand, moderator |
| `forex_backup` | 4 | finance, market, brand, moderator |
| `route_optimization` | 3 | logistics, supply, moderator |

---

## 4. Agent ↔ Source Coverage Matrix

| Agent | Servers | Live Sources | Mock Sources | Total Tools | Coverage Score |
|-------|---------|-------------|-------------|-------------|---------------|
| **Risk Sentinel** | news_geopolitical, web_intel, climate_risk, cyber_vulnerability, enhanced_finance, forex_backup, rag | GDELT, GDACS, NewsAPI, NOAA, NVD, Shodan, OWM | FRED | 46 | ★★★★★ |
| **Supply Optimizer** | erp_inventory, shipping_logistics, route_optimization, rag | Neo4j, GraphHopper | ERP, Shipping | 19 | ★★★☆☆ |
| **Logistics Navigator** | shipping_logistics, climate_risk, route_optimization, rag | OWM, NOAA, USGS, GraphHopper | Port/Freight | 21 | ★★★★☆ |
| **Market Intelligence** | finance_market, commodity_prices, market_radar, web_intel, enhanced_finance, forex_backup, rag | Finnhub, Frankfurter, Alpha Vantage, Polygon, Twelve Data, FMP, MarketAux, Mediastack, Currents | Commodity, Trade | 54 | ★★★★★ |
| **Finance Guardian** | finance_market, commodity_prices, market_radar, erp_inventory, enhanced_finance, forex_backup, rag | Finnhub, Frankfurter, Alpha Vantage, Polygon, Twelve Data, FMP, ExchangeRate-API | ERP, Currency | 54 | ★★★★★ |
| **Brand Protector** | web_intel, news_geopolitical, market_radar, enhanced_finance, forex_backup, rag | Reddit, NewsAPI, Mediastack, Currents, MarketAux, Firecrawl | Social Sentiment | 46 | ★★★★☆ |
| **Moderator** | ALL servers | ALL live sources | ALL mocks | 92 | ★★★★★ |

---

## 5. API Key Reference

### Configured & Working

| Key | Variable | Value (partial) | Source | Status |
|-----|----------|----------------|--------|--------|
| Finnhub | `FINNHUB_API_KEY` | `***` | [finnhub.io](https://finnhub.io) | ✅ LIVE |
| NewsAPI | `NEWSAPI_KEY` | `***` | [newsapi.org](https://newsapi.org) | ✅ LIVE |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | `***` | [alphavantage.co](https://www.alphavantage.co) | ✅ NEW |
| Polygon.io | `POLYGON_API_KEY` | `***` | [polygon.io](https://polygon.io) | ✅ NEW |
| OpenWeatherMap | `OPENWEATHERMAP_API_KEY` | `***` | [openweathermap.org](https://openweathermap.org/api) | ✅ NEW |
| Mediastack | `MEDIASTACK_API_KEY` | `***` | [mediastack.com](https://mediastack.com) | ✅ NEW |
| NOAA | `NOAA_API_KEY` | `***` | [ncdc.noaa.gov](https://www.ncdc.noaa.gov/cdo-web/token) | ✅ NEW |
| NIST NVD | `NIST_NVD_API_KEY` | `***` | [nvd.nist.gov](https://nvd.nist.gov/vuln/data-feeds) | ✅ NEW |
| Currents | `CURRENTS_API_KEY` | `***` | [currentsapi.services](https://currentsapi.services) | ✅ NEW |
| Twelve Data | `TWELVEDATA_API_KEY` | `***` | [twelvedata.com](https://twelvedata.com) | ✅ LIVE |
| FMP | `FMP_API_KEY` | `***` | [financialmodelingprep.com](https://site.financialmodelingprep.com) | ✅ LIVE |
| Shodan | `SHODAN_API_KEY` | `***` | [shodan.io](https://shodan.io) | ✅ LIVE (InternetDB free) |
| ExchangeRate-API | `EXCHANGERATE_API_KEY` | `***` | [exchangerate-api.com](https://exchangerate-api.com) | ✅ LIVE |
| GNews | `GNEWS_API_KEY` | `***` | [gnews.io](https://gnews.io) | ⚠️ Needs activation |
| MarketAux | `MARKETAUX_API_KEY` | `***` | [marketaux.com](https://marketaux.com) | ✅ LIVE |
| GraphHopper | `GRAPHHOPPER_API_KEY` | `***` | [graphhopper.com](https://graphhopper.com) | ✅ LIVE |
| Groq | `GROQ_API_KEY` | Configured | [console.groq.com](https://console.groq.com) | ✅ LIVE |
| Gemini | `GEMINI_API_KEY` | `***` | [ai.google.dev](https://ai.google.dev) | ✅ LIVE |

### Configured but Broken/Needs Fix

| Key | Variable | Issue | Fix |
|-----|----------|-------|-----|
| FRED | `FRED_API_KEY` | Invalid format (needs 32-char lowercase) | Get new key from [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/fred/) |

### No Key Required (Free/Public APIs)

| Source | URL | Notes |
|--------|-----|-------|
| Frankfurter | `frankfurter.app` | ECB forex data, no auth |
| Open-Meteo | `open-meteo.com` | Weather forecasts, no auth |
| USGS Earthquakes | `earthquake.usgs.gov` | Real-time seismic data |
| Wikipedia | `en.wikipedia.org/w/api.php` | MediaWiki API (not REST) |
| World Bank | `api.worldbank.org/v2` | Economic indicators |
| GDACS | `gdacs.org` | Global disaster alerts |
| GDELT | `api.gdeltproject.org` | Geopolitical events (rate-limited) |
| SEC EDGAR | `sec.gov/edgar` | US company filings |
| Arxiv | `export.arxiv.org` | Academic papers (needs `follow_redirects=True`) |
| NOAA Drought Monitor | `usdmdataservices.unl.edu` | Public, no auth |
| NIST NVD (basic) | `services.nvd.nist.gov` | Works without key (slower) |

---

## 6. Recommended Additional Sources

Curated from [public-apis/public-apis](https://github.com/public-apis/public-apis) — only APIs directly relevant to supply chain risk, logistics, finance, and geopolitical monitoring.

### 🔴 HIGH PRIORITY — Directly fills agent gaps

| # | Source | Category | Auth | Free Tier | Best Agent | Why Critical | Signup |
|---|--------|----------|------|-----------|------------|--------------|--------|
| 1 | **ACLED** | Geopolitical Risk | apiKey | Free (academic) | Risk Sentinel | **Conflict zones** — WorldMonitor uses it; Risk Agent has NO real conflict data | [acleddata.com](https://acleddata.com/acess-api/) |
| 2 | **MarineTraffic** | Shipping/Logistics | apiKey | Free tier | Logistics Navigator | **Real vessel tracking** — replaces mock `_port_status` and `_freight_rate` | [marinetraffic.com](https://www.marinetraffic.com/en/p/api) |
| 3 | **Twelve Data** | Finance | apiKey | 800 credits/day | Finance, Market | **Stocks + forex + crypto** — broader than Finnhub, free tier generous | [twelvedata.com](https://twelvedata.com/) |
| 4 | **Financial Modeling Prep** | Finance | apiKey | 250 calls/day | Finance, Market | **Comprehensive financials** — income statements, balance sheets, DCF, ratings | [financialmodelingprep.com](https://site.financialmodelingprep.com/developer/docs) |
| 5 | **OpenSky Network** | Aviation/Logistics | None | Free | Logistics Navigator | **Real-time flight tracking** — ADS-B data, air freight visibility | [opensky-network.org](https://opensky-network.org/apidoc/index.html) |
| 6 | **HaveIBeenPwned** | Cyber/Security | apiKey | Free (limited) | Risk Sentinel | **Data breach detection** — supply chain cyber risk from compromised accounts | [haveibeenpwned.com](https://haveibeenpwned.com/API/v3) |
| 7 | **Shodan** | Cyber/Infrastructure | apiKey | Free (limited) | Risk Sentinel | **Internet-connected device search** — SCADA/ICS exposure detection | [shodan.io](https://developer.shodan.io/) |
| 8 | **ExchangeRate-API** | Currency | apiKey | 1500 req/mo | Finance Guardian | **Backup forex** — more currencies than Frankfurter | [exchangerate-api.com](https://www.exchangerate-api.com) |
| 9 | **GNews** | News | apiKey | 100 req/day | Brand, Market | **Alternative news** — complements NewsAPI + Mediastack | [gnews.io](https://gnews.io/) |
| 10 | **OpenSanctions** | Compliance | apiKey | Free (limited) | Risk, Finance | **Sanctions & PEP screening** — supply chain compliance risk | [opensanctions.org](https://www.opensanctions.org/docs/api/) |

### 🟡 MEDIUM PRIORITY — Expands depth

| # | Source | Category | Auth | Free Tier | Best Agent | Why Useful | Signup |
|---|--------|----------|------|-----------|------------|------------|--------|
| 11 | **UCDP** | Geopolitical | None | Free | Risk Sentinel | **Long-term conflict trends** — complements ACLED | [ucdp.uu.se](https://ucdp.uu.se/downloads/) |
| 12 | **Trading Economics** | Economic | apiKey | Free trial | Market, Finance | **Economic indicators** — GDP, inflation, PMI per country | [tradingeconomics.com](https://tradingeconomics.com/api) |
| 13 | **MarketAux** | Financial News | apiKey | Free tier | Market, Brand | **Financial news with sentiment** — ticker-tagged news | [marketaux.com](https://www.marketaux.com/) |
| 14 | **Carbon Interface** | Environment/ESG | apiKey | Free | Risk, Finance | **Carbon footprint estimation** — ESG/sustainability risk | [carboninterface.com](https://docs.carboninterface.com/) |
| 15 | **OpenAQ** | Air Quality | apiKey | Free | Risk, Logistics | **Global air quality** — complements OWM air quality | [openaq.org](https://docs.openaq.org/) |
| 16 | **GraphHopper** | Routing/Logistics | apiKey | Free tier | Logistics Navigator | **Real route optimization** — replaces mock `_route_optimize` | [graphhopper.com](https://docs.graphhopper.com/) |
| 17 | **Nasdaq Data Link** | Financial | apiKey | Free tier | Finance, Market | **Comprehensive financial + economic data** (formerly Quandl) | [data.nasdaq.com](https://docs.data.nasdaq.com/) |
| 18 | **AviationStack** | Aviation | apiKey | Free tier | Logistics Navigator | **Flight tracking & schedules** — air freight planning | [aviationstack.com](https://aviationstack.com/) |
| 19 | **Censys** | Cyber/Infrastructure | apiKey | Free (limited) | Risk Sentinel | **Internet-wide scanning** — infrastructure exposure | [censys.io](https://search.censys.io/api) |
| 20 | **FRED (fixed key)** | Economic | apiKey | Free | Market, Finance | **Federal Reserve data** — interest rates, GDP, employment | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/fred/) |

### 🟢 NICE TO HAVE — Future expansion

| # | Source | Category | Auth | Free Tier | Best Agent | Why Nice | Signup |
|---|--------|----------|------|-----------|------------|----------|--------|
| 21 | **Dun & Bradstreet** | Supplier | apiKey | Sandbox | Supply Optimizer | **Real Tier-2/3 supplier data** | [developer.dnb.com](https://developer.dnb.com) |
| 22 | **AISStream** | Shipping | apiKey | Free tier | Logistics Navigator | **Global AIS ship data** | [aisstream.com](https://aisstream.com) |
| 23 | **Visual Crossing** | Weather | apiKey | 1000 req/day | Risk, Logistics | **Historical weather + forecasts** | [visualcrossing.com](https://www.visualcrossing.com/weather-api) |
| 24 | **NASA EONET** | Disaster | None | Free | Risk Sentinel | **Natural event tracking** — fires, floods, storms | [eonet.gsfc.nasa.gov](https://eonet.gsfc.nasa.gov/) |
| 25 | **CARTO** | Geospatial | apiKey | Free tier | Logistics, Risk | **Geospatial analytics** — route visualization | [carto.com](https://carto.com/) |
| 26 | **OpenChargeMap** | EV/Logistics | apiKey | Free | Logistics | **EV charging stations** — electric fleet planning | [openchargemap.org](https://openchargemap.org/site/develop/api) |
| 27 | **VirusTotal** | Cyber | apiKey | Free (limited) | Risk Sentinel | **Malware/threat analysis** — supply chain software integrity | [virustotal.com](https://www.virustotal.com/en/documentation/public-api/) |
| 28 | **GreyNoise** | Cyber | apiKey | Free (community) | Risk Sentinel | **Internet noise filtering** — threat intelligence | [greynoise.io](https://docs.greynoise.io/) |
| 29 | **REST Countries** | Geocoding | None | Free | All agents | **Country info** — capital, currency, region, borders | [restcountries.com](https://restcountries.com) |
| 30 | **OpenFIGI** | Finance | apiKey | Free | Finance | **Financial instrument identification** — map tickers to ISIN/LEI | [openfigi.com](https://www.openfigi.com/api) |

---

## 7. Sources by Essential Category Gaps

### Gap 1: Geopolitical Conflict Data (Risk Sentinel has NO real conflict source)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🔴 Critical | **ACLED** | apiKey | **NOT integrated** | `acled_conflict_events`, `acled_conflict_trends` |
| 🟡 Medium | **UCDP** | None | **NOT integrated** | `ucdp_conflict_data`, `ucdp_battle_deaths` |
| 🟢 Nice | **NASA EONET** | None | **NOT integrated** | `eonet_natural_events`, `eonet_categories` |
| ✅ Done | **GDELT** | None | Integrated | `gdelt_search_events`, `gdelt_search_gkg` |
| ✅ Done | **GDACS** | None | Integrated | `gdacs_disaster_alerts` |

### Gap 2: Real Shipping/Vessel Data (Logistics has ALL mock tools)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🔴 Critical | **MarineTraffic** | apiKey | **NOT integrated** | `marinetraffic_vessel_positions`, `marinetraffic_port_calls` |
| 🟡 Medium | **OpenSky Network** | None | **NOT integrated** | `opensky_flights`, `opensky_tracks` |
| 🟡 Medium | **GraphHopper** | apiKey | **NOT integrated** | `graphhopper_route`, `graphhopper_isochrone` |
| 🟡 Medium | **AviationStack** | apiKey | **NOT integrated** | `aviationstack_flights`, `aviationstack_routes` |
| 🟢 Nice | **AISStream** | apiKey | **NOT integrated** | `aisstream_vessel_positions` |
| 🟢 Nice | **BIC-Boxtech** | OAuth | **NOT integrated** | `bic_container_search` |

### Gap 3: Cyber/Infrastructure Threats (Only NVD integrated)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🔴 Critical | **HaveIBeenPwned** | apiKey | **NOT integrated** | `hibp_breached_account`, `hibp_breach_list` |
| 🔴 Critical | **Shodan** | apiKey | **NOT integrated** | `shodan_host_search`, `shodan_exploit_search` |
| 🟡 Medium | **Censys** | apiKey | **NOT integrated** | `censys_host_search`, `censys_certificate_search` |
| 🟡 Medium | **VirusTotal** | apiKey | **NOT integrated** | `vt_file_scan`, `vt_domain_report` |
| 🟢 Nice | **GreyNoise** | apiKey | **NOT integrated** | `greynoise_ip_context`, `greynoise_ip_quick` |
| ✅ Done | **NIST NVD** | apiKey | Integrated | `nvd_cve_search`, `nvd_cve_by_cpe`, `nvd_cve_details`, `nvd_recent_cves` |

### Gap 4: Supplier/Compliance Data (Only Neo4j mock)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🔴 Critical | **OpenSanctions** | apiKey | **NOT integrated** | `opensanctions_search`, `opensanctions_screen_entity` |
| 🟡 Medium | **Dun & Bradstreet** | apiKey | **NOT integrated** | `dnb_company_search`, `dnb_supplier_risk` |
| 🟢 Nice | **OpenCorporates** | apiKey | Integrated (basic) | `opencorporates_search` |

### Gap 5: ESG/Sustainability (No sources at all)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🟡 Medium | **Carbon Interface** | apiKey | **NOT integrated** | `carbon_estimate`, `carbon_fuel_combustion` |
| 🟡 Medium | **OpenAQ** | apiKey | **NOT integrated** | `openaq_latest_measurements`, `openaq_cities` |
| 🟢 Nice | **Climatiq** | apiKey | **NOT integrated** | `climatiq_emission_estimate`, `climatiq_electricity_emission` |

### Gap 6: Financial Depth (Finnhub + Polygon only)

| Priority | Source | Auth | Status | MCP Tools Possible |
|----------|--------|------|--------|-------------------|
| 🟡 Medium | **Twelve Data** | apiKey | **NOT integrated** | `twelvedata_time_series`, `twelvedata_forex_pairs` |
| 🟡 Medium | **Financial Modeling Prep** | apiKey | **NOT integrated** | `fmp_income_statement`, `fmp_dcf`, `fmp_rating` |
| 🟡 Medium | **Nasdaq Data Link** | apiKey | **NOT integrated** | `nasdaq_datasets`, `nasdaq_time_series` |
| 🟡 Medium | **OpenFIGI** | apiKey | **NOT integrated** | `openfigi_mapping` |
| 🟢 Nice | **MarketAux** | apiKey | **NOT integrated** | `marketaux_news_sentiment` |

---

## 8. Integration Status Summary

### Current State

```
Total MCP Tools:     75
Live Data Sources:   19 (with real API calls)
Mock-Only Sources:   8  (returning hardcoded data)
Internal Sources:    4  (Neo4j, Firecrawl, ChromaDB, Neon PG)
API Keys Configured: 11 (all working)
API Keys Broken:     1  (FRED - invalid format)
No Key Required:     11 (free public APIs)
```

### Before vs After Day 7

| Metric | Before (Day 6) | After (Day 7) | Delta |
|--------|----------------|---------------|-------|
| Total MCP Tools | 45 | 75 | +30 (+67%) |
| Live Data Sources | 12 | 19 | +7 (+58%) |
| MCP Server Groups | 6 | 10 | +4 (+67%) |
| API Keys | 4 | 11 | +7 |
| Agent Coverage (avg tools/agent) | ~15 | ~33 | +18 (+120%) |

### Remaining Gaps (Priority Order)

1. **Geopolitical Conflict** — Need ACLED + UCDP (Risk Agent has no real conflict data)
2. **Real Shipping Data** — Need MarineTraffic + OpenSky (Logistics has all mock tools)
3. **Cyber Threat Intel** — Need HIBP + Shodan (only NVD currently)
4. **Supplier Compliance** — Need OpenSanctions (no sanctions screening)
5. **ESG/Sustainability** — Need Carbon Interface + OpenAQ (zero coverage)
6. **Financial Depth** — Need Twelve Data + FMP (only Finnhub + Polygon)

### Recommended Next Actions (Day 8)

1. **Fix FRED key** → Get proper 32-char key from [fred.stlouisfed.org](https://fred.stlouisfed.org) → instant upgrade
2. **Add ACLED** → Register at [acleddata.com](https://acleddata.com/acess-api/) → `acled_tools.py`
3. **Add MarineTraffic** → Register at [marinetraffic.com](https://www.marinetraffic.com/en/p/api) → `marinetraffic_tools.py`
4. **Add OpenSky Network** → No key needed → `opensky_tools.py`
5. **Add HaveIBeenPwned** → Register at [haveibeenpwned.com](https://haveibeenpwned.com/API/v3) → `hibp_tools.py`
6. **Add Twelve Data** → Register at [twelvedata.com](https://twelvedata.com) → `twelvedata_tools.py`
7. **Add GraphHopper** → Register at [graphhopper.com](https://docs.graphhopper.com/) → `graphhopper_tools.py`

---

*Document generated from project source code analysis + [public-apis/public-apis](https://github.com/public-apis/public-apis) catalog (1,400+ free APIs).*


