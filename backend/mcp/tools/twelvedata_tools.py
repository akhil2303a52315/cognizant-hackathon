"""Twelve Data MCP Tools — Real-time stocks, forex, crypto from 80+ exchanges."""
import httpx
import os

TWELVEDATA_BASE = "https://api.twelvedata.com"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.twelvedata_api_key or os.getenv("TWELVEDATA_API_KEY", "")
    except Exception:
        return os.getenv("TWELVEDATA_API_KEY", "")


def _mock_time_series(symbol: str) -> dict:
    return {"symbol": symbol, "values": [], "mock": True}


def _mock_forex(pair: str) -> dict:
    return {"pair": pair, "rate": 1.0, "mock": True}


async def time_series(params: dict) -> dict:
    """Get stock/forex/crypto time series from Twelve Data.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'USD/EUR', 'BTC/USD')
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points (default: 30)
    """
    symbol = params.get("symbol", "AAPL")
    interval = params.get("interval", "1day")
    outputsize = params.get("outputsize", 30)
    key = _get_key()

    if not key:
        return _mock_time_series(symbol)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{TWELVEDATA_BASE}/time_series", params={
                "symbol": symbol, "interval": interval, "outputsize": outputsize, "apikey": key,
            })
            data = resp.json()

        if "values" in data and data["values"]:
            values = []
            for v in data["values"][:30]:
                values.append({
                    "datetime": v.get("datetime", ""),
                    "open": float(v.get("open", 0)),
                    "high": float(v.get("high", 0)),
                    "low": float(v.get("low", 0)),
                    "close": float(v.get("close", 0)),
                    "volume": int(v.get("volume", 0) or 0),
                })
            return {"symbol": symbol, "interval": interval, "values": values, "count": len(values), "mock": False}

        if data.get("status") == "error":
            return {**_mock_time_series(symbol), "error": data.get("message", "")}

        return _mock_time_series(symbol)
    except Exception:
        return _mock_time_series(symbol)


async def price_quote(params: dict) -> dict:
    """Get real-time price quote from Twelve Data.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'TSM', 'USD/EUR')
    """
    symbol = params.get("symbol", "AAPL")
    key = _get_key()

    if not key:
        return {"symbol": symbol, "price": 0, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TWELVEDATA_BASE}/price", params={
                "symbol": symbol, "apikey": key,
            })
            data = resp.json()

        if "price" in data:
            return {
                "symbol": symbol,
                "price": float(data["price"]),
                "mock": False,
            }

        if data.get("status") == "error":
            return {"symbol": symbol, "price": 0, "error": data.get("message", ""), "mock": True}

        return {"symbol": symbol, "price": 0, "mock": True}
    except Exception:
        return {"symbol": symbol, "price": 0, "mock": True}


async def forex_rate(params: dict) -> dict:
    """Get real-time forex rate from Twelve Data.

    Args:
        pair: Currency pair (e.g., 'USD/EUR', 'USD/CNY')
    """
    pair = params.get("pair", "USD/EUR")
    key = _get_key()

    if not key:
        return _mock_forex(pair)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TWELVEDATA_BASE}/price", params={
                "symbol": pair, "apikey": key,
            })
            data = resp.json()

        if "price" in data:
            return {"pair": pair, "rate": float(data["price"]), "mock": False}

        return _mock_forex(pair)
    except Exception:
        return _mock_forex(pair)


async def market_movers(params: dict) -> dict:
    """Get top market movers (gainers/losers) from Twelve Data.

    Args:
        exchange: Exchange code (e.g., 'NASDAQ', 'NYSE')
    """
    exchange = params.get("exchange", "NASDAQ")
    key = _get_key()

    if not key:
        return {"gainers": [], "losers": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TWELVEDATA_BASE}/market_movers", params={
                "exchange": exchange, "apikey": key,
            })
            data = resp.json()

        # Handle various response formats
        if data.get("status") == "error":
            return {"gainers": [], "losers": [], "error": data.get("message", ""), "mock": True}

        gainers = []
        gainers_raw = data.get("gainers", [])
        if isinstance(gainers_raw, list):
            for g in gainers_raw[:5]:
                if isinstance(g, dict):
                    gainers.append({"symbol": g.get("symbol", ""), "price": float(g.get("price", 0) or 0), "change_pct": float(g.get("change_percent", 0) or 0)})

        losers = []
        losers_raw = data.get("losers", [])
        if isinstance(losers_raw, list):
            for l in losers_raw[:5]:
                if isinstance(l, dict):
                    losers.append({"symbol": l.get("symbol", ""), "price": float(l.get("price", 0) or 0), "change_pct": float(l.get("change_percent", 0) or 0)})

        if gainers or losers:
            return {"exchange": exchange, "gainers": gainers, "losers": losers, "mock": False}

        return {"gainers": [], "losers": [], "mock": True}
    except Exception:
        return {"gainers": [], "losers": [], "mock": True}


TOOLS = [
    {
        "name": "td_time_series",
        "description": "Get stock/forex/crypto time series (OHLCV). Uses Twelve Data API. 80+ exchanges.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker (e.g., 'AAPL', 'USD/EUR', 'BTC/USD')"},
                "interval": {"type": "string", "description": "Interval: 1min,5min,15min,1h,4h,1day,1week,1month", "default": "1day"},
                "outputsize": {"type": "integer", "description": "Data points", "default": 30}
            },
            "required": ["symbol"]
        },
        "handler": time_series,
        "cache_ttl": 300,
    },
    {
        "name": "td_price_quote",
        "description": "Get real-time price quote. Uses Twelve Data API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker (e.g., 'AAPL', 'TSM')"}
            },
            "required": ["symbol"]
        },
        "handler": price_quote,
        "cache_ttl": 60,
    },
    {
        "name": "td_forex_rate",
        "description": "Get real-time forex rate. Uses Twelve Data API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pair": {"type": "string", "description": "Currency pair (e.g., 'USD/EUR')", "default": "USD/EUR"}
            },
            "required": ["pair"]
        },
        "handler": forex_rate,
        "cache_ttl": 300,
    },
    {
        "name": "td_market_movers",
        "description": "Get top market gainers/losers. Uses Twelve Data API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exchange": {"type": "string", "description": "Exchange (NASDAQ, NYSE)", "default": "NASDAQ"}
            },
            "required": []
        },
        "handler": market_movers,
        "cache_ttl": 300,
    },
]
