"""MCP manifest and health endpoints for frontend integration."""

from fastapi import APIRouter
from backend.mcp.registry import list_tools
from backend.mcp.mcp_toolkit import get_tool_health

router = APIRouter()


@router.get("/manifest")
async def mcp_manifest():
    """Return the full MCP tool manifest with health stats.

    Each tool includes: name, description, category, input_schema,
    allowed_agents, and live health stats (calls, success_rate, avg_latency).
    """
    tools = list_tools()
    health = get_tool_health()

    enriched = []
    for t in tools:
        h = health.get(t["name"], {})
        enriched.append({
            **t,
            "health": {
                "calls": h.get("calls", 0),
                "success_rate": h.get("success_rate", 0),
                "avg_latency_ms": h.get("avg_latency_ms", 0),
                "last_error": h.get("last_error"),
                "last_success": h.get("last_success"),
            },
        })

    categories = sorted(set(t["category"] for t in tools))

    return {
        "success": True,
        "data": {
            "tools": enriched,
            "categories": categories,
            "total_tools": len(enriched),
        },
        "error": None,
    }


@router.get("/tools/{agent}")
async def mcp_tools_for_agent(agent: str):
    """Return MCP tools available to a specific agent."""
    tools = list_tools()
    filtered = [t for t in tools if agent in t.get("allowed_agents", []) or not t.get("allowed_agents")]

    return {
        "success": True,
        "data": {
            "agent": agent,
            "tools": filtered,
            "total": len(filtered),
        },
        "error": None,
    }


@router.get("/health")
async def mcp_health():
    """Return health stats for all MCP tools."""
    health = get_tool_health()
    return {
        "success": True,
        "data": health,
        "error": None,
    }
