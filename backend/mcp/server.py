from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRouter
from backend.mcp.registry import list_tools, get_tool, invoke_tool
from backend.mcp.audit import audit_log
from backend.mcp.cache import cache_get, cache_set
import time
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

mcp_app = FastAPI(title="MCP Tool Server", version="1.0.0")


@mcp_app.get("/tools")
async def get_tools():
    return {"tools": list_tools()}


@mcp_app.get("/tools/{tool_name}")
async def get_tool_detail(tool_name: str):
    tool = get_tool(tool_name)
    if not tool:
        raise HTTPException(404, f"Tool '{tool_name}' not found")
    return tool


@mcp_app.post("/tools/{tool_name}/invoke")
async def invoke_tool_endpoint(tool_name: str, request: Request):
    tool = get_tool(tool_name)
    if not tool:
        raise HTTPException(404, f"Tool '{tool_name}' not found")

    body = await request.json()
    agent = request.headers.get("X-Agent-Name", "unknown")
    start = time.time()

    input_hash = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

    cached_result = await cache_get(f"mcp:{tool_name}:{input_hash}")
    if cached_result:
        latency = int((time.time() - start) * 1000)
        await audit_log(tool=tool_name, agent=agent, input_hash=input_hash,
                        latency_ms=latency, was_cached=True)
        return {"result": cached_result, "cached": True, "tool": tool_name}

    try:
        result = await invoke_tool(tool_name, body)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"MCP tool error: {e}")
        raise HTTPException(500, f"Tool execution failed: {e}")

    latency = int((time.time() - start) * 1000)
    await audit_log(tool=tool_name, agent=agent, input_hash=input_hash,
                    latency_ms=latency, was_cached=False)

    ttl = tool.get("cache_ttl", 3600)
    await cache_set(f"mcp:{tool_name}:{input_hash}", result, ttl=ttl)

    return {"result": result, "cached": False, "tool": tool_name, "latency_ms": latency}


@mcp_app.get("/audit")
async def get_audit_logs(limit: int = 50):
    from backend.db.neon import execute_query
    rows = await execute_query(
        "SELECT * FROM mcp_audit_log ORDER BY created_at DESC LIMIT $1", limit
    )
    return {"logs": [dict(r) for r in rows]}


@mcp_app.get("/health")
async def mcp_health():
    return {"status": "ok", "tools_registered": len(list_tools())}


# ---------------------------------------------------------------------------
# Day 4: MCP Toolkit + Secure Execution endpoints
# ---------------------------------------------------------------------------
@mcp_app.get("/manifest")
async def get_manifest():
    """Return the complete tool discovery manifest with server groupings and agent scopes."""
    from backend.mcp.mcp_servers import get_tool_manifest
    return get_tool_manifest()


@mcp_app.get("/servers")
async def get_servers():
    """Return all MCP server definitions."""
    from backend.mcp.mcp_servers import get_all_server_definitions
    return get_all_server_definitions()


@mcp_app.get("/agent/{agent_name}/tools")
async def get_agent_tools(agent_name: str):
    """Return the tools allowed for a specific agent."""
    from backend.mcp.mcp_servers import get_agent_allowed_tools, get_agent_servers
    tools = get_agent_allowed_tools(agent_name)
    servers = [s.name for s in get_agent_servers(agent_name)]
    return {"agent": agent_name, "tools": tools, "servers": servers}


@mcp_app.post("/secure-invoke")
async def secure_invoke_endpoint(request: Request):
    """Secure MCP invocation with sandboxing, guardrails, rate limiting, and audit.

    Body: {"tool": "...", "params": {...}, "agent": "..."}
    """
    body = await request.json()
    tool_name = body.get("tool", "")
    params = body.get("params", {})
    agent = body.get("agent", request.headers.get("X-Agent-Name", "unknown"))

    if not tool_name:
        raise HTTPException(422, "Missing 'tool' parameter")

    from backend.mcp.secure_mcp import secure_invoke
    result = await secure_invoke(agent, tool_name, params)

    if not result.get("scope_valid"):
        raise HTTPException(403, result.get("warnings", ["Scope violation"])[0])
    if result.get("rate_limited"):
        raise HTTPException(429, "Rate limit exceeded")
    if not result.get("success"):
        raise HTTPException(500, result.get("warnings", ["Execution failed"])[0])

    return result


@mcp_app.get("/tool-health")
async def tool_health():
    """Return health stats for all tracked MCP tools."""
    from backend.mcp.mcp_toolkit import get_tool_health
    return get_tool_health()


@mcp_app.get("/rate-limit/{agent_name}")
async def rate_limit_status(agent_name: str):
    """Return current rate limit status for an agent."""
    from backend.mcp.secure_mcp import get_rate_limit_status
    return get_rate_limit_status(agent_name)


@mcp_app.post("/agent/{agent_name}/health-check")
async def agent_mcp_health_check(agent_name: str):
    """Run health checks for all MCP servers available to an agent."""
    from backend.mcp.mcp_toolkit import get_mcp_client
    try:
        client = get_mcp_client(agent_name)
        return await client.health_check()
    except Exception as e:
        raise HTTPException(500, f"Health check failed: {e}")
