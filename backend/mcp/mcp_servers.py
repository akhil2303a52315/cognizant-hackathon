"""MCP Server definitions for SupplyChainGPT Council.

Groups the 47+ registered MCP tools into logical server categories,
each representing a domain-specific MCP server. These definitions
drive the MultiServerMCPClient in mcp_toolkit.py and determine
which tools are available to which agents via least-privilege scopes.

Server categories:
  - news_geopolitical: GDELT, GDACS, NewsAPI, Wikipedia
  - shipping_logistics: Route optimization, port status, freight rates, weather, earthquakes
  - erp_inventory: ERP queries, supplier search, contracts, Neo4j graph
  - finance_market: Finnhub, Frankfurter, FRED/Yahoo, commodity prices, trade data
  - web_intel: Firecrawl scrape/crawl/search, Reddit, Arxiv
  - rag: Agentic RAG, Graph RAG v2, basic RAG query
"""

import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP Server definition model
# ---------------------------------------------------------------------------
class MCPServerDef(BaseModel):
    """Definition of a logical MCP server grouping."""
    name: str
    description: str
    tools: list[str]               # tool names that belong to this server
    allowed_agents: list[str]      # agents permitted to use this server's tools
    rate_limit_per_minute: int = 30
    requires_auth: bool = False
    health_check_tool: Optional[str] = None  # tool to call for health check

    class Config:
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# Server definitions — maps to existing registered tools
# ---------------------------------------------------------------------------
MCP_SERVERS: dict[str, MCPServerDef] = {
    "news_geopolitical": MCPServerDef(
        name="news_geopolitical",
        description="News & Geopolitical Intelligence — GDELT events, GDACS disasters, NewsAPI headlines, Wikipedia knowledge",
        tools=[
            "news_search",
            "newsapi_top_headlines",
            "gdelt_search_events",
            "gdelt_search_gkg",
            "gdacs_disaster_alerts",
            "wikipedia_search",
            "arxiv_search",
        ],
        allowed_agents=["risk", "brand", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="newsapi_top_headlines",
    ),
    "shipping_logistics": MCPServerDef(
        name="shipping_logistics",
        description="Shipping & Logistics — Route optimization, port status, freight rates, weather, earthquakes",
        tools=[
            "route_optimize",
            "port_status",
            "freight_rate",
            "get_shipping_routes",
            "weather_current",
            "weather_forecast",
            "usgs_earthquakes",
        ],
        allowed_agents=["logistics", "supply", "moderator"],
        rate_limit_per_minute=30,
        health_check_tool="weather_current",
    ),
    "erp_inventory": MCPServerDef(
        name="erp_inventory",
        description="ERP & Inventory — Supplier search, contracts, Neo4j graph queries, PO creation",
        tools=[
            "erp_query",
            "neo4j_query",
            "supplier_search",
            "contract_lookup",
            "supplier_risk_score",
            "search_suppliers",
        ],
        allowed_agents=["supply", "finance", "moderator"],
        rate_limit_per_minute=15,
        requires_auth=True,
        health_check_tool="supplier_search",
    ),
    "finance_market": MCPServerDef(
        name="finance_market",
        description="Finance & Market — Stock quotes, forex rates, commodity prices, trade data, insurance",
        tools=[
            "finnhub_stock_quote",
            "finnhub_stock_candles",
            "frankfurter_latest_rates",
            "frankfurter_historical_rates",
            "fred_commodity_price",
            "currency_rate",
            "insurance_claim",
            "comtrade_trade_data",
            "worldbank_indicators",
        ],
        allowed_agents=["finance", "market", "moderator"],
        rate_limit_per_minute=30,
        health_check_tool="frankfurter_latest_rates",
    ),
    "web_intel": MCPServerDef(
        name="web_intel",
        description="Web Intelligence — Firecrawl scrape/crawl/search, Reddit, social sentiment, competitor intel",
        tools=[
            "firecrawl_scrape",
            "firecrawl_crawl",
            "firecrawl_search",
            "reddit_search",
            "social_sentiment",
            "competitor_intel",
        ],
        allowed_agents=["brand", "risk", "market", "moderator"],
        rate_limit_per_minute=10,
        health_check_tool="reddit_search",
    ),
    "rag": MCPServerDef(
        name="rag",
        description="RAG Pipeline — Agentic RAG, Graph RAG v2, basic hybrid retrieval",
        tools=[
            "rag_query",
            "agentic_rag_query",
            "graph_rag_v2",
        ],
        allowed_agents=["risk", "supply", "logistics", "market", "finance", "brand", "moderator"],
        rate_limit_per_minute=60,
        health_check_tool="rag_query",
    ),
    "commodity_prices": MCPServerDef(
        name="commodity_prices",
        description="Commodity & Economic Data — Alpha Vantage commodity prices, stock time-series, economic indicators, currency exchange",
        tools=[
            "av_commodity_price",
            "av_stock_time_series",
            "av_economic_indicator",
            "av_currency_exchange",
            "fred_commodity_price",
            "fred_economic_data",
        ],
        allowed_agents=["market", "finance", "moderator"],
        rate_limit_per_minute=10,
        health_check_tool="av_commodity_price",
    ),
    "market_radar": MCPServerDef(
        name="market_radar",
        description="Market Radar — Polygon.io stocks/forex/aggregates, Finnhub company data, Mediastack 435+ news feeds, Currents API news",
        tools=[
            "polygon_stock_aggregate",
            "polygon_stock_snapshot",
            "polygon_forex_rate",
            "polygon_market_status",
            "polygon_ticker_news",
            "stock_quote",
            "company_profile",
            "company_financials",
            "forex_rate_finnhub",
            "mediastack_news_search",
            "mediastack_sources",
            "mediastack_historical_news",
            "currents_news_search",
            "currents_latest_news",
            "currents_brand_sentiment",
        ],
        allowed_agents=["market", "finance", "brand", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="polygon_market_status",
    ),
    "climate_risk": MCPServerDef(
        name="climate_risk",
        description="Climate & Weather Risk — OpenWeatherMap alerts/forecast, NOAA climate/storms/drought, sea level trends",
        tools=[
            "owm_current_weather",
            "owm_weather_forecast",
            "owm_weather_alerts",
            "owm_air_quality",
            "noaa_climate_data",
            "noaa_storm_events",
            "noaa_sea_level",
            "noaa_drought_monitor",
        ],
        allowed_agents=["risk", "logistics", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="owm_current_weather",
    ),
    "cyber_vulnerability": MCPServerDef(
        name="cyber_vulnerability",
        description="Cyber & Infrastructure Vulnerability — NIST NVD CVE search, Shodan device/exploit search",
        tools=[
            "nvd_cve_search",
            "nvd_cve_by_cpe",
            "nvd_cve_details",
            "nvd_recent_cves",
            "shodan_device_search",
            "shodan_host_info",
            "shodan_exploit_search",
        ],
        allowed_agents=["risk", "moderator"],
        rate_limit_per_minute=15,
        health_check_tool="nvd_recent_cves",
    ),
    "enhanced_finance": MCPServerDef(
        name="enhanced_finance",
        description="Enhanced Finance — Twelve Data stocks/forex/crypto, FMP financials/ratings/DCF, MarketAux sentiment",
        tools=[
            "td_time_series",
            "td_price_quote",
            "td_forex_rate",
            "td_market_movers",
            "fmp_company_profile",
            "fmp_key_metrics",
            "fmp_dcf_valuation",
            "fmp_income_statement",
            "marketaux_news",
            "marketaux_sentiment",
            "marketaux_trending",
        ],
        allowed_agents=["market", "finance", "brand", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="td_price_quote",
    ),
    "forex_backup": MCPServerDef(
        name="forex_backup",
        description="Forex Backup — ExchangeRate-API reliable forex, GNews alternative news",
        tools=[
            "exr_latest_rates",
            "exr_pair_conversion",
            "gnews_search",
            "gnews_top_headlines",
        ],
        allowed_agents=["finance", "market", "brand", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="exr_latest_rates",
    ),
    "route_optimization": MCPServerDef(
        name="route_optimization",
        description="Route Optimization — GraphHopper route planning, distance matrix, geocoding",
        tools=[
            "gh_route_optimize",
            "gh_distance_matrix",
            "gh_geocode",
        ],
        allowed_agents=["logistics", "supply", "moderator"],
        rate_limit_per_minute=20,
        health_check_tool="gh_geocode",
    ),
}


# ---------------------------------------------------------------------------
# Agent → Server mapping (least-privilege)
# ---------------------------------------------------------------------------
AGENT_SERVER_MAP: dict[str, list[str]] = {
    "risk":       ["news_geopolitical", "web_intel", "climate_risk", "cyber_vulnerability",
                   "enhanced_finance", "forex_backup", "rag"],
    "supply":     ["erp_inventory", "shipping_logistics", "route_optimization", "rag"],
    "logistics":  ["shipping_logistics", "climate_risk", "route_optimization", "rag"],
    "market":     ["finance_market", "commodity_prices", "market_radar", "web_intel",
                   "enhanced_finance", "forex_backup", "rag"],
    "finance":    ["finance_market", "commodity_prices", "market_radar", "erp_inventory",
                   "enhanced_finance", "forex_backup", "rag"],
    "brand":      ["web_intel", "news_geopolitical", "market_radar",
                   "enhanced_finance", "forex_backup", "rag"],
    "moderator":  ["news_geopolitical", "shipping_logistics", "erp_inventory",
                   "finance_market", "web_intel", "commodity_prices", "market_radar",
                   "climate_risk", "cyber_vulnerability", "enhanced_finance",
                   "forex_backup", "route_optimization", "rag"],
}


def get_agent_allowed_tools(agent_name: str) -> list[str]:
    """Return the list of tool names an agent is permitted to use."""
    servers = AGENT_SERVER_MAP.get(agent_name, ["rag"])
    tools = []
    for server_name in servers:
        server = MCP_SERVERS.get(server_name)
        if server:
            tools.extend(server.tools)
    return tools


def get_agent_servers(agent_name: str) -> list[MCPServerDef]:
    """Return the MCPServerDef objects an agent has access to."""
    server_names = AGENT_SERVER_MAP.get(agent_name, ["rag"])
    return [MCP_SERVERS[name] for name in server_names if name in MCP_SERVERS]


def get_server_for_tool(tool_name: str) -> Optional[MCPServerDef]:
    """Find which server definition a tool belongs to."""
    for server in MCP_SERVERS.values():
        if tool_name in server.tools:
            return server
    return None


def is_tool_allowed_for_agent(tool_name: str, agent_name: str) -> bool:
    """Check if an agent is permitted to use a specific tool."""
    allowed = get_agent_allowed_tools(agent_name)
    return tool_name in allowed


def get_all_server_definitions() -> dict[str, dict]:
    """Return all server definitions as serializable dicts."""
    return {
        name: {
            "name": s.name,
            "description": s.description,
            "tools": s.tools,
            "allowed_agents": s.allowed_agents,
            "rate_limit_per_minute": s.rate_limit_per_minute,
            "requires_auth": s.requires_auth,
        }
        for name, s in MCP_SERVERS.items()
    }


def get_tool_manifest() -> dict:
    """Return a complete tool discovery manifest: all servers, tools, and agent scopes."""
    return {
        "servers": get_all_server_definitions(),
        "agent_scopes": AGENT_SERVER_MAP,
        "total_tools": sum(len(s.tools) for s in MCP_SERVERS.values()),
        "total_servers": len(MCP_SERVERS),
    }
