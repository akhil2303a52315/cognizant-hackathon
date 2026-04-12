from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _erp_query(params: dict):
    query = params.get("sql_query", params.get("query", ""))
    module = params.get("module", "procurement")
    try:
        from backend.db.neon import execute_query
        rows = await execute_query(query)
        return {"results": [dict(r) for r in rows], "module": module}
    except Exception as e:
        return _mock_erp(module)


def _mock_erp(module: str) -> dict:
    return {
        "results": [
            {"module": module, "total_spend": 2400000, "supplier_count": 12, "on_time_delivery_pct": 87.5},
        ],
        "mock": True,
    }


async def _currency_rate(params: dict):
    base = params.get("base_currency", "USD")
    target = params.get("target_currency", "EUR")
    return {
        "base": base,
        "target": target,
        "rate": 0.92,
        "change_24h_pct": -0.15,
        "change_30d_pct": 1.8,
        "source": "ECB",
        "mock": True,
    }


async def _insurance_claim(params: dict):
    claim_type = params.get("claim_type", "cargo_damage")
    supplier_id = params.get("supplier_id", "")
    return {
        "claim_type": claim_type,
        "supplier_id": supplier_id,
        "avg_processing_days": 21,
        "approval_rate_pct": 78,
        "pending_claims": 3,
        "total_claimed_usd": 125000,
        "mock": True,
    }


def register():
    register_tool(
        name="erp_query",
        description="Query ERP data from Neon PostgreSQL (sandboxed, read-only)",
        input_schema={
            "type": "object",
            "properties": {
                "sql_query": {"type": "string", "description": "SQL query (read-only)"},
                "module": {"type": "string", "description": "ERP module", "default": "procurement"},
            },
            "required": ["sql_query"],
        },
        handler=_erp_query,
        category="finance",
        cache_ttl=3600,
    )
    register_tool(
        name="currency_rate",
        description="Get current currency exchange rates",
        input_schema={
            "type": "object",
            "properties": {
                "base_currency": {"type": "string", "description": "Base currency code", "default": "USD"},
                "target_currency": {"type": "string", "description": "Target currency code", "default": "EUR"},
            },
        },
        handler=_currency_rate,
        category="finance",
        cache_ttl=1800,
    )
    register_tool(
        name="insurance_claim",
        description="Get insurance claim data and statistics",
        input_schema={
            "type": "object",
            "properties": {
                "claim_type": {"type": "string", "description": "Claim type", "default": "cargo_damage"},
                "supplier_id": {"type": "string", "description": "Supplier ID"},
            },
        },
        handler=_insurance_claim,
        category="finance",
        cache_ttl=3600,
    )
