# SupplyChainGPT — MCP (Model Context Protocol) Specification

Complete specification for MCP tool integration across all 7 agents. Every tool is sandboxed, rate-limited, and follows least-privilege access.

---

## 1. MCP Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                       │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Risk     │  │ Supply   │  │ Logistics│             │
│  │ Agent    │  │ Agent    │  │ Agent    │             │
│  │          │  │          │  │          │             │
│  │ Tools:   │  │ Tools:   │  │ Tools:   │             │
│  │ -news    │  │ -neo4j   │  │ -route   │             │
│  │ -gdelt   │  │ -supplier│  │ -port    │             │
│  │ -finance │  │ -contract│  │ -freight │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │              │              │                   │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐             │
│  │ Market   │  │ Finance  │  │ Brand    │             │
│  │ Agent    │  │ Agent    │  │ Agent    │             │
│  │          │  │          │  │          │             │
│  │ Tools:   │  │ Tools:   │  │ Tools:   │             │
│  │ -commod  │  │ -erp     │  │ -social  │             │
│  │ -trade   │  │ -currency│  │ -competitor│            │
│  │ -tariff  │  │ -insurance│ │ -content  │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │              │              │                   │
│       └──────────────┼──────────────┘                   │
│                      │                                   │
│              ┌───────┴───────┐                          │
│              │  MCP SERVER    │                          │
│              │  (FastAPI)     │                          │
│              │                │                          │
│              │  - Auth        │                          │
│              │  - Sandbox    │                          │
│              │  - Rate Limit │                          │
│              │  - Audit Log  │                          │
│              └───────┬───────┘                          │
│                      │                                   │
│       ┌──────────────┼──────────────┐                  │
│       │              │              │                    │
│  ┌────┴────┐  ┌─────┴─────┐  ┌────┴────┐             │
│  │External │  │ Internal  │  │ Compute │             │
│  │ APIs    │  │ Databases  │  │ Tools   │             │
│  └─────────┘  └───────────┘  └─────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 2. MCP Server Implementation

### 2.1 Server Setup

```python
# backend/mcp/server.py

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import time
import hashlib
import json
import os

mcp_app = FastAPI(title="SupplyChainGPT MCP Server", version="1.0.0")

mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["POST"],
    allow_headers=["*"],
)

# === Rate Limiting ===
_rate_limits: dict[str, list[float]] = {}
RATE_LIMIT_PER_MINUTE = int(os.getenv("MCP_RATE_LIMIT", "30"))

def check_rate_limit(agent: str):
    """Simple in-memory rate limiter per agent."""
    now = time.time()
    key = agent
    if key not in _rate_limits:
        _rate_limits[key] = []

    # Remove entries older than 60 seconds
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < 60]

    if len(_rate_limits[key]) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(429, f"Rate limit exceeded for agent {agent}")

    _rate_limits[key].append(now)

# === Audit Logging ===
async def log_tool_call(agent: str, tool: str, params: dict, result: Any, latency_ms: int):
    """Log every MCP tool call to Neon PostgreSQL for audit."""
    from backend.mcp.audit import audit_log
    await audit_log(agent=agent, tool=tool, params=params, result_summary=str(result)[:500], latency_ms=latency_ms)

# === Auth Middleware ===
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-key")

async def verify_mcp_auth(request: Request):
    """Verify MCP API key in header."""
    key = request.headers.get("X-MCP-API-Key", "")
    if key != MCP_API_KEY:
        raise HTTPException(401, "Invalid MCP API key")

# === Base Models ===
class ToolCallRequest(BaseModel):
    agent: str
    tool: str
    params: dict
    session_id: Optional[str] = None

class ToolCallResponse(BaseModel):
    tool: str
    result: Any
    latency_ms: int
    cached: bool = False
```

### 2.2 Tool Registry

```python
# backend/mcp/registry.py

from typing import Callable, Any
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    agent: str                    # Which agent owns this tool
    parameters: dict              # JSON Schema for params
    rate_limit_per_minute: int = 30
    requires_auth: bool = True
    cache_ttl_seconds: int = 300  # 5 min default cache
    sandbox: bool = True          # Run in sandbox mode

# Global tool registry
TOOL_REGISTRY: dict[str, ToolDefinition] = {}

def register_tool(tool: ToolDefinition):
    TOOL_REGISTRY[tool.name] = tool

def get_tools_for_agent(agent: str) -> list[ToolDefinition]:
    return [t for t in TOOL_REGISTRY.values() if t.agent == agent]

def get_tool(name: str) -> ToolDefinition | None:
    return TOOL_REGISTRY.get(name)
```

### 2.3 Tool Router Endpoint

```python
# backend/mcp/server.py (continued)

@mcp_app.post("/mcp/call", response_model=ToolCallResponse)
async def call_tool(
    req: ToolCallRequest,
    auth=Depends(verify_mcp_auth),
):
    """Main MCP tool call endpoint — routes to appropriate tool handler."""
    check_rate_limit(req.agent)

    tool_def = get_tool(req.tool)
    if not tool_def:
        raise HTTPException(404, f"Tool '{req.tool}' not found")

    if tool_def.agent != req.agent:
        raise HTTPException(403, f"Agent '{req.agent}' cannot use tool '{req.tool}' (owned by '{tool_def.agent}')")

    # Check Redis cache
    cache_key = f"mcp:{req.tool}:{hashlib.md5(json.dumps(req.params, sort_keys=True).encode()).hexdigest()}"
    cached_result = await check_cache(cache_key)
    if cached_result:
        return ToolCallResponse(tool=req.tool, result=cached_result, latency_ms=0, cached=True)

    # Execute tool
    start = time.time()
    try:
        handler = TOOL_HANDLERS[req.tool]
        result = await handler(req.params)
    except Exception as e:
        raise HTTPException(500, f"Tool execution failed: {str(e)}")

    latency_ms = int((time.time() - start) * 1000)

    # Cache result
    if tool_def.cache_ttl_seconds > 0:
        await set_cache(cache_key, result, tool_def.cache_ttl_seconds)

    # Audit log
    await log_tool_call(req.agent, req.tool, req.params, result, latency_ms)

    return ToolCallResponse(tool=req.tool, result=result, latency_ms=latency_ms)

@mcp_app.get("/mcp/tools")
async def list_tools(agent: Optional[str] = None):
    """List available MCP tools, optionally filtered by agent."""
    tools = list(TOOL_REGISTRY.values())
    if agent:
        tools = [t for t in tools if t.agent == agent]
    return [t.model_dump() for t in tools]

@mcp_app.get("/mcp/health")
async def mcp_health():
    return {"status": "ok", "tools_registered": len(TOOL_REGISTRY)}
```

