from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _commodity_price(params: dict):
    commodity = params.get("commodity", "")
    return {
        "commodity": commodity,
        "price_usd": 142.50,
        "unit": "per metric ton",
        "change_24h_pct": -1.2,
        "change_30d_pct": 5.8,
        "52w_high": 165.00,
        "52w_low": 98.00,
        "mock": True,
    }


async def _trade_data(params: dict):
    commodity = params.get("commodity", "")
    country = params.get("country", "")
    return {
        "commodity": commodity,
        "country": country,
        "export_volume_tonnes": 125000,
        "import_volume_tonnes": 89000,
        "trade_balance": 36000,
        "yoy_change_pct": 3.2,
        "top_partners": ["China", "USA", "Germany"],
        "mock": True,
    }


async def _tariff_lookup(params: dict):
    hs_code = params.get("hs_code", "")
    origin = params.get("origin_country", "")
    destination = params.get("destination_country", "")
    return {
        "hs_code": hs_code,
        "origin": origin,
        "destination": destination,
        "tariff_rate_pct": 7.5,
        "anti_dumping": False,
        "quota_applies": False,
        "trade_agreement": "WTO MFN",
        "effective_date": "2025-01-01",
        "mock": True,
    }


def register():
    register_tool(
        name="commodity_price",
        description="Get current commodity prices and trends",
        input_schema={
            "type": "object",
            "properties": {
                "commodity": {"type": "string", "description": "Commodity name (e.g., copper, lithium)"},
            },
            "required": ["commodity"],
        },
        handler=_commodity_price,
        category="commodity",
        cache_ttl=3600,
    )
    register_tool(
        name="trade_data",
        description="Get trade volume data for commodities by country",
        input_schema={
            "type": "object",
            "properties": {
                "commodity": {"type": "string", "description": "Commodity name"},
                "country": {"type": "string", "description": "Country code", "default": ""},
            },
            "required": ["commodity"],
        },
        handler=_trade_data,
        category="commodity",
        cache_ttl=7200,
    )
    register_tool(
        name="tariff_lookup",
        description="Look up tariff rates by HS code and country pair",
        input_schema={
            "type": "object",
            "properties": {
                "hs_code": {"type": "string", "description": "HS code for the product"},
                "origin_country": {"type": "string", "description": "Origin country"},
                "destination_country": {"type": "string", "description": "Destination country"},
            },
            "required": ["hs_code"],
        },
        handler=_tariff_lookup,
        category="commodity",
        cache_ttl=86400,
    )
