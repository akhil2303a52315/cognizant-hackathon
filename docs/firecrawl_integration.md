# Firecrawl MCP Integration

## Overview
Self-hosted Firecrawl provides **unlimited web scraping** to all 7 AI agents. Runs as Docker instance at `http://localhost:3002`.

## 6 MCP Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `web_scrape` | Scrape URL → markdown | News, supplier pages |
| `web_crawl` | Crawl site with depth/limits | Full site analysis |
| `web_search` | Web search → scraped results | Market intel, risk signals |
| `web_extract_data` | Extract structured JSON | Supplier portals, specs |
| `web_scrape_supplier` | Supplier site → certs, capabilities | Alternate sourcing |
| `web_scrape_news` | News article → title, author, content | Risk & Brand monitoring |

## Agent Access (all 7 agents)

| Agent | Tools | Firecrawl Use |
|-------|-------|---------------|
| Risk | 49 | Risk intel, news, supplier risk pages |
| Supply | 28 | Supplier websites, certifications |
| Logistics | 30 | Port status, customs, carriers |
| Market | 57 | Competitor sites, market reports |
| Finance | 63 | Financial reports, regulatory filings |
| Brand | 49 | News articles, competitor brands |
| Moderator | 95 | Additional context gathering |

## Error Handling

- **Retry**: 2 retries with exponential backoff on connection/timeout/5xx errors
- **ConnectError**: Mock fallback + "Start Firecrawl: cd firecrawl && docker compose up -d"
- **Timeout**: Mock fallback + "Page too large — reduce parameters"
- **4xx errors**: No retry, immediate mock fallback
- **LLM extract fail**: Falls back to plain scrape with raw markdown
- **Not configured**: Mock with guidance to set FIRECRAWL_BASE_URL

## Setup

```bash
# 1. Start Firecrawl
cd firecrawl && docker compose up -d

# 2. Configure .env
FIRECRAWL_BASE_URL=http://localhost:3002

# 3. Start everything
start-all.bat
```

## Docker Containers (5 services)
- `firecrawl-api-1` — API on port 3002
- `firecrawl-playwright-service-1` — Browser automation
- `firecrawl-redis-1` — Job queue
- `firecrawl-rabbitmq-1` — Message broker
- `firecrawl-nuq-postgres-1` — Database

## LLM Extract (optional)
Set in `firecrawl/.env`:
```
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
OPENAI_API_KEY=<your-gemini-key>
MODEL_NAME=gemini-2.0-flash
```

## RAG Integration
- `load_from_url()` → uses `web_scrape`
- `load_from_crawl()` → uses `web_crawl`
- `social_sentiment` → uses `web_search` internally