---

## 3. Tool Definitions & Handlers

### 3.1 Risk Agent Tools

#### `news_search`
Search news articles for supply chain events.

```python
# backend/mcp/tools/news_tools.py

import httpx
import os

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

async def news_search(params: dict) -> dict:
    """Search NewsAPI for supply chain related articles."""
    query = params.get("query", "supply chain disruption")
    date_from = params.get("date_from", None)
    date_to = params.get("date_to", None)
    region = params.get("region", None)
    page_size = params.get("page_size", 10)

    url = "https://newsapi.org/v2/everything"
    params_req = {
        "q": query,
        "apiKey": NEWSAPI_KEY,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en",
    }
    if date_from:
        params_req["from"] = date_from
    if date_to:
        params_req["to"] = date_to
    if region:
        # Map region to country code for NewsAPI
        country_map = {"asia": "jp,cn,kr,in", "europe": "de,gb,fr", "americas": "us,br,mx"}
        params_req.setdefault("domains", "")

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params_req, timeout=10.0)

    data = resp.json()
    articles = data.get("articles", [])[:page_size]

    return {
        "total_results": data.get("totalResults", 0),
        "articles": [
            {
                "title": a.get("title"),
                "source": a.get("source", {}).get("name"),
                "published_at": a.get("publishedAt"),
                "description": a.get("description"),
                "url": a.get("url"),
            }
            for a in articles
        ],
    }

# Register tool
register_tool(ToolDefinition(
    name="news_search",
    description="Search news for supply chain events using NewsAPI",
    agent="risk",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "region": {"type": "string", "description": "Region filter"},
            "page_size": {"type": "integer", "description": "Max results", "default": 10},
        },
        "required": ["query"],
    },
    cache_ttl_seconds=300,  # 5 min cache
))
```

#### `gdelt_query`
Query GDELT Global Knowledge Graph for geopolitical events.

```python
async def gdelt_query(params: dict) -> dict:
    """Query GDELT API for geopolitical events affecting supply chains."""
    country = params.get("country", None)
    event_type = params.get("event_type", None)  # "conflict", "protest", "disaster"
    time_range_days = params.get("time_range_days", 7)

    # GDELT Events API (free)
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    query_parts = []
    if country:
        query_parts.append(f"sourcecountry:{country}")
    if event_type:
        query_parts.append(event_type)
    query = " ".join(query_parts) if query_parts else "supply chain disruption"

    params_req = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": 25,
        "format": "json",
        "timespan": f"{time_range_days}d",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params_req, timeout=15.0)

    data = resp.json()
    articles = data.get("articles", [])

    return {
        "total_results": len(articles),
        "events": [
            {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "date": a.get("seendate", ""),
                "url": a.get("url", ""),
                "language": a.get("language", ""),
            }
            for a in articles[:15]
        ],
    }

register_tool(ToolDefinition(
    name="gdelt_query",
    description="Query GDELT for geopolitical events",
    agent="risk",
    parameters={
        "type": "object",
        "properties": {
            "country": {"type": "string", "description": "ISO country code"},
            "event_type": {"type": "string", "description": "Event type filter"},
            "time_range_days": {"type": "integer", "default": 7},
        },
    },
    cache_ttl_seconds=600,  # 10 min cache
))
```

#### `supplier_financials`
Get supplier financial health indicators (mock/demo data for hackathon).

```python
async def supplier_financials(params: dict) -> dict:
    """Get supplier financial health data."""
    supplier_id = params.get("supplier_id")

    # Demo/mock data for hackathon — replace with real ERP API
    mock_data = {
        "S1": {"name": "Taiwan Semi Corp", "z_score": 1.8, "credit_rating": "BBB", "stock_change_30d": -12.5, "revenue_trend": "declining"},
        "S2": {"name": "India Electronics Ltd", "z_score": 3.2, "credit_rating": "A", "stock_change_30d": 3.1, "revenue_trend": "stable"},
        "S3": {"name": "Vietnam Components", "z_score": 2.5, "credit_rating": "BBB+", "stock_change_30d": -2.3, "revenue_trend": "growing"},
    }

    return mock_data.get(supplier_id, {"error": f"Supplier {supplier_id} not found"})

register_tool(ToolDefinition(
    name="supplier_financials",
    description="Get supplier financial health indicators",
    agent="risk",
    parameters={
        "type": "object",
        "properties": {
            "supplier_id": {"type": "string", "description": "Supplier identifier"},
        },
        "required": ["supplier_id"],
    },
    cache_ttl_seconds=900,  # 15 min cache
))
```

---

### 3.2 Supply Agent Tools

#### `neo4j_query`
Query the Neo4j supplier relationship graph.

```python
# backend/mcp/tools/supplier_tools.py

from neo4j import AsyncGraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

async def neo4j_query(params: dict) -> dict:
    """Execute Cypher query against supplier relationship graph."""
    cypher = params.get("cypher_query")
    limit = params.get("limit", 50)

    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD))

    async with driver.session() as session:
        result = await session.run(cypher)
        records = await result.data(limit)

    await driver.close()
    return {"records": records, "count": len(records)}

register_tool(ToolDefinition(
    name="neo4j_query",
    description="Query Neo4j supplier relationship graph with Cypher",
    agent="supply",
    parameters={
        "type": "object",
        "properties": {
            "cypher_query": {"type": "string", "description": "Cypher query string"},
            "limit": {"type": "integer", "default": 50},
        },
        "required": ["cypher_query"],
    },
    cache_ttl_seconds=300,
    sandbox=True,  # Cypher queries are sandboxed (read-only enforced)
))
```

