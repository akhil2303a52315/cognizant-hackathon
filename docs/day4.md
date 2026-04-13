# Day 4 Development — MCP Tool Integration

> **Date:** Day 4 (Apr 15)
> **Focus:** MCP servers + secure tool calling in every agent
> **Status:** ✅ Complete

---

## Overview

Day 4 built the Model Context Protocol (MCP) tool infrastructure: a central registry, sandbox validation, Redis caching, audit logging, LangChain integration, and 22 original tools across 7 agent domains. Each tool is sandboxed, rate-limited, and follows least-privilege access. On Day 6, 23 additional real-data tools were added (total: 45).

---

## MCP Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     MCP TOOL SERVER                               │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Registry  │  │ Sandbox  │  │  Cache   │  │  Audit   │       │
│  │ (45 tools)│  │ Validate │  │ (Redis)  │  │ (Neon PG)│       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘       │
│        │              │              │              │              │
│        └──────────────┴──────────────┴──────────────┘           │
│                            │                                      │
│                   ┌────────▼────────┐                           │
│                   │  MCP FastAPI     │                           │
│                   │  Server          │                           │
│                   │  /tools          │                           │
│                   │  /tools/{name}   │                           │
│                   │  /tools/{name}/invoke │                      │
│                   │  /audit          │                           │
│                   │  /health         │                           │
│                   └─────────────────┘                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              LANGCHAIN INTEGRATION                          ││
│  │  MCP Tools → LangChain Tool objects → Agent tool calling   ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## MCP Module Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `backend/mcp/registry.py` | Central tool registry (45 tools) | `register_tool`, `list_tools`, `get_tool`, `invoke_tool`, `_register_all_tools` |
| `backend/mcp/server.py` | FastAPI MCP server | `/tools`, `/tools/{name}`, `/tools/{name}/invoke`, `/audit`, `/health` |
| `backend/mcp/sandbox.py` | Input validation + security | `validate_cypher`, `validate_sql`, `detect_prompt_injection`, `redact_pii`, `validate_inputs` |
| `backend/mcp/cache.py` | Redis result caching | `cache_get`, `cache_set`, `cache_delete` |
| `backend/mcp/audit.py` | Tool invocation audit logging | `audit_log` (writes to Neon PG) |
| `backend/mcp/langchain_integration.py` | MCP → LangChain Tool bridge | `get_langchain_tools`, `_sync_wrapper`, `_async_wrapper` |

---

## Tool Registration System

### Registry Pattern

```python
# backend/mcp/registry.py

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict          # JSON Schema for input validation
    handler: Callable | None     # Async function that executes the tool
    category: str = "general"   # Tool category for grouping
    cache_ttl: int = 3600       # Cache time-to-live in seconds

def register_tool(name, description, input_schema, handler, category, cache_ttl):
    _registry[name] = ToolDefinition(...)

async def invoke_tool(name, params):
    # 1. Validate inputs via sandbox
    violations = validate_inputs(name, params)
    if violations:
        raise PermissionError(...)
    # 2. Execute handler
    return await t.handler(params)
```

### Tool Registration Flow

```python
# _register_all_tools() — called on app startup

# Original tools (7 modules, register() pattern)
for reg in [reg_news, reg_supplier, reg_shipping, reg_commodity, reg_finance, reg_social, reg_firecrawl]:
    reg()

# New real-data tools (7 modules, TOOLS list pattern)
for tool_list, category in [
    (gdelt_tools, "geopolitical"),
    (finnhub_tools, "financial"),
    (fred_tools, "economic"),
    (frankfurter_tools, "forex"),
    (weather_tools, "disaster"),
    (knowledge_tools, "knowledge"),
    (trade_tools, "trade"),
]:
    for t in tool_list:
        register_tool(name=t["name"], ...)

# RAG tool (special handler)
register_tool(name="rag_query", handler=_rag_query_handler, category="rag")
```

---

