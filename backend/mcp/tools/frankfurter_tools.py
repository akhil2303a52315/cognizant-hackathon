"""Frankfurter Forex Rate MCP Tools — Free ECB-sourced exchange rates, no API key needed."""
import httpx

FRANKFURTER_BASE = "https://api.frankfurter.app"


def _mock_exchange_rate(base: str, quote: str) -> dict:
    mock_rates = {"EUR": 0.92, "CNY": 7.24, "JPY": 149.50, "TWD": 31.50, "GBP": 0.79, "KRW": 1320.0, "INR": 83.0}
    return {
        "base": base,
        "rates": {quote: mock_rates.get(quote, 1.0)},
        "date": "2024-01-15",
        "mock": True
    }


async def exchange_rate(params: dict) -> dict:
    """Get latest exchange rate from ECB via Frankfurter. No API key needed.
    
    Args:
        base: Base currency (default: USD)
        quote: Quote currency or comma-separated list (e.g., 'EUR,CNY,JPY')
    """
    base = params.get("base", "USD")
    quote = params.get("quote", "EUR")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(f"{FRANKFURTER_BASE}/latest", params={
                "from": base,
                "to": quote
            })
            data = resp.json()

        return {
            "base": data.get("base", base),
            "rates": data.get("rates", {}),
            "date": data.get("date", ""),
            "mock": False
        }
    except Exception:
        return _mock_exchange_rate(base, quote)


async def historical_rate(params: dict) -> dict:
    """Get historical exchange rate from ECB via Frankfurter. No API key needed.
    
    Args:
        base: Base currency (default: USD)
        quote: Quote currency or comma-separated list
        date: Date in YYYY-MM-DD format
        start_date: Start date for range (YYYY-MM-DD)
        end_date: End date for range (YYYY-MM-DD)
    """
    base = params.get("base", "USD")
    quote = params.get("quote", "EUR")
    date = params.get("date")
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    try:
        params_dict = {"from": base, "to": quote}

        if date:
            url = f"{FRANKFURTER_BASE}/{date}"
        elif start_date and end_date:
            url = f"{FRANKFURTER_BASE}/{start_date}..{end_date}"
        else:
            url = f"{FRANKFURTER_BASE}/latest"

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params_dict)
            data = resp.json()

        return {
            "base": data.get("base", base),
            "rates": data.get("rates", {}),
            "mock": False
        }
    except Exception:
        return _mock_exchange_rate(base, quote)


async def currency_list(params: dict) -> dict:
    """List all available currencies from Frankfurter."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(f"{FRANKFURTER_BASE}/currencies")
            data = resp.json()

        return {"currencies": data, "mock": False}
    except Exception:
        return {"currencies": {"USD": "US Dollar", "EUR": "Euro", "CNY": "Chinese Yuan", "JPY": "Japanese Yen", "TWD": "New Taiwan Dollar"}, "mock": True}


TOOLS = [
    {
        "name": "exchange_rate",
        "description": "Get latest ECB exchange rate. No API key needed. Supports 30+ currencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Base currency (e.g., 'USD')", "default": "USD"},
                "quote": {"type": "string", "description": "Quote currency or CSV list (e.g., 'EUR,CNY,JPY')", "default": "EUR"}
            },
            "required": ["base", "quote"]
        },
        "handler": exchange_rate,
        "cache_ttl": 3600,
    },
    {
        "name": "historical_rate",
        "description": "Get historical ECB exchange rate. Supports single date or date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Base currency", "default": "USD"},
                "quote": {"type": "string", "description": "Quote currency", "default": "EUR"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "start_date": {"type": "string", "description": "Range start (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "Range end (YYYY-MM-DD)"}
            }
        },
        "handler": historical_rate,
        "cache_ttl": 86400,
    },
    {
        "name": "currency_list",
        "description": "List all available currencies from Frankfurter/ECB.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": currency_list,
        "cache_ttl": 86400,
    },
]