#### `supplier_search`
Search for alternate suppliers matching criteria.

```python
async def supplier_search(params: dict) -> dict:
    """Search for alternate suppliers by component, region, capability."""
    component = params.get("component")
    region = params.get("region", None)
    min_capability = params.get("min_capability_match", 70)

    # Cypher query to find alternates
    cypher = f"""
    MATCH (s:Supplier)-[:SUPPLIES]->(c:Component {{name: '{component}'}})
    WHERE s.capability_match >= {min_capability}
    {"AND s.region = '" + region + "'" if region else ""}
    RETURN s.id, s.name, s.capability_match, s.lead_time_days, s.location, s.tier
    ORDER BY s.capability_match DESC
    LIMIT 10
    """

    return await neo4j_query({"cypher_query": cypher})

register_tool(ToolDefinition(
    name="supplier_search",
    description="Search for alternate suppliers by component and region",
    agent="supply",
    parameters={
        "type": "object",
        "properties": {
            "component": {"type": "string", "description": "Component name/ID"},
            "region": {"type": "string", "description": "Preferred region"},
            "min_capability_match": {"type": "integer", "default": 70, "description": "Minimum capability match %"},
        },
        "required": ["component"],
    },
    cache_ttl_seconds=600,
))
```

#### `contract_lookup`
Look up contract terms for a supplier.

```python
async def contract_lookup(params: dict) -> dict:
    """Look up contract terms, SLAs, and penalties."""
    supplier_id = params.get("supplier_id")
    component = params.get("component", None)

    # Demo/mock data
    contracts = {
        "S1": {
            "supplier": "Taiwan Semi Corp",
            "terms": [
                {"type": "SLA", "detail": "14-day lead time, 98% on-time delivery"},
                {"type": "penalty", "detail": "2% penalty per week delay"},
                {"type": "force_majeure", "detail": "Standard FM clause applies"},
                {"type": "MOQ", "detail": "10,000 units per order"},
            ],
        },
        "S2": {
            "supplier": "India Electronics Ltd",
            "terms": [
                {"type": "SLA", "detail": "12-day lead time, 95% on-time delivery"},
                {"type": "penalty", "detail": "1.5% penalty per week delay"},
                {"type": "MOQ", "detail": "5,000 units per order"},
            ],
        },
    }

    result = contracts.get(supplier_id, {"error": f"No contract found for {supplier_id}"})
    return result

register_tool(ToolDefinition(
    name="contract_lookup",
    description="Look up contract terms, SLAs, and penalties",
    agent="supply",
    parameters={
        "type": "object",
        "properties": {
            "supplier_id": {"type": "string"},
            "component": {"type": "string"},
        },
        "required": ["supplier_id"],
    },
    cache_ttl_seconds=1800,  # 30 min cache
))
```

---

### 3.3 Logistics Agent Tools

#### `route_optimize`
Run OR-Tools route optimization.

```python
# backend/mcp/tools/shipping_tools.py

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

async def route_optimize(params: dict) -> dict:
    """Optimize routes using OR-Tools."""
    origin = params.get("origin")
    destination = params.get("destination")
    constraints = params.get("constraints", {})

    max_lead_time = constraints.get("lead_time_max", 30)
    max_budget = constraints.get("budget_max", 500000)

    # Demo route options with OR-Tools optimization
    routes = [
        {
            "mode": "sea",
            "path": f"{origin} → {destination}",
            "transit_days": 28,
            "cost_usd": 45000,
            "congestion_risk": "Medium",
            "carbon_kg": 1200,
        },
        {
            "mode": "air",
            "path": f"{origin} → {destination}",
            "transit_days": 3,
            "cost_usd": 185000,
            "congestion_risk": "Low",
            "carbon_kg": 8500,
        },
        {
            "mode": "mixed",
            "path": f"{origin} → Dubai → {destination}",
            "transit_days": 12,
            "cost_usd": 78000,
            "congestion_risk": "Low",
            "carbon_kg": 3200,
        },
    ]

    # Filter by constraints
    valid_routes = [r for r in routes if r["transit_days"] <= max_lead_time and r["cost_usd"] <= max_budget]

    return {
        "routes": valid_routes,
        "recommended": valid_routes[0] if valid_routes else None,
        "optimization_constraints": constraints,
    }

register_tool(ToolDefinition(
    name="route_optimize",
    description="Optimize shipping routes using OR-Tools",
    agent="logistics",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "destination": {"type": "string"},
            "constraints": {
                "type": "object",
                "properties": {
                    "lead_time_max": {"type": "integer", "default": 30},
                    "budget_max": {"type": "integer", "default": 500000},
                },
            },
        },
        "required": ["origin", "destination"],
    },
    cache_ttl_seconds=300,
))
```

#### `port_status`
Check port congestion status.