## MCP Server Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/mcp/tools` | GET | List all registered tools | MCP Key |
| `/mcp/tools/{name}` | GET | Get tool details + input schema | MCP Key |
| `/mcp/tools/{name}/invoke` | POST | Execute a tool with params | MCP Key |
| `/mcp/audit` | GET | View audit logs (last 50) | MCP Key |
| `/mcp/health` | GET | Health check + tool count | None |

### Invoke Flow

```
POST /mcp/tools/stock_quote/invoke
Headers: X-MCP-API-Key: dev-mcp-key
Body: {"symbol": "TSM"}

→ Sandbox validation
→ Cache check (Redis: mcp:stock_quote:<sha256>)
→ If cached: return cached result + audit log
→ If not cached: invoke handler → cache result → audit log → return
```

---

## Sandbox & Security

### Input Validation

```python
# backend/mcp/sandbox.py

def validate_inputs(tool_name, params):
    violations = []

    # Cypher write protection (Neo4j)
    if tool_name == "neo4j_query":
        violations.extend(validate_cypher(query))
        # Blocks: CREATE, MERGE, DELETE, SET, DROP, CALL

    # SQL write protection (ERP)
    if tool_name == "erp_query":
        violations.extend(validate_sql(query))
        # Blocks: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE

    # Prompt injection detection (all tools)
    for key, value in params.items():
        violations.extend(detect_prompt_injection(value))
        # Detects: "ignore previous instructions", "you are now", "jailbreak", etc.

    return violations
```

### Prompt Injection Patterns

| Pattern | Category |
|---------|----------|
| `ignore\s+(all\s+)?previous\s+instructions` | Role switching |
| `you\s+are\s+now` | Role switching |
| `system\s*:\s*` | System prompt extraction |
| `forget\s+(everything\|all)` | Instruction override |
| `override\s+(safety\|security\|rules)` | Security bypass |
| `jailbreak` | Known attack |
| `pretend\s+you\s+are` | Role manipulation |

### PII Redaction

```python
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}

def redact_pii(text):
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text
```

---

## Caching Strategy

### Redis Cache

```python
# Key format: mcp:{tool_name}:{sha256(sorted_params)}
# TTL: per-tool (default 3600s = 1 hour)

async def cache_get(key):
    data = await redis.get(key)
    return json.loads(data) if data else None

async def cache_set(key, value, ttl):
    await redis.setex(key, ttl, json.dumps(value))
```

### Cache TTL by Category

| Category | Default TTL | Reason |
|----------|------------|---------|
| News/Geopolitical | 5 min | Rapidly changing |
| Social sentiment | 3 min | Real-time feeds |
| Stock quotes | 30 sec | Market data |
| Forex rates | 30 min | ECB daily update |
| Commodity prices | 10 min | Moderate change |
| Weather | 10 min | Hourly updates |
| Earthquakes | 30 min | Event-driven |
| Trade data | 1 hour | Slow-changing |
| RAG queries | 5 min | Document-based |
| General | 1 hour | Default |

---

## Audit Logging

### Schema

```sql
CREATE TABLE mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent VARCHAR(30) NOT NULL,
    tool VARCHAR(50) NOT NULL,
    params JSONB,
    result_summary TEXT,
    latency_ms INT,
    was_cached BOOLEAN DEFAULT false,
    sandbox_violations TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Audit Record

Every tool invocation creates an audit record with:
- **agent**: Which agent called the tool (from `X-Agent-Name` header)
- **tool**: Tool name invoked
- **input_hash**: SHA256 of sorted params (no raw data stored for security)
- **latency_ms**: Execution time in milliseconds
- **was_cached**: Whether result came from Redis cache
- **sandbox_violations**: Any blocked operations (empty if none)

---

## LangChain Integration

```python
# backend/mcp/langchain_integration.py

def get_langchain_tools() -> list[Tool]:
    """Convert all MCP tools to LangChain Tool objects for agent use."""
    tools = []
    for t in list_tools():
        tool = Tool(
            name=t["name"],
            description=t["description"],
            func=_sync_wrapper(t["name"]),      # sync fallback
            coroutine=_async_wrapper(t["name"]), # async preferred
        )
        tools.append(tool)
    return tools
