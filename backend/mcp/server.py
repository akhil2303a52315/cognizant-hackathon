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