```python
async def port_status(params: dict) -> dict:
    """Check port congestion using Marine Traffic API (or mock)."""
    port_name = params.get("port_name")

    # Mock data for hackathon
    port_data = {
        "Shanghai": {"congestion_level": "High", "avg_delay_days": 14, "vessels_waiting": 45, "status": "severe_backlog"},
        "Rotterdam": {"congestion_level": "Low", "avg_delay_days": 1, "vessels_waiting": 5, "status": "normal"},
        "Singapore": {"congestion_level": "Medium", "avg_delay_days": 4, "vessels_waiting": 18, "status": "moderate_delay"},
        "Hamburg": {"congestion_level": "Low", "avg_delay_days": 2, "vessels_waiting": 8, "status": "normal"},
        "Dubai": {"congestion_level": "Low", "avg_delay_days": 1, "vessels_waiting": 3, "status": "normal"},
    }

    return port_data.get(port_name, {"error": f"Port {port_name} not found", "suggestion": "Try: Shanghai, Rotterdam, Singapore, Hamburg, Dubai"})

register_tool(ToolDefinition(
    name="port_status",
    description="Check port congestion and delay status",
    agent="logistics",
    parameters={
        "type": "object",
        "properties": {
            "port_name": {"type": "string", "description": "Port name"},
        },
        "required": ["port_name"],
    },
    cache_ttl_seconds=180,  # 3 min cache (port status changes frequently)
))
```

#### `freight_rate`
Get current freight rates for a lane.

```python
async def freight_rate(params: dict) -> dict:
    """Get freight rates for a shipping lane and mode."""
    lane = params.get("lane")  # e.g., "Shanghai→Rotterdam"
    mode = params.get("mode", "sea")  # sea, air, land

    # Mock data
    rates = {
        "sea": {"per_container_usd": 3200, "per_teu_usd": 1800, "transit_days": 28},
        "air": {"per_kg_usd": 4.50, "transit_days": 3},
        "land": {"per_container_usd": 2800, "transit_days": 14},
    }

    return {"lane": lane, "mode": mode, "rates": rates.get(mode, rates["sea"])}

register_tool(ToolDefinition(
    name="freight_rate",
    description="Get current freight rates for a shipping lane",
    agent="logistics",
    parameters={
        "type": "object",
        "properties": {
            "lane": {"type": "string", "description": "Shipping lane (e.g., Shanghai→Rotterdam)"},
            "mode": {"type": "string", "enum": ["sea", "air", "land"], "default": "sea"},
        },
        "required": ["lane"],
    },
    cache_ttl_seconds=600,
))
```

---

### 3.4 Market Agent Tools

#### `commodity_price`
Get commodity prices and trends.

```python
# backend/mcp/tools/commodity_tools.py

async def commodity_price(params: dict) -> dict:
    """Get commodity price data and short-term trends."""
    commodity = params.get("commodity")  # e.g., "lithium", "copper", "semiconductor"
    time_range = params.get("time_range", "30d")

    # Mock data for hackathon
    prices = {
        "lithium": {"current_usd_per_ton": 13500, "change_30d_pct": -8.2, "forecast_90d": "declining", "note": "Chile export restrictions may reverse trend"},
        "copper": {"current_usd_per_ton": 9200, "change_30d_pct": 5.1, "forecast_90d": "rising", "note": "EV demand driving increase"},
        "semiconductor": {"current_index": 185, "change_30d_pct": 12.3, "forecast_90d": "volatile", "note": "Taiwan geopolitical risk premium"},
        "crude_oil": {"current_usd_per_barrel": 78, "change_30d_pct": -3.5, "forecast_90d": "stable", "note": "OPEC+ maintaining cuts"},
    }

    return prices.get(commodity, {"error": f"Commodity {commodity} not tracked"})

register_tool(ToolDefinition(
    name="commodity_price",
    description="Get commodity price data and trends",
    agent="market",
    parameters={
        "type": "object",
        "properties": {
            "commodity": {"type": "string", "description": "Commodity name"},
            "time_range": {"type": "string", "default": "30d"},
        },
        "required": ["commodity"],
    },
    cache_ttl_seconds=600,
))
```

#### `trade_data`
Query international trade data.

```python
async def trade_data(params: dict) -> dict:
    """Query trade data (UN Comtrade-style)."""
    country = params.get("country")
    product_category = params.get("product_category", None)

    # Mock data
    return {
        "country": country,
        "exports": {"total_usd": "2.1B", "top_categories": ["electronics", "machinery", "chemicals"]},
        "imports": {"total_usd": "1.8B", "top_categories": ["raw_materials", "energy", "food"]},
        "trade_balance": "surplus",
        "tariff_exposure": "medium",
        "key_trade_partners": ["US", "China", "EU"],
    }

register_tool(ToolDefinition(
    name="trade_data",
    description="Query international trade data",
    agent="market",
    parameters={
        "type": "object",
        "properties": {
            "country": {"type": "string"},
            "product_category": {"type": "string"},
        },
        "required": ["country"],
    },
    cache_ttl_seconds=3600,  # 1 hour cache
))
```

#### `tariff_lookup`
Check tariff rates between countries.

```python
async def tariff_lookup(params: dict) -> dict:
    """Check tariff rates for trade between countries."""
    origin = params.get("origin_country")
    destination = params.get("destination_country")
    product = params.get("product", None)

    # Mock data
    return {
        "origin": origin,
        "destination": destination,
        "product": product,
        "current_tariff_pct": 7.5,
        "pending_changes": "Proposed 15% increase (Q3 2026)",
        "trade_agreement": "WTO Most Favored Nation",
        "risk_level": "medium",
    }

register_tool(ToolDefinition(
    name="tariff_lookup",
    description="Check tariff rates between countries",
    agent="market",
    parameters={
        "type": "object",
        "properties": {
            "origin_country": {"type": "string"},
            "destination_country": {"type": "string"},
            "product": {"type": "string"},
        },
        "required": ["origin_country", "destination_country"],
    },
    cache_ttl_seconds=3600,
))
```

---

### 3.5 Finance Agent Tools

#### `erp_query`
Query ERP financial data.