```

This bridge allows the LangGraph council agents to call MCP tools natively via LangChain's `Tool` interface while the MCP server handles validation, caching, and auditing.

---

## Original Tool Files (Day 4)

| File | Tools | Agent | External API |
|------|-------|-------|-------------|
| `news_tools.py` | `news_search` | risk | NewsAPI + Firecrawl |
| `supplier_tools.py` | `neo4j_query`, `supplier_search`, `contract_lookup` | supply | Neo4j |
| `shipping_tools.py` | `route_optimize`, `port_status`, `freight_rate` | logistics | OR-Tools |
| `commodity_tools.py` | `commodity_price`, `trade_data`, `tariff_lookup` | market | FRED/Comtrade |
| `finance_tools.py` | `erp_query`, `currency_rate`, `insurance_claim` | finance | Exchange API |
| `social_tools.py` | `social_sentiment`, `competitor_ads`, `content_generate` | brand | Reddit/LLM |
| `firecrawl_tools.py` | `firecrawl_scrape`, `web_search` | all | Firecrawl |

### Tool Registration Pattern (Original)

```python
# Each original tool file has a register() function

def register():
    register_tool(
        name="news_search",
        description="Search for news articles related to supply chain",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "date_range": {"type": "string", "description": "Date range (1d, 7d, 30d)", "default": "7d"},
            },
            "required": ["query"],
        },
        handler=_news_search,
        category="news",
        cache_ttl=300,
    )
```

---

## New Real-Data Tool Files (Day 6 Extension)

| File | Tools | Category | API |
|------|-------|----------|-----|
| `gdelt_tools.py` | `gdelt_events`, `gdelt_tone` | geopolitical | GDELT |
| `finnhub_tools.py` | `stock_quote`, `company_profile`, `company_financials` | financial | Finnhub |
| `fred_tools.py` | `fred_commodity_price`, `economic_indicator` | economic | FRED + Yahoo Finance |
| `frankfurter_tools.py` | `exchange_rate`, `historical_rate` | forex | Frankfurter |
| `weather_tools.py` | `weather_forecast`, `earthquake_check`, `disaster_alerts` | disaster | Open-Meteo + USGS + GDACS |
| `knowledge_tools.py` | `wikipedia_search`, `wikipedia_summary`, `arxiv_search`, `reddit_sentiment` | knowledge | MediaWiki + Arxiv + Reddit |
| `trade_tools.py` | `trade_flows`, `sec_filing`, `opencorporates_search` | trade | UN Comtrade + SEC + OpenCorporates |

### Tool Registration Pattern (New)

```python
# New tools use a TOOLS list exported from the module

TOOLS = [
    {
        "name": "stock_quote",
        "description": "Get real-time stock quote for a symbol",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"},
            },
            "required": ["symbol"],
        },
        "handler": _stock_quote,
        "cache_ttl": 30,
    },
    ...
]
```

---

## Mock Fallback Strategy

Every tool follows this pattern to ensure the demo never breaks:

```python
async def _tool_handler(params):
    api_key = _get_key()  # from backend.config.settings or os.getenv
    if not api_key:
        return _mock_response(params)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, params={...})
            if resp.status_code != 200:
                return _mock_response(params)
            data = resp.json()
            data["mock"] = False
            return data
    except Exception as e:
        logger.warning(f"API call failed: {e}")
        return _mock_response(params)

def _mock_response(params):
    return {..., "mock": True, "error": "API unavailable"}
```

The `mock: true/false` flag lets the frontend display warnings when fallback data is used.

---

## Day 4 Deliverables ✅

- [x] Central tool registry with `register_tool` + `invoke_tool`
- [x] FastAPI MCP server with 5 endpoints
- [x] Sandbox validation (Cypher, SQL, prompt injection, PII)
- [x] Redis result caching with per-tool TTL
- [x] Audit logging to Neon PostgreSQL
- [x] LangChain Tool bridge for agent integration
- [x] 7 original tool modules (22 tools)
- [x] `rag_query` MCP tool for all agents
- [x] Mock fallback strategy for every tool
- [x] MCP API key authentication (separate from main API key)
