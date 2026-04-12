from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _route_optimize(params: dict):
    origin = params.get("origin", "")
    destination = params.get("destination", "")
    constraints = params.get("constraints", {})
    return {
        "routes": [
            {"origin": origin, "destination": destination, "mode": "sea", "cost": 1200, "transit_days": 21, "co2_kg": 450},
            {"origin": origin, "destination": destination, "mode": "air", "cost": 3800, "transit_days": 3, "co2_kg": 2100},
            {"origin": origin, "destination": destination, "mode": "rail", "cost": 1800, "transit_days": 12, "co2_kg": 800},
        ],
        "recommended": "sea",
        "constraints": constraints,
        "mock": True,
    }


async def _port_status(params: dict):
    port = params.get("port", "")
    return {
        "port": port,
        "status": "operational",
        "congestion_level": "moderate",
        "avg_wait_hours": 18,
        "vessels_in_queue": 7,
        "last_updated": "2025-01-15T10:00:00Z",
        "mock": True,
    }


async def _freight_rate(params: dict):
    route = params.get("route", "")
    cargo_type = params.get("cargo_type", "container")
    return {
        "route": route,
        "cargo_type": cargo_type,
        "current_rate_usd": 2850,
        "rate_trend": "increasing",
        "change_pct_30d": 8.5,
        "benchmark_rate": 2600,
        "mock": True,
    }


def register():
    register_tool(
        name="route_optimize",
        description="Optimize shipping routes between origin and destination",
        input_schema={
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin port/city"},
                "destination": {"type": "string", "description": "Destination port/city"},
                "constraints": {"type": "object", "description": "Constraints (budget, time, co2)"},
            },
            "required": ["origin", "destination"],
        },
        handler=_route_optimize,
        category="shipping",
        cache_ttl=3600,
    )
    register_tool(
        name="port_status",
        description="Get current port congestion and operational status",
        input_schema={
            "type": "object",
            "properties": {
                "port": {"type": "string", "description": "Port name or code"},
            },
            "required": ["port"],
        },
        handler=_port_status,
        category="shipping",
        cache_ttl=1800,
    )
    register_tool(
        name="freight_rate",
        description="Get current freight rates for a shipping route",
        input_schema={
            "type": "object",
            "properties": {
                "route": {"type": "string", "description": "Shipping route (e.g., 'Asia-Europe')"},
                "cargo_type": {"type": "string", "description": "Cargo type", "default": "container"},
            },
            "required": ["route"],
        },
        handler=_freight_rate,
        category="shipping",
        cache_ttl=3600,
    )