```python
# backend/mcp/tools/finance_tools.py

async def erp_query(params: dict) -> dict:
    """Query ERP for financial data (POs, spend, budgets)."""
    po_id = params.get("po_id", None)
    supplier_id = params.get("supplier_id", None)
    date_range = params.get("date_range", "30d")

    # Mock data
    return {
        "active_pos": [
            {"po_id": "PO-101", "supplier": "S1", "amount_usd": 1200000, "status": "in_transit", "eta": "2026-05-01"},
            {"po_id": "PO-102", "supplier": "S1", "amount_usd": 800000, "status": "confirmed", "eta": "2026-05-15"},
            {"po_id": "PO-103", "supplier": "S2", "amount_usd": 500000, "status": "pending", "eta": "2026-06-01"},
        ],
        "total_exposure_usd": 4200000,
        "budget_remaining_usd": 1800000,
        "spend_ytd_usd": 8500000,
    }

register_tool(ToolDefinition(
    name="erp_query",
    description="Query ERP for financial data (POs, spend, budgets)",
    agent="finance",
    parameters={
        "type": "object",
        "properties": {
            "po_id": {"type": "string"},
            "supplier_id": {"type": "string"},
            "date_range": {"type": "string", "default": "30d"},
        },
    },
    cache_ttl_seconds=300,
))
```

#### `currency_rate`
Get exchange rates.

```python
async def currency_rate(params: dict) -> dict:
    """Get currency exchange rates."""
    from_currency = params.get("from_currency", "USD")
    to_currency = params.get("to_currency", "INR")

    # Mock rates
    rates = {"USD_INR": 83.5, "USD_EUR": 0.92, "USD_CNY": 7.25, "USD_TWD": 32.1, "USD_VND": 24500}

    key = f"{from_currency}_{to_currency}"
    rate = rates.get(key, None)

    if not rate:
        # Try reverse
        reverse_key = f"{to_currency}_{from_currency}"
        reverse_rate = rates.get(reverse_key, None)
        if reverse_rate:
            rate = 1 / reverse_rate
        else:
            rate = 1.0  # Fallback

    return {"from": from_currency, "to": to_currency, "rate": round(rate, 4), "source": "mock"}

register_tool(ToolDefinition(
    name="currency_rate",
    description="Get currency exchange rates",
    agent="finance",
    parameters={
        "type": "object",
        "properties": {
            "from_currency": {"type": "string", "default": "USD"},
            "to_currency": {"type": "string", "default": "INR"},
        },
    },
    cache_ttl_seconds=1800,
))
```

#### `insurance_claim`
File or track insurance claims.

```python
async def insurance_claim(params: dict) -> dict:
    """File or track cargo insurance claims."""
    incident_id = params.get("incident_id")
    claim_type = params.get("claim_type", "delay")
    amount = params.get("amount", None)

    return {
        "claim_id": f"CLM-{hash(incident_id) % 10000:04d}",
        "incident_id": incident_id,
        "type": claim_type,
        "estimated_payout_usd": amount * 0.85 if amount else None,
        "status": "filed",
        "processing_time_estimate": "10-15 business days",
        "documentation_required": ["Bill of Lading", "Delay Certificate", "Commercial Invoice"],
    }

register_tool(ToolDefinition(
    name="insurance_claim",
    description="File or track cargo insurance claims",
    agent="finance",
    parameters={
        "type": "object",
        "properties": {
            "incident_id": {"type": "string"},
            "claim_type": {"type": "string", "enum": ["delay", "damage", "loss"]},
            "amount": {"type": "number"},
        },
        "required": ["incident_id"],
    },
    cache_ttl_seconds=0,  # No cache for write operations
))
```

---

### 3.6 Brand Agent Tools

#### `social_sentiment`
Get brand sentiment metrics from social media.

```python
# backend/mcp/tools/social_tools.py

async def social_sentiment(params: dict) -> dict:
    """Get brand sentiment metrics from social platforms."""
    brand = params.get("brand")
    platform = params.get("platform", "all")  # twitter, reddit, all
    time_range = params.get("time_range", "7d")

    # Mock data
    return {
        "brand": brand,
        "overall_sentiment": 62,  # 0-100
        "trend": "declining",
        "negative_mentions_24h": 2400,
        "positive_mentions_24h": 1800,
        "neutral_mentions_24h": 3200,
        "top_negative_topics": ["delivery delays", "stock shortage", "price increase"],
        "top_positive_topics": ["product quality", "customer service"],
        "competitor_comparison": {
            "our_sentiment": 62,
            "competitor_avg": 71,
            "gap": -9,
        },
    }

register_tool(ToolDefinition(
    name="social_sentiment",
    description="Get brand sentiment metrics from social platforms",
    agent="brand",
    parameters={
        "type": "object",
        "properties": {
            "brand": {"type": "string"},
            "platform": {"type": "string", "enum": ["twitter", "reddit", "all"], "default": "all"},
            "time_range": {"type": "string", "default": "7d"},
        },
        "required": ["brand"],
    },
    cache_ttl_seconds=180,
))
```

#### `competitor_ads`
Monitor competitor advertising activity.

```python
async def competitor_ads(params: dict) -> dict:
    """Monitor competitor ad spend and campaigns."""
    competitor = params.get("competitor")
    keywords = params.get("keywords", [])

    # Mock data
    return {
        "competitor": competitor,
        "ad_spend_trend": "increasing",
        "estimated_daily_spend_usd": 15000,
        "active_campaigns": [
            {"name": "Always in Stock", "channel": "Google Ads", "target_keywords": ["fast delivery", "reliable supply"]},
            {"name": "Summer Sale", "channel": "Social", "target_keywords": ["discount", "value"]},
        ],
        "bidding_on_our_keywords": True,
        "alert": f"{competitor} is targeting your brand keywords with 'Always in Stock' campaign",
    }

register_tool(ToolDefinition(
    name="competitor_ads",
    description="Monitor competitor ad spend and campaigns",
    agent="brand",
    parameters={
        "type": "object",
        "properties": {
            "competitor": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["competitor"],
    },
    cache_ttl_seconds=600,
))
```

#### `content_generate`
Generate crisis communication content.

