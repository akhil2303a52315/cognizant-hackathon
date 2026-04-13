"""Polygon.io MCP Tools — Real stocks, forex, market aggregates from 92+ exchanges."""
import httpx
import os

POLYGON_BASE = "https://api.polygon.io"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.polygon_api_key or os.getenv("POLYGON_API_KEY", "")
    except Exception:
        return os.getenv("POLYGON_API_KEY", "")


def _mock_stock_aggregate(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "results": [
            {"date": "2025-01-15", "open": 145.0, "high": 148.5, "low": 144.2, "close": 146.8, "volume": 52000000},
            {"date": "2025-01-14", "open": 143.5, "high": 146.0, "low": 142.8, "close": 145.0, "volume": 48000000},
        ],
        "mock": True,
    }


def _mock_forex(from_curr: str, to_curr: str) -> dict:
    return {
        "from": from_curr,
        "to": to_curr,
        "rate": 0.92 if to_curr == "EUR" else 7.24 if to_curr == "CNY" else 1.0,
        "mock": True,
    }


def _mock_market_status() -> dict:
    return {
        "exchanges": [
            {"exchange": "NYSE", "status": "open"},
            {"exchange": "NASDAQ", "status": "open"},
            {"exchange": "TSE", "status": "closed"},
        ],
        "mock": True,
    }


