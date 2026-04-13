"""Financial Modeling Prep (FMP) MCP Tools — Financials, DCF, ratings, sector data."""
import httpx
import os

FMP_BASE_V3 = "https://financialmodelingprep.com/api/v3"
FMP_BASE_V4 = "https://financialmodelingprep.com/stable"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.fmp_api_key or os.getenv("FMP_API_KEY", "")
    except Exception:
        return os.getenv("FMP_API_KEY", "")


def _mock_profile(symbol: str) -> dict:
    return {"symbol": symbol, "companyName": "Mock Corp", "mock": True}


async def company_profile(params: dict) -> dict:
    """Get company profile from FMP.

    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSM')
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return _mock_profile(symbol)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{FMP_BASE_V4}/profile", params={"symbol": symbol, "apikey": key})
            data = resp.json()

        if isinstance(data, list) and data:
            p = data[0]
            return {
                "symbol": p.get("symbol", symbol),
                "name": p.get("companyName", ""),
                "sector": p.get("sector", ""),
                "industry": p.get("industry", ""),
                "market_cap": p.get("mktCap", 0),
                "price": float(p.get("price", 0)),
                "exchange": p.get("exchangeShortName", ""),
                "description": p.get("description", "")[:500],
                "mock": False,
            }

        return _mock_profile(symbol)
    except Exception:
        return _mock_profile(symbol)


async def key_metrics(params: dict) -> dict:
    """Get key financial metrics (P/E, ROE, debt/equity) from FMP.

    Args:
        symbol: Stock ticker
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return {"symbol": symbol, "metrics": {}, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{FMP_BASE_V4}/key-metrics", params={
                "symbol": symbol, "period": "annual", "apikey": key,
            })
            data = resp.json()

        if isinstance(data, list) and data:
            m = data[0]
            return {
                "symbol": symbol,
                "pe_ratio": m.get("peRatio", None),
                "roe": m.get("roe", None),
                "debt_to_equity": m.get("debtToEquity", None),
                "current_ratio": m.get("currentRatio", None),
                "gross_margin": m.get("grossMargin", None),
                "operating_margin": m.get("operatingMargin", None),
                "revenue_growth": m.get("revenueGrowth", None),
                "mock": False,
            }

        return {"symbol": symbol, "metrics": {}, "mock": True}
    except Exception:
        return {"symbol": symbol, "metrics": {}, "mock": True}


async def dcf_valuation(params: dict) -> dict:
    """Get DCF (discounted cash flow) valuation from FMP.

    Args:
        symbol: Stock ticker
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return {"symbol": symbol, "dcf": 0, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FMP_BASE_V4}/discounted-cash-flow", params={"symbol": symbol, "apikey": key})
            data = resp.json()

        if isinstance(data, list) and data:
            r = data[0]
            dcf_val = r.get("dcf", 0)
            stock_price = r.get("Stock Price", 0)
            # If DCF > price, stock is undervalued
            if dcf_val and stock_price:
                valuation = "undervalued" if float(dcf_val) > float(stock_price) else "overvalued"
            else:
                valuation = "N/A"
            return {
                "symbol": symbol,
                "dcf": float(dcf_val) if dcf_val else 0,
                "stock_price": float(stock_price) if stock_price else 0,
                "valuation": valuation,
                "date": r.get("date", ""),
                "mock": False,
            }

        return {"symbol": symbol, "dcf": 0, "mock": True}
    except Exception:
        return {"symbol": symbol, "dcf": 0, "mock": True}


async def income_statement(params: dict) -> dict:
    """Get latest income statement from FMP.

    Args:
        symbol: Stock ticker
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return {"symbol": symbol, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{FMP_BASE_V4}/income-statement", params={
                "symbol": symbol, "apikey": key,
            })
            data = resp.json()

        if isinstance(data, list) and data:
            s = data[0]
            return {
                "symbol": symbol,
                "date": s.get("date", ""),
                "revenue": s.get("revenue", 0),
                "cost_of_revenue": s.get("costOfRevenue", 0),
                "gross_profit": s.get("grossProfit", 0),
                "operating_income": s.get("operatingIncome", 0),
                "net_income": s.get("netIncome", 0),
                "eps": s.get("eps", 0),
                "mock": False,
            }

        return {"symbol": symbol, "mock": True}
    except Exception:
        return {"symbol": symbol, "mock": True}


TOOLS = [
    {
        "name": "fmp_company_profile",
        "description": "Get company profile (sector, market cap, description). Uses FMP API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker (e.g., 'AAPL', 'TSM')"}
            },
            "required": ["symbol"]
        },
        "handler": company_profile,
        "cache_ttl": 3600,
    },
    {
        "name": "fmp_key_metrics",
        "description": "Get key financial metrics (P/E, ROE, debt/equity). Uses FMP API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker"}
            },
            "required": ["symbol"]
        },
        "handler": key_metrics,
        "cache_ttl": 86400,
    },
    {
        "name": "fmp_dcf_valuation",
        "description": "Get DCF valuation (undervalued/overvalued). Uses FMP API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker"}
            },
            "required": ["symbol"]
        },
        "handler": dcf_valuation,
        "cache_ttl": 1800,
    },
    {
        "name": "fmp_income_statement",
        "description": "Get income statement (revenue, profit, EPS). Uses FMP API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker"}
            },
            "required": ["symbol"]
        },
        "handler": income_statement,
        "cache_ttl": 86400,
    },
]