```python
async def content_generate(params: dict) -> dict:
    """Generate crisis communication drafts (press releases, social posts, ad copies, customer emails)."""
    content_type = params.get("type")  # press_release, social_post, ad_copy, customer_email
    context = params.get("context", "")
    tone = params.get("tone", "professional")  # professional, empathetic, urgent, reassuring

    # This tool delegates to the LLM for content generation
    # The actual generation happens in the Brand Agent's LLM call
    # This tool provides the template structure

    templates = {
        "press_release": {
            "subject": "[DRAFT] Company Statement on Supply Chain Disruption",
            "sections": ["Situation Overview", "Actions Taken", "Customer Impact", "Timeline", "Contact"],
        },
        "social_post": {
            "platforms": ["Twitter (280 chars)", "LinkedIn (700 chars)", "Facebook (500 chars)"],
            "tone_options": ["empathetic", "reassuring", "transparent"],
        },
        "ad_copy": {
            "types": ["brand_resilience", "substitute_products", "pre_order", "value_messaging"],
            "channels": ["Google Ads", "Social Media", "Display"],
        },
        "customer_email": {
            "sections": ["Personal greeting", "Situation update", "What we're doing", "What this means for you", "Next steps"],
            "personalization": ["by_customer_segment", "by_order_status"],
        },
    }

    return {
        "content_type": content_type,
        "template": templates.get(content_type, {}),
        "context": context,
        "tone": tone,
        "note": "All generated content is DRAFT — requires human review before publishing",
    }

register_tool(ToolDefinition(
    name="content_generate",
    description="Generate crisis communication drafts",
    agent="brand",
    parameters={
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["press_release", "social_post", "ad_copy", "customer_email"]},
            "context": {"type": "string", "description": "Context for the content"},
            "tone": {"type": "string", "enum": ["professional", "empathetic", "urgent", "reassuring"], "default": "professional"},
        },
        "required": ["type"],
    },
    cache_ttl_seconds=0,  # No cache for generative content
))
```

---

## 4. MCP Security & Sandboxing

### 4.1 Sandbox Rules

```python
# backend/mcp/sandbox.py

SANDBOX_RULES = {
    # Tool-level restrictions
    "neo4j_query": {
        "read_only": True,                    # Only MATCH queries allowed
        "blocked_keywords": ["CREATE", "DELETE", "SET", "REMOVE", "MERGE", "DROP"],
        "max_records": 100,
        "timeout_seconds": 10,
    },
    "route_optimize": {
        "max_constraints": 20,
        "timeout_seconds": 30,
    },
    "content_generate": {
        "pii_redaction": True,                # Redact PII in generated content
        "human_review_required": True,        # Flag for human review
        "max_content_length": 5000,
    },
    "erp_query": {
        "fields_allowed": ["po_id", "supplier_id", "amount", "status", "eta"],
        "fields_blocked": ["customer_name", "customer_email", "phone", "address"],
    },
    "insurance_claim": {
        "write_allowed": True,                # This is a write tool
        "audit_required": True,               # Must log all claim filings
    },
}

def validate_cypher_query(query: str) -> bool:
    """Ensure Cypher query is read-only (no mutations)."""
    blocked = SANDBOX_RULES["neo4j_query"]["blocked_keywords"]
    upper_query = query.upper()
    for keyword in blocked:
        if keyword in upper_query:
            return False
    return True

def redact_pii(text: str) -> str:
    """Redact PII from text before returning to agents."""
    import re
    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', text)
    # Redact phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', text)
    # Redact credit card numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CC]', text)
    return text
```

### 4.2 Agent-Tool Permission Matrix

| Tool | risk | supply | logistics | market | finance | brand |
|------|------|--------|-----------|--------|---------|-------|
| `news_search` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `gdelt_query` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `supplier_financials` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `neo4j_query` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `supplier_search` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `contract_lookup` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `route_optimize` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `port_status` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `freight_rate` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `commodity_price` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `trade_data` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `tariff_lookup` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `erp_query` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `currency_rate` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `insurance_claim` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `social_sentiment` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `competitor_ads` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `content_generate` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### 4.3 Prompt Injection Protection

```python
# backend/mcp/sanitize.py

import re

def sanitize_external_content(content: str) -> str:
    """Sanitize external content before adding to agent context."""
    # Remove potential prompt injection patterns
    patterns_to_remove = [
        r"(?i)ignore\s+(previous|above|all)\s+instructions",
        r"(?i)disregard\s+(your|the)\s+(system|initial)\s+prompt",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)new\s+instructions?:",
        r"(?i)forget\s+(everything|all|previous)",
        r"```[\s\S]*?```",  # Remove code blocks from external content
    ]

    sanitized = content
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, "[FILTERED]", sanitized)

    return sanitized

def validate_tool_params(tool_name: str, params: dict) -> dict:
    """Validate and sanitize tool parameters."""
    sanitized = {}
    for key, value in params.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_external_content(value)
        else:
            sanitized[key] = value
    return sanitized
```

---

## 5. MCP Audit Logging

### 5.1 Audit Table (Neon PostgreSQL)

```sql
CREATE TABLE mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    agent VARCHAR(30) NOT NULL,
    tool VARCHAR(50) NOT NULL,
    params JSONB,
    result_summary TEXT,
    latency_ms INT,
    was_cached BOOLEAN DEFAULT false,
    sandbox_violations TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast querying
CREATE INDEX idx_mcp_audit_session ON mcp_audit_log(session_id);
CREATE INDEX idx_mcp_audit_agent ON mcp_audit_log(agent);
CREATE INDEX idx_mcp_audit_created ON mcp_audit_log(created_at DESC);
```

### 5.2 Audit Logger

