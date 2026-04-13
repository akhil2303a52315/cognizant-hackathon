"""Alpha Vantage MCP Tools — Real commodity prices, stock time-series, economic indicators."""
import httpx
import os

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.alpha_vantage_api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
    except Exception:
        return os.getenv("ALPHA_VANTAGE_API_KEY", "")


def _mock_commodity(symbol: str) -> dict:
    mock_prices = {
        "WTI": {"price": 78.45, "unit": "USD/barrel"},
        "BRENT": {"price": 82.30, "unit": "USD/barrel"},
        "NATURAL_GAS": {"price": 2.85, "unit": "USD/MMBtu"},
        "COPPER": {"price": 4.25, "unit": "USD/lb"},
        "ALUMINUM": {"price": 2380.00, "unit": "USD/metric ton"},
        "WHEAT": {"price": 6.12, "unit": "USD/bushel"},
        "CORN": {"price": 4.58, "unit": "USD/bushel"},
        "COTTON": {"price": 0.82, "unit": "USD/lb"},
        "IRON_ORE": {"price": 118.50, "unit": "USD/metric ton"},
        "LITHIUM": {"price": 13500.00, "unit": "USD/metric ton"},
    }
    data = mock_prices.get(symbol.upper(), {"price": 100.00, "unit": "USD/unit"})
    return {
        "symbol": symbol,
        "price": data["price"],
        "unit": data["unit"],
        "change_pct_24h": -1.2,
        "source": "alpha_vantage",
        "mock": True,
    }


def _mock_economic_indicator(indicator: str) -> dict:
    return {
        "indicator": indicator,
        "country": "US",
        "value": 52.5,
        "unit": "index",
        "last_updated": "2025-01-15",
        "mock": True,
    }


async def commodity_price(params: dict) -> dict:
    """Get real-time commodity price from Alpha Vantage.

    Args:
        symbol: Commodity symbol (WTI, BRENT, NATURAL_GAS, COPPER, ALUMINUM, WHEAT, CORN, COTTON, IRON_ORE, LITHIUM)
    """
    symbol = params.get("symbol", "WTI")
    key = _get_key()

    if not key:
        return _mock_commodity(symbol)

    function_map = {
        "WTI": "WTI",
        "BRENT": "BRENT",
        "NATURAL_GAS": "NATURAL_GAS",
        "COPPER": "COPPER",
        "ALUMINUM": "ALUMINUM",
        "WHEAT": "WHEAT",
        "CORN": "CORN",
        "COTTON": "COTTON",
        "IRON_ORE": "IRON_ORE",
        "LITHIUM": "LITHIUM",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ALPHA_VANTAGE_BASE, params={
                "function": function_map.get(symbol.upper(), "WTI"),
                "apikey": key,
            })
            data = resp.json()

        # Parse based on response structure
        if "data" in data and isinstance(data["data"], list):
            latest = data["data"][0] if data["data"] else {}
            raw_val = latest.get("value", "0")
            try:
                price = float(raw_val)
            except (ValueError, TypeError):
                price = 0.0
            return {
                "symbol": symbol,
                "name": data.get("name", symbol),
                "price": price,
                "unit": data.get("unit", "USD"),
                "interval": data.get("interval", "monthly"),
                "date": latest.get("date", ""),
                "source": "alpha_vantage",
                "mock": False,
            }

        # Time series format
        if "Time Series (Daily)" in data:
            series = data["Time Series (Daily)"]
            latest_date = next(iter(series), None)
            if latest_date:
                latest = series[latest_date]
                return {
                    "symbol": symbol,
                    "price": float(latest.get("4. close", 0)),
                    "unit": "USD",
                    "date": latest_date,
                    "open": float(latest.get("1. open", 0)),
                    "high": float(latest.get("2. high", 0)),
                    "low": float(latest.get("3. low", 0)),
                    "volume": int(latest.get("5. volume", 0)),
                    "source": "alpha_vantage",
                    "mock": False,
                }

        # Note/Information response (rate limited)
        if "Note" in data:
            return {**_mock_commodity(symbol), "rate_limited": True, "note": data["Note"]}
        if "Information" in data:
            return {**_mock_commodity(symbol), "rate_limited": True, "note": data["Information"]}

        return _mock_commodity(symbol)
    except Exception:
        return _mock_commodity(symbol)


async def stock_time_series(params: dict) -> dict:
    """Get daily stock time-series from Alpha Vantage.

    Args:
        symbol: Stock ticker (e.g., 'TSM', 'AAPL')
        outputsize: 'compact' (100 pts) or 'full' (20+ yrs)
    """
    symbol = params.get("symbol", "AAPL")
    outputsize = params.get("outputsize", "compact")
    key = _get_key()

    if not key:
        return {"symbol": symbol, "data": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ALPHA_VANTAGE_BASE, params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": outputsize,
                "apikey": key,
            })
            data = resp.json()

        if "Time Series (Daily)" in data:
            series = data["Time Series (Daily)"]
            points = []
            for date, vals in list(series.items())[:30]:
                points.append({
                    "date": date,
                    "open": float(vals.get("1. open", 0)),
                    "high": float(vals.get("2. high", 0)),
                    "low": float(vals.get("3. low", 0)),
                    "close": float(vals.get("4. close", 0)),
                    "volume": int(vals.get("5. volume", 0)),
                })
            return {"symbol": symbol, "data": points, "count": len(points), "mock": False}

        if "Note" in data:
            return {"symbol": symbol, "data": [], "rate_limited": True, "mock": True}

        return {"symbol": symbol, "data": [], "mock": True}
    except Exception:
        return {"symbol": symbol, "data": [], "mock": True}