async def stock_aggregate(params: dict) -> dict:
    """Get stock aggregate bars (OHLCV) from Polygon.io.

    Args:
        symbol: Stock ticker (e.g., 'TSM', 'AAPL')
        timespan: Bar timespan ('minute', 'hour', 'day', 'week', 'month')
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    symbol = params.get("symbol", "AAPL")
    timespan = params.get("timespan", "day")
    from_date = params.get("from_date", "2025-01-01")
    to_date = params.get("to_date", "2025-01-15")
    key = _get_key()

    if not key:
        return _mock_stock_aggregate(symbol)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{POLYGON_BASE}/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_date}/{to_date}",
                params={"apiKey": key, "limit": 30}
            )
            data = resp.json()

        if data.get("status") == "OK" and data.get("results"):
            results = []
            for r in data["results"][:30]:
                results.append({
                    "date": r.get("t", ""),
                    "open": r.get("o", 0),
                    "high": r.get("h", 0),
                    "low": r.get("l", 0),
                    "close": r.get("c", 0),
                    "volume": r.get("v", 0),
                    "vwap": r.get("vw", 0),
                })
            return {"symbol": symbol, "results": results, "count": len(results), "mock": False}

        return _mock_stock_aggregate(symbol)
    except Exception:
        return _mock_stock_aggregate(symbol)


async def stock_snapshot(params: dict) -> dict:
    """Get real-time stock snapshot (price, change, volume) from Polygon.io.

    Args:
        symbols: Comma-separated stock tickers (e.g., 'TSM,AAPL,INTC')
    """
    symbols = params.get("symbols", "AAPL")
    key = _get_key()

    if not key:
        return {"symbols": symbols, "results": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{POLYGON_BASE}/v2/snapshot/locale/us/markets/stocks/tickers",
                params={"tickers": symbols, "apiKey": key}
            )
            data = resp.json()

        if data.get("status") == "OK" and data.get("tickers"):
            results = []
            for t in data["tickers"][:10]:
                day = t.get("day", {})
                prev = t.get("prevDay", {})
                results.append({
                    "symbol": t.get("ticker", ""),
                    "price": day.get("c", 0),
                    "change": day.get("c", 0) - prev.get("c", 0) if prev else 0,
                    "change_pct": t.get("todaysChangePerc", 0),
                    "volume": day.get("v", 0),
                    "vwap": day.get("vw", 0),
                })
            return {"symbols": symbols, "results": results, "mock": False}

        return {"symbols": symbols, "results": [], "mock": True}
    except Exception:
        return {"symbols": symbols, "results": [], "mock": True}


async def forex_rate(params: dict) -> dict:
    """Get real-time forex rate from Polygon.io.

    Args:
        from_currency: Source currency (e.g., 'USD')
        to_currency: Target currency (e.g., 'EUR')
    """
    from_curr = params.get("from_currency", "USD")
    to_curr = params.get("to_currency", "EUR")
    key = _get_key()

    if not key:
        return _mock_forex(from_curr, to_curr)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{POLYGON_BASE}/v1/conversion/{from_curr}/{to_curr}",
                params={"apiKey": key, "amount": 1}
            )
            data = resp.json()

        if data.get("status") == "success":
            return {
                "from": from_curr,
                "to": to_curr,
                "rate": data.get("converted", 0),
                "last_updated": data.get("last", {}).get("timestamp", 0),
                "mock": False,
            }

        # Free tier may not authorize forex — try Ticker Price endpoint as fallback
        try:
            pair = f"C:{from_curr}{to_curr}"
            resp2 = await client.get(
                f"{POLYGON_BASE}/v1/last/currencies/{from_curr}/{to_curr}",
                params={"apiKey": key}
            )
            d2 = resp2.json()
            if d2.get("status") == "SUCCESS" and d2.get("last", {}).get("price"):
                return {
                    "from": from_curr,
                    "to": to_curr,
                    "rate": d2["last"]["price"],
                    "source": "polygon_ticker_price",
                    "mock": False,
                }
        except Exception:
            pass

        return _mock_forex(from_curr, to_curr)
    except Exception:
        return _mock_forex(from_curr, to_curr)


async def market_status(params: dict) -> dict:
    """Get current market status for all exchanges from Polygon.io."""
    key = _get_key()

    if not key:
        return _mock_market_status()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{POLYGON_BASE}/v1/marketstatus/now", params={"apiKey": key})
            data = resp.json()

        exchanges = []
        for ex_name, ex_status in data.get("exchanges", {}).items():
            # API returns flat strings like {"nasdaq": "open"} or nested dicts
            if isinstance(ex_status, str):
                exchanges.append({"exchange": ex_name, "status": ex_status})
            elif isinstance(ex_status, dict):
                exchanges.append({"exchange": ex_name, "status": ex_status.get("status", "unknown")})
            else:
                exchanges.append({"exchange": ex_name, "status": str(ex_status)})

        # Check if we got real data (has 'market' or 'serverTime' key)
        if data.get("market") or data.get("serverTime") or exchanges:
            return {
                "exchanges": exchanges,
                "currencies": data.get("currencies", {}),
                "market": data.get("market", "unknown"),
                "server_time": data.get("serverTime", ""),
                "mock": False,
            }

        return _mock_market_status()
    except Exception:
        return _mock_market_status()


async def ticker_news(params: dict) -> dict:
    """Get news articles for a stock ticker from Polygon.io.

    Args:
        ticker: Stock ticker (e.g., 'TSM')
        limit: Max results (default: 5)
    """
    ticker = params.get("ticker", "AAPL")
    limit = params.get("limit", 5)
    key = _get_key()

    if not key:
        return {"ticker": ticker, "results": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{POLYGON_BASE}/v1/reference/news",
                params={"ticker": ticker, "limit": limit, "apiKey": key}
            )
            data = resp.json()

        if data.get("results"):
            results = [{
                "title": r.get("title", ""),
                "url": r.get("article_url", ""),
                "source": r.get("publisher", {}).get("name", ""),
                "published": r.get("published_utc", ""),
                "tickers": r.get("tickers", []),
            } for r in data["results"]]
            return {"ticker": ticker, "results": results, "count": len(results), "mock": False}

        return {"ticker": ticker, "results": [], "mock": True}
    except Exception:
        return {"ticker": ticker, "results": [], "mock": True}


TOOLS = [
    {
        "name": "polygon_stock_aggregate",
        "description": "Get stock OHLCV aggregate bars (price history). Uses Polygon.io API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker (e.g., 'TSM', 'AAPL')"},
                "timespan": {"type": "string", "description": "Bar timespan: minute, hour, day, week, month", "default": "day"},
                "from_date": {"type": "string", "description": "Start date YYYY-MM-DD", "default": "2025-01-01"},
                "to_date": {"type": "string", "description": "End date YYYY-MM-DD", "default": "2025-01-15"}
            },
            "required": ["symbol"]
        },
        "handler": stock_aggregate,
        "cache_ttl": 1800,
    },
    {
        "name": "polygon_stock_snapshot",
        "description": "Get real-time stock snapshot (price, change, volume). Uses Polygon.io API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "string", "description": "Comma-separated tickers (e.g., 'TSM,AAPL,INTC')"}
            },
            "required": ["symbols"]
        },
        "handler": stock_snapshot,
        "cache_ttl": 60,
    },
    {
        "name": "polygon_forex_rate",
        "description": "Get real-time forex exchange rate. Uses Polygon.io API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "Source currency (e.g., 'USD')", "default": "USD"},
                "to_currency": {"type": "string", "description": "Target currency (e.g., 'EUR', 'CNY')", "default": "EUR"}
            },
            "required": ["from_currency", "to_currency"]
        },
        "handler": forex_rate,
        "cache_ttl": 1800,
    },
    {
        "name": "polygon_market_status",
        "description": "Get current market status for all exchanges (open/closed). Uses Polygon.io API.",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "handler": market_status,
        "cache_ttl": 300,
    },
    {
        "name": "polygon_ticker_news",
        "description": "Get news articles for a stock ticker. Uses Polygon.io API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker (e.g., 'TSM')"},
                "limit": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["ticker"]
        },
        "handler": ticker_news,
        "cache_ttl": 3600,
    },
]