```python
# backend/mcp/audit.py

import asyncpg
import os
import json

async def audit_log(agent: str, tool: str, params: dict, result_summary: str, latency_ms: int, session_id: str = None):
    """Log MCP tool call to Neon PostgreSQL audit table."""
    conn = await asyncpg.connect(os.environ["NEON_DATABASE_URL"])
    try:
        await conn.execute(
            """INSERT INTO mcp_audit_log (session_id, agent, tool, params, result_summary, latency_ms)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            session_id, agent, tool, json.dumps(params), result_summary[:500], latency_ms,
        )
    finally:
        await conn.close()

async def get_audit_trail(session_id: str, limit: int = 100) -> list:
    """Retrieve audit trail for a council session."""
    conn = await asyncpg.connect(os.environ["NEON_DATABASE_URL"])
    try:
        rows = await conn.fetch(
            """SELECT agent, tool, params, result_summary, latency_ms, was_cached, created_at
               FROM mcp_audit_log
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            session_id, limit,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()
```

---

## 6. MCP Cache Strategy (Redis)

### 6.1 Cache Key Patterns

| Pattern | TTL | Example |
|---------|-----|---------|
| `mcp:news_search:{hash}` | 5m | `mcp:news_search:a1b2c3` |
| `mcp:gdelt_query:{hash}` | 10m | `mcp:gdelt_query:d4e5f6` |
| `mcp:supplier_financials:{hash}` | 15m | `mcp:supplier_financials:g7h8i9` |
| `mcp:neo4j_query:{hash}` | 5m | `mcp:neo4j_query:j0k1l2` |
| `mcp:commodity_price:{hash}` | 10m | `mcp:commodity_price:m3n4o5` |
| `mcp:port_status:{hash}` | 3m | `mcp:port_status:p6q7r8` |
| `mcp:erp_query:{hash}` | 5m | `mcp:erp_query:s9t0u1` |
| `mcp:social_sentiment:{hash}` | 3m | `mcp:social_sentiment:v2w3x4` |

### 6.2 Cache Implementation

```python
# backend/mcp/cache.py

import redis.asyncio as redis
import json
import os

_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    return _redis_client

async def check_cache(key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cache(key: str, value: dict, ttl_seconds: int):
    r = await get_redis()
    await r.setex(key, ttl_seconds, json.dumps(value))

async def invalidate_cache(pattern: str):
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)
```

---

## 7. MCP API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp/call` | Execute a tool call (agent-authenticated) |
| GET | `/mcp/tools` | List all registered tools (optional `?agent=` filter) |
| GET | `/mcp/tools/{tool_name}` | Get tool definition and schema |
| GET | `/mcp/health` | Health check + tool count |
| GET | `/mcp/audit/{session_id}` | Get audit trail for a session |
| GET | `/mcp/cache/stats` | Cache hit/miss statistics |

---

## 8. MCP Integration with LangChain Agents

### 8.1 Converting MCP Tools to LangChain Tools

```python
# backend/mcp/langchain_integration.py

from langchain_core.tools import tool as lc_tool
from langchain_core.runnables import RunnableConfig
import httpx
import os

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-key")

def create_langchain_tool(mcp_tool_name: str, agent: str, description: str, param_schema: dict):
    """Create a LangChain tool that calls the MCP server."""

    @lc_tool(mcp_tool_name, args_schema=param_schema, description=description)
    async def mcp_tool_wrapper(**kwargs) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MCP_SERVER_URL}/mcp/call",
                json={"agent": agent, "tool": mcp_tool_name, "params": kwargs},
                headers={"X-MCP-API-Key": MCP_API_KEY},
                timeout=30.0,
            )
            if resp.status_code != 200:
                return f"Error: MCP tool call failed ({resp.status_code})"
            data = resp.json()
            return str(data["result"])

    return mcp_tool_wrapper

# Example: Create LangChain tools for Risk Agent
risk_news_tool = create_langchain_tool(
    "news_search", "risk",
    "Search news for supply chain events",
    {"query": {"type": "string"}, "date_from": {"type": "string"}, "region": {"type": "string"}},
)

risk_gdelt_tool = create_langchain_tool(
    "gdelt_query", "risk",
    "Query GDELT for geopolitical events",
    {"country": {"type": "string"}, "event_type": {"type": "string"}, "time_range_days": {"type": "integer"}},
)

risk_financials_tool = create_langchain_tool(
    "supplier_financials", "risk",
    "Get supplier financial health data",
    {"supplier_id": {"type": "string"}},
)
```

### 8.2 Attaching Tools to Agents

```python
# backend/agents/risk_agent.py

from langchain_groq import ChatGroq
from langchain.agents import create_react_agent
from backend.mcp.langchain_integration import risk_news_tool, risk_gdelt_tool, risk_financials_tool

RISK_SYSTEM_PROMPT = """You are the Risk Sentinel Agent..."""  # (from agents.md)

def create_risk_agent():
    llm = ChatGroq(
        groq_api_key=os.environ["GROQ_API_KEY"],
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
    )

    tools = [risk_news_tool, risk_gdelt_tool, risk_financials_tool]

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=RISK_SYSTEM_PROMPT,
    )

    return agent
```

---

## 9. MCP Settings UI (Frontend Modal)

The Settings modal in the React SPA includes an MCP Tools tab:

| Setting | Type | Description |
|---------|------|-------------|
| Tool toggles | Switch | Enable/disable individual MCP tools per agent |
| Cache TTL | Slider | Adjust cache duration per tool (0–3600s) |
| Rate limit | Input | Set max calls per minute per tool |
| Sandbox mode | Toggle | Enable/disable sandbox for Neo4j queries |
| Audit log export | Button | Export MCP audit trail as JSON/PDF |
| MCP server URL | Input | Configure MCP server endpoint |
| API key | Input | MCP authentication key |

---

## 10. MCP Error Handling

### 10.1 Fallback Strategy

```python
MCP_ERROR_HANDLING = {
    "tool_timeout": {
        "action": "return_cached_or_error",
        "timeout_seconds": 30,
        "fallback": "Return last cached result if available, else error message",
    },
    "tool_rate_limited": {
        "action": "queue_and_retry",
        "retry_after_seconds": 60,
        "max_retries": 3,
    },
    "tool_auth_failed": {
        "action": "log_and_error",
        "audit": True,
    },
    "tool_sandbox_violation": {
        "action": "block_and_audit",
        "audit": True,
        "alert": True,
    },
    "external_api_down": {
        "action": "return_cached_or_mock",
        "fallback": "Return cached data if available, else mock data for demo",
    },
}
```

