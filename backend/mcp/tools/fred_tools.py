"""FRED Economic Data MCP Tools — Commodity prices, economic indicators."""
import httpx
import os

FRED_BASE = "https://api.stlouisfed.org/fred"

# Key FRED series for supply chain
FRED_SERIES = {
    "crude_oil": "DCOILBRENTEU",
    "wti_oil": "DCOILWTICO",
    "industrial_commodities": "WPU102",
    "copper": "PCOPPUSDM",
    "aluminum": "PALUMUSDM",
    "steel": "WPS101",
    "natural_gas": "DHHNGSP",
    "usd_eur": "DEXUSEU",
    "usd_cny": "DEXCHUS",
    "usd_jpy": "DEXJPUS",
    "usd_twd": "DEXTWNUS",
    "cpi_us": "CPIAUCSL",
    "ppi_us": "PPIACO",
    "gdp_us": "GDP",
    "manufacturing_pmi": "MANMM101USM189S",
    "container_freight": "WPSFD4111",
}


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.fred_api_key or os.getenv("FRED_API_KEY", "")
    except Exception:
        return os.getenv("FRED_API_KEY", "")


def _mock_commodity_price(commodity: str) -> dict:
    mock_prices = {
        "crude_oil": 82.50, "wti_oil": 78.30, "industrial_commodities": 195.4,
        "copper": 8450.0, "aluminum": 2350.0, "steel": 850.0,
        "natural_gas": 2.85, "container_freight": 3200.0,
    }
    return {
        "commodity": commodity,
        "series_id": FRED_SERIES.get(commodity, "UNKNOWN"),
        "price": mock_prices.get(commodity, 100.0),
        "unit": "USD",
        "date": "2024-01-15",
        "mock": True
    }


def _mock_economic_indicator(indicator: str) -> dict:
    return {
        "indicator": indicator,
        "series_id": FRED_SERIES.get(indicator, "UNKNOWN"),
        "value": 100.0,
        "date": "2024-01-01",
        "mock": True
    }


async def commodity_price(params: dict) -> dict:
    """Get real commodity price from FRED.
    
    Args:
        commodity: Commodity name (crude_oil, wti_oil, copper, aluminum, steel, natural_gas, industrial_commodities, container_freight)
    """
    commodity = params.get("commodity", "crude_oil")
    key = _get_key()
    series_id = FRED_SERIES.get(commodity, FRED_SERIES.get("crude_oil"))

    if not key:
        return _mock_commodity_price(commodity)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(f"{FRED_BASE}/series/observations", params={
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1
            })
            if resp.status_code != 200:
                return _mock_commodity_price(commodity)
            data = resp.json()

        observations = data.get("observations", [])
        if not observations:
            return _mock_commodity_price(commodity)

        latest = observations[0]
        val = latest.get("value", ".")
        if val == "." or val is None:
            return _mock_commodity_price(commodity)

        return {
            "commodity": commodity,
            "series_id": series_id,
            "price": float(val),
            "date": latest.get("date", ""),
            "unit": "USD",
            "mock": False
        }
    except Exception:
        return _mock_commodity_price(commodity)


async def economic_indicator(params: dict) -> dict:
    """Get economic indicator from FRED (CPI, PPI, GDP, PMI, etc.).
    
    Args:
        indicator: Indicator name (cpi_us, ppi_us, gdp_us, manufacturing_pmi, usd_eur, usd_cny, usd_jpy, usd_twd)
    """
    indicator = params.get("indicator", "cpi_us")
    key = _get_key()
    series_id = FRED_SERIES.get(indicator, FRED_SERIES.get("cpi_us"))

    if not key:
        return _mock_economic_indicator(indicator)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FRED_BASE}/series/observations", params={
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 5
            })
            data = resp.json()

        observations = data.get("observations", [])
        if not observations:
            return _mock_economic_indicator(indicator)

        latest = observations[0]
        history = [{"date": o.get("date", ""), "value": float(o.get("value", 0) or 0)} for o in observations]

        return {
            "indicator": indicator,
            "series_id": series_id,
            "value": float(latest.get("value", 0) or 0),
            "date": latest.get("date", ""),
            "history": history,
            "mock": False
        }
    except Exception:
        return _mock_economic_indicator(indicator)


async def fred_search(params: dict) -> dict:
    """Search FRED for economic series matching a query.
    
    Args:
        query: Search terms (e.g., 'supply chain', 'semiconductor')
        limit: Max results (default: 5)
    """
    query = params.get("query", "supply chain")
    limit = params.get("limit", 5)
    key = _get_key()

    if not key:
        return {"query": query, "series": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FRED_BASE}/series/search", params={
                "search_text": query,
                "api_key": key,
                "file_type": "json",
                "limit": limit,
                "order_by": "popularity",
                "sort_order": "desc"
            })
            data = resp.json()

        series_list = data.get("seriess", [])
        results = [{
            "id": s.get("id", ""),
            "title": s.get("title", ""),
            "frequency": s.get("frequency", ""),
            "units": s.get("units", ""),
            "popularity": s.get("popularity", 0),
        } for s in series_list]

        return {"query": query, "series": results, "mock": False}
    except Exception:
        return {"query": query, "series": [], "mock": True}


TOOLS = [
    {
        "name": "fred_commodity_price",
        "description": "Get real commodity prices from FRED. Supports: crude_oil, wti_oil, copper, aluminum, steel, natural_gas, industrial_commodities, container_freight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "commodity": {"type": "string", "description": "Commodity name (e.g., 'crude_oil', 'copper', 'container_freight')", "default": "crude_oil"}
            },
            "required": ["commodity"]
        },
        "handler": commodity_price,
        "cache_ttl": 3600,
    },
    {
        "name": "economic_indicator",
        "description": "Get economic indicators from FRED. Supports: cpi_us, ppi_us, gdp_us, manufacturing_pmi, usd_eur, usd_cny, usd_jpy, usd_twd.",
        "input_schema": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string", "description": "Indicator name (e.g., 'cpi_us', 'manufacturing_pmi')", "default": "cpi_us"}
            },
            "required": ["indicator"]
        },
        "handler": economic_indicator,
        "cache_ttl": 3600,
    },
    {
        "name": "fred_search",
        "description": "Search FRED database for economic series. Returns series ID, title, frequency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms"},
                "limit": {"type": "integer", "description": "Max results (default: 5)", "default": 5}
            },
            "required": ["query"]
        },
        "handler": fred_search,
        "cache_ttl": 86400,
    },
]
