"""Finnhub Financial Data MCP Tools — Real stock/forex/company data."""
import httpx
import os

FINNHUB_BASE = "https://finnhub.io/api/v1"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.finnhub_api_key or os.getenv("FINNHUB_API_KEY", "")
    except Exception:
        return os.getenv("FINNHUB_API_KEY", "")


def _mock_stock_quote(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "current_price": 145.67,
        "change": -2.34,
        "change_percent": -1.58,
        "high": 148.50,
        "low": 144.20,
        "open": 147.80,
        "prev_close": 148.01,
        "mock": True
    }


def _mock_company_profile(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "name": f"{symbol} Corporation",
        "industry": "Semiconductors",
        "market_cap": 450000000000,
        "exchange": "NASDAQ",
        "ipo": "1990-01-01",
        "country": "US",
        "mock": True
    }


def _mock_financials(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "revenue": 65_000_000_000,
        "net_income": 15_000_000_000,
        "total_assets": 200_000_000_000,
        "total_debt": 30_000_000_000,
        "debt_to_equity": 0.18,
        "roe": 0.25,
        "mock": True
    }


async def stock_quote(params: dict) -> dict:
    """Get real-time stock quote from Finnhub.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'TSM', 'AAPL', 'INTC')
    """
    import time
    symbol = params.get("symbol", "AAPL")
    key = _get_key()
    current_time = time.time()

    if not key:
        return {**_mock_stock_quote(symbol), "timestamp": current_time, "data_freshness": "mock"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FINNHUB_BASE}/quote", params={"symbol": symbol, "token": key})
            resp.raise_for_status()
            data = resp.json()

        # Check if current price is available and not stale
        current_price = data.get("c", 0)
        prev_close = data.get("pc", 0)
        
        # Determine data freshness
        data_freshness = "real_time"
        is_market_hours = _is_market_hours()
        
        # If no current price or it's after hours, mark as stale
        if current_price == 0 or current_price == prev_close:
            data_freshness = "market_closed" if not is_market_hours else "stale"
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "change": data.get("d", 0),
            "change_percent": data.get("dp", 0),
            "high": data.get("h", 0),
            "low": data.get("l", 0),
            "open": data.get("o", 0),
            "prev_close": prev_close,
            "timestamp": current_time,
            "data_freshness": data_freshness,
            "market_hours": is_market_hours,
            "mock": False
        }
    except Exception as e:
        # Return mock data with error info
        return {**_mock_stock_quote(symbol), "timestamp": current_time, "data_freshness": "error", "error": str(e)}


def _is_market_hours() -> bool:
    """Check if US market is currently open."""
    import datetime
    from datetime import timezone
    
    now = datetime.datetime.now(timezone.utc)
    # Convert to Eastern Time (US market timezone)
    eastern_tz = datetime.timezone(datetime.timedelta(hours=-5))  # EST
    eastern_time = now.astimezone(eastern_tz)
    
    # Check if it's weekday
    if eastern_time.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return False
    
    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = eastern_time.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = eastern_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= eastern_time <= market_close


async def company_profile(params: dict) -> dict:
    """Get company profile from Finnhub.
    
    Args:
        symbol: Stock ticker symbol
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return _mock_company_profile(symbol)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FINNHUB_BASE}/stock/profile2", params={"symbol": symbol, "token": key})
            data = resp.json()

        if not data:
            return _mock_company_profile(symbol)

        return {
            "symbol": symbol,
            "name": data.get("name", ""),
            "industry": data.get("finnhubIndustry", ""),
            "market_cap": data.get("marketCapitalization", 0) * 1_000_000,
            "exchange": data.get("exchange", ""),
            "ipo": data.get("ipo", ""),
            "country": data.get("country", ""),
            "mock": False
        }
    except Exception:
        return _mock_company_profile(symbol)


async def company_financials(params: dict) -> dict:
    """Get company financial statements from Finnhub.
    
    Args:
        symbol: Stock ticker symbol
        statement: Financial statement type ('bs' balance sheet, 'ic' income, 'cf' cash flow)
    """
    symbol = params.get("symbol", "AAPL")
    statement = params.get("statement", "ic")
    key = _get_key()

    if not key:
        return _mock_financials(symbol)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FINNHUB_BASE}/stock/financials", params={
                "symbol": symbol, "statement": statement, "token": key
            })
            data = resp.json()

        financials = data.get("financials", [])
        if not financials:
            return _mock_financials(symbol)

        latest = financials[0] if financials else {}
        return {
            "symbol": symbol,
            "year": latest.get("year", ""),
            "revenue": latest.get("revenue", 0),
            "net_income": latest.get("netIncome", 0),
            "total_assets": latest.get("totalAssets", 0),
            "total_debt": latest.get("totalLiabilities", 0),
            "mock": False
        }
    except Exception:
        return _mock_financials(symbol)


async def forex_rate(params: dict) -> dict:
    """Get forex exchange rate from Finnhub.
    
    Args:
        base: Base currency (e.g., 'USD')
        quote: Quote currency (e.g., 'EUR')
    """
    base = params.get("base", "USD")
    quote = params.get("quote", "EUR")
    key = _get_key()

    if not key:
        return {"base": base, "quote": quote, "rate": 0.92, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{FINNHUB_BASE}/forex/rate", params={
                "base": base, "quote": quote, "token": key
            })
            data = resp.json()

        return {
            "base": base,
            "quote": quote,
            "rate": data.get("quote", {}).get("c", 0),
            "mock": False
        }
    except Exception:
        return {"base": base, "quote": quote, "rate": 0.92, "mock": True}


TOOLS = [
    {
        "name": "stock_quote",
        "description": "Get real-time stock quote (price, change, high/low). Uses Finnhub API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker (e.g., 'TSM', 'AAPL')"}
            },
            "required": ["symbol"]
        },
        "handler": stock_quote,
        "cache_ttl": 300,
    },
    {
        "name": "company_profile",
        "description": "Get company profile (name, industry, market cap, country). Uses Finnhub API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["symbol"]
        },
        "handler": company_profile,
        "cache_ttl": 86400,
    },
    {
        "name": "company_financials",
        "description": "Get company financial statements (revenue, income, assets). Uses Finnhub API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"},
                "statement": {"type": "string", "description": "Statement type: 'bs' (balance sheet), 'ic' (income), 'cf' (cash flow)", "default": "ic"}
            },
            "required": ["symbol"]
        },
        "handler": company_financials,
        "cache_ttl": 86400,
    },
    {
        "name": "forex_rate_finnhub",
        "description": "Get forex exchange rate from Finnhub. Use for real-time currency conversion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Base currency (e.g., 'USD')", "default": "USD"},
                "quote": {"type": "string", "description": "Quote currency (e.g., 'EUR')", "default": "EUR"}
            },
            "required": ["base", "quote"]
        },
        "handler": forex_rate,
        "cache_ttl": 1800,
    },
]
