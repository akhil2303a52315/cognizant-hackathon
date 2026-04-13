"""ExchangeRate-API MCP Tools — Reliable forex rates from exchange rate API."""
import httpx
import os

EXR_BASE = "https://v6.exchangerate-api.com/v6"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.exchangerate_api_key or os.getenv("EXCHANGERATE_API_KEY", "")
    except Exception:
        return os.getenv("EXCHANGERATE_API_KEY", "")


def _mock_rate(base: str, target: str) -> dict:
    return {"base": base, "target": target, "rate": 1.0, "mock": True}


async def latest_rates(params: dict) -> dict:
    """Get latest exchange rates for a base currency from ExchangeRate-API.

    Args:
        base: Base currency code (e.g., 'USD', 'EUR')
    """
    base = params.get("base", "USD")
    key = _get_key()

    if not key:
        return {"base": base, "rates": {}, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{EXR_BASE}/{key}/latest/{base}")
            data = resp.json()

        if data.get("result") == "success" and "conversion_rates" in data:
            return {
                "base": data.get("base_code", base),
                "rates": data["conversion_rates"],
                "last_updated": data.get("time_last_update_utc", ""),
                "mock": False,
            }

        return {"base": base, "rates": {}, "mock": True}
    except Exception:
        return {"base": base, "rates": {}, "mock": True}


async def pair_conversion(params: dict) -> dict:
    """Convert amount between two currencies using ExchangeRate-API.

    Args:
        base: Source currency (e.g., 'USD')
        target: Target currency (e.g., 'CNY')
        amount: Amount to convert (default: 1)
    """
    base = params.get("base", "USD")
    target = params.get("target", "CNY")
    amount = params.get("amount", 1)
    key = _get_key()

    if not key:
        return _mock_rate(base, target)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{EXR_BASE}/{key}/pair/{base}/{target}/{amount}")
            data = resp.json()

        if data.get("result") == "success":
            return {
                "base": base,
                "target": target,
                "rate": data.get("conversion_rate", 0),
                "converted_amount": data.get("conversion_result", 0),
                "mock": False,
            }

        return _mock_rate(base, target)
    except Exception:
        return _mock_rate(base, target)


TOOLS = [
    {
        "name": "exr_latest_rates",
        "description": "Get latest exchange rates for a base currency. Uses ExchangeRate-API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Base currency (e.g., 'USD')", "default": "USD"}
            },
            "required": []
        },
        "handler": latest_rates,
        "cache_ttl": 3600,
    },
    {
        "name": "exr_pair_conversion",
        "description": "Convert amount between two currencies. Uses ExchangeRate-API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Source currency", "default": "USD"},
                "target": {"type": "string", "description": "Target currency", "default": "CNY"},
                "amount": {"type": "number", "description": "Amount to convert", "default": 1}
            },
            "required": ["base", "target"]
        },
        "handler": pair_conversion,
        "cache_ttl": 1800,
    },
]