async def economic_indicator(params: dict) -> dict:
    """Get economic indicator from Alpha Vantage (GDP, CPI, PMI, unemployment, etc.).

    Args:
        indicator: Indicator name (REAL_GDP, CPI, INFLATION, UNEMPLOYMENT, MANUFACTURING_PMI, etc.)
        country: Country code (default: 'US')
    """
    indicator = params.get("indicator", "REAL_GDP")
    country = params.get("country", "US")
    key = _get_key()

    if not key:
        return _mock_economic_indicator(indicator)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ALPHA_VANTAGE_BASE, params={
                "function": indicator,
                "country": country,
                "apikey": key,
            })
            data = resp.json()

        if "data" in data and isinstance(data["data"], list):
            points = data["data"][:12]
            return {
                "indicator": indicator,
                "country": country,
                "unit": data.get("unit", ""),
                "data": points,
                "count": len(points),
                "mock": False,
            }

        if "Note" in data:
            return {**_mock_economic_indicator(indicator), "rate_limited": True}

        return _mock_economic_indicator(indicator)
    except Exception:
        return _mock_economic_indicator(indicator)


async def currency_exchange_rate(params: dict) -> dict:
    """Get real-time currency exchange rate from Alpha Vantage.

    Args:
        from_currency: Source currency (e.g., 'USD')
        to_currency: Target currency (e.g., 'CNY')
    """
    from_curr = params.get("from_currency", "USD")
    to_curr = params.get("to_currency", "CNY")
    key = _get_key()

    if not key:
        return {"from": from_curr, "to": to_curr, "rate": 7.24, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ALPHA_VANTAGE_BASE, params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_curr,
                "to_currency": to_curr,
                "apikey": key,
            })
            data = resp.json()

        rate_data = data.get("Realtime Currency Exchange Rate", {})
        if rate_data:
            return {
                "from": from_curr,
                "to": to_curr,
                "rate": float(rate_data.get("5. Exchange Rate", 0)),
                "last_refreshed": rate_data.get("6. Last Refreshed", ""),
                "timezone": rate_data.get("7. Time Zone", ""),
                "mock": False,
            }

        if "Note" in data:
            return {"from": from_curr, "to": to_curr, "rate": 7.24, "rate_limited": True, "mock": True}

        return {"from": from_curr, "to": to_curr, "rate": 7.24, "mock": True}
    except Exception:
        return {"from": from_curr, "to": to_curr, "rate": 7.24, "mock": True}


TOOLS = [
    {
        "name": "av_commodity_price",
        "description": "Get real-time commodity prices (WTI, Brent, natural gas, copper, aluminum, wheat, corn, iron ore, lithium). Uses Alpha Vantage API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Commodity: WTI, BRENT, NATURAL_GAS, COPPER, ALUMINUM, WHEAT, CORN, COTTON, IRON_ORE, LITHIUM", "default": "WTI"}
            },
            "required": ["symbol"]
        },
        "handler": commodity_price,
        "cache_ttl": 300,
    },
    {
        "name": "av_stock_time_series",
        "description": "Get daily stock price time-series (30 days). Uses Alpha Vantage API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker (e.g., 'TSM', 'AAPL')"},
                "outputsize": {"type": "string", "description": "'compact' (100 pts) or 'full'", "default": "compact"}
            },
            "required": ["symbol"]
        },
        "handler": stock_time_series,
        "cache_ttl": 1800,
    },
    {
        "name": "av_economic_indicator",
        "description": "Get economic indicators (GDP, CPI, inflation, unemployment, PMI). Uses Alpha Vantage API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string", "description": "Indicator: REAL_GDP, CPI, INFLATION, UNEMPLOYMENT, MANUFACTURING_PMI", "default": "REAL_GDP"},
                "country": {"type": "string", "description": "Country code (e.g., 'US', 'CN', 'DE')", "default": "US"}
            },
            "required": ["indicator"]
        },
        "handler": economic_indicator,
        "cache_ttl": 86400,
    },
    {
        "name": "av_currency_exchange",
        "description": "Get real-time currency exchange rate. Uses Alpha Vantage API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "Source currency (e.g., 'USD')", "default": "USD"},
                "to_currency": {"type": "string", "description": "Target currency (e.g., 'CNY', 'EUR', 'JPY')", "default": "CNY"}
            },
            "required": ["from_currency", "to_currency"]
        },
        "handler": currency_exchange_rate,
        "cache_ttl": 1800,
    },
]