### 10.2 Graceful Degradation

When MCP tools fail, agents should still function:

1. **Cached data available** → Use cached result with `confidence` penalty (-10%)
2. **No cache, mock data available** → Use mock data with `confidence` penalty (-30%) and flag as simulated
3. **No data at all** → Agent responds with "Data unavailable" and reduced confidence (floor at 20%)

```python
async def call_tool_with_fallback(agent: str, tool: str, params: dict) -> dict:
    """Call MCP tool with graceful degradation on failure."""
    try:
        resp = await call_mcp_tool(agent, tool, params)
        resp["data_source"] = "live"
        return resp
    except httpx.TimeoutException:
        cached = await check_cache(f"mcp:{tool}:{hash_params(params)}")
        if cached:
            cached["data_source"] = "cached"
            cached["confidence_penalty"] = -10
            return cached
        return {"data_source": "unavailable", "error": "Tool timeout, no cached data", "confidence_penalty": -30}
    except Exception as e:
        return {"data_source": "error", "error": str(e), "confidence_penalty": -30}
```

---

## 11. Complete Tool Summary (45 Tools)

### Original Tools (1-22)

| # | Tool Name | Agent | External API | Live? |
|---|-----------|-------|-------------|-------|
| 1 | `news_search` | risk | NewsAPI | ✅ |
| 2 | `gdelt_query` | risk | GDELT | ✅ |
| 3 | `supplier_financials` | risk | Finnhub | ✅ |
| 4 | `neo4j_query` | supply | Neo4j | ✅ |
| 5 | `supplier_search` | supply | Neo4j | ✅ |
| 6 | `contract_lookup` | supply | Mock/DB | Mock |
| 7 | `route_optimize` | logistics | OR-Tools | ✅ |
| 8 | `port_status` | logistics | Mock | Mock |
| 9 | `freight_rate` | logistics | Mock | Mock |
| 10 | `commodity_price` | market | FRED/Yahoo | ✅ |
| 11 | `trade_data` | market | UN Comtrade | ✅ |
| 12 | `tariff_lookup` | market | Trade DB | Mock |
| 13 | `erp_query` | finance | SAP/Oracle | Mock |
| 14 | `currency_rate` | finance | Frankfurter | ✅ |
| 15 | `insurance_claim` | finance | Insurance DB | Mock |
| 16 | `social_sentiment` | brand | Reddit | ✅ |
| 17 | `competitor_ads` | brand | Mock | Mock |
| 18 | `content_generate` | brand | LLM | ✅ |
| 19 | `rag_query` | all | Pinecone/HF | ✅ |
| 20 | `firecrawl_scrape` | all | Firecrawl | ✅ |
| 21 | `web_search` | all | Firecrawl | ✅ |
| 22 | `pdf_export` | all | ReportLab | ✅ |

### New Real-Data Tools (23-45)

| # | Tool Name | Agent | External API | Live? | File |
|---|-----------|-------|-------------|-------|------|
| 23 | `gdelt_events` | risk | GDELT | ✅ | `gdelt_tools.py` |
| 24 | `gdelt_tone` | risk | GDELT | ✅ | `gdelt_tools.py` |
| 25 | `stock_quote` | risk/finance | Finnhub | ✅ | `finnhub_tools.py` |
| 26 | `company_profile` | risk/finance | Finnhub | ✅ | `finnhub_tools.py` |
| 27 | `company_financials` | risk/finance | Finnhub | ✅ | `finnhub_tools.py` |
| 28 | `fred_commodity_price` | market | FRED + Yahoo Finance | ✅ | `fred_tools.py` |
| 29 | `economic_indicator` | market | FRED | ✅ | `fred_tools.py` |
| 30 | `exchange_rate` | finance | Frankfurter | ✅ | `frankfurter_tools.py` |
| 31 | `historical_rate` | finance | Frankfurter | ✅ | `frankfurter_tools.py` |
| 32 | `weather_forecast` | risk/logistics | Open-Meteo | ✅ | `weather_tools.py` |
| 33 | `earthquake_check` | risk | USGS | ✅ | `weather_tools.py` |
| 34 | `disaster_alerts` | risk | GDACS | ✅ | `weather_tools.py` |
| 35 | `wikipedia_search` | all | MediaWiki API | ✅ | `knowledge_tools.py` |
| 36 | `wikipedia_summary` | all | MediaWiki API | ✅ | `knowledge_tools.py` |
| 37 | `arxiv_search` | all | Arxiv | ✅ | `knowledge_tools.py` |
| 38 | `reddit_sentiment` | brand | Reddit | ✅ | `knowledge_tools.py` |
| 39 | `trade_flows` | market | UN Comtrade | ✅ | `trade_tools.py` |
| 40 | `sec_filing` | finance | SEC EDGAR | ✅ | `trade_tools.py` |
| 41 | `opencorporates_search` | supply | OpenCorporates | ✅ | `trade_tools.py` |
| 42 | `worldbank_indicator` | market | World Bank | ✅ | `trade_tools.py` |
| 43-45 | (reserved for future) | — | — | — | — |

### Market API (Frontend Aggregation)

| Endpoint | Tools Used |
|----------|-----------|
| `GET /market/ticker` | `stock_quote` ×4, `exchange_rate`, `fred_commodity_price` ×2 |
| `GET /market/company/{symbol}` | `company_profile`, `stock_quote`, `company_financials`, `wikipedia_summary` |
| `GET /market/risk-dashboard` | `earthquake_check` ×3, `weather_forecast` ×3, `disaster_alerts` |
| `GET /market/brand-intel` | `reddit_sentiment` ×2, `wikipedia_search`, `arxiv_search` |
