"""Dynamic MCP client toolkit for SupplyChainGPT Council.

Provides MultiServerMCPClient that:
  - Discovers available tools from the registry
  - Filters tools per agent via least-privilege scopes from mcp_servers.py
  - Converts MCP tools to LangChain Tool objects for ReAct agent integration
  - Supports tool schema evolution with cached fallback
  - Tracks tool health and availability
"""

import json
import time
import logging
from typing import Optional
from datetime import datetime, timezone

from backend.mcp.mcp_servers import (
    MCP_SERVERS,
    AGENT_SERVER_MAP,
    get_agent_allowed_tools,
    get_agent_servers,
    is_tool_allowed_for_agent,
    get_tool_manifest,
)
from backend.mcp.registry import list_tools, get_tool, invoke_tool
from backend.mcp.cache import cache_get, cache_set
from backend.mcp.audit import audit_log

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool health tracker
# ---------------------------------------------------------------------------
_tool_health: dict[str, dict] = {}


def _update_tool_health(tool_name: str, success: bool, latency_ms: int, error: Optional[str] = None):
    """Track per-tool health stats: success rate, avg latency, last error."""
    if tool_name not in _tool_health:
        _tool_health[tool_name] = {
            "calls": 0, "successes": 0, "failures": 0,
            "total_latency_ms": 0, "last_error": None, "last_success": None,
        }
    h = _tool_health[tool_name]
    h["calls"] += 1
    h["total_latency_ms"] += latency_ms
    if success:
        h["successes"] += 1
        h["last_success"] = datetime.now(timezone.utc).isoformat()
    else:
        h["failures"] += 1
        h["last_error"] = error


def get_tool_health() -> dict:
    """Return health stats for all tracked tools."""
    result = {}
    for name, h in _tool_health.items():
        avg_latency = h["total_latency_ms"] / max(h["calls"], 1)
        success_rate = h["successes"] / max(h["calls"], 1)
        result[name] = {
            "calls": h["calls"],
            "success_rate": round(success_rate, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "last_success": h["last_success"],
            "last_error": h["last_error"],
            "status": "healthy" if success_rate > 0.8 else ("degraded" if success_rate > 0.5 else "failing"),
        }
    return result


# ---------------------------------------------------------------------------
# Schema evolution: cache tool schemas, detect drift, fallback
# ---------------------------------------------------------------------------
SCHEMA_CACHE_PREFIX = "mcp_schema:"


async def _get_cached_schema(tool_name: str) -> Optional[dict]:
    """Get the cached schema for a tool (for fallback if schema evolves)."""
    return await cache_get(f"{SCHEMA_CACHE_PREFIX}{tool_name}")


async def _cache_schema(tool_name: str, schema: dict):
    """Cache a tool's input schema for fallback during evolution."""
    await cache_set(f"{SCHEMA_CACHE_PREFIX}{tool_name}", schema, ttl=86400)


async def get_tool_schema_with_fallback(tool_name: str) -> Optional[dict]:
    """Get a tool's current schema, falling back to cached version if missing.

    Handles schema evolution: if a tool's schema changes or becomes
    unavailable, we fall back to the last known good schema from Redis.
    """
    # Try current registry
    tool_info = get_tool(tool_name)
    if tool_info and tool_info.get("input_schema"):
        current = tool_info["input_schema"]
        # Cache the current schema
        await _cache_schema(tool_name, current)
        return current

    # Fallback to cached schema
    cached = await _get_cached_schema(tool_name)
    if cached:
        logger.warning(f"Tool '{tool_name}' schema unavailable — using cached fallback")
        return cached

    logger.error(f"Tool '{tool_name}' schema unavailable and no cached fallback")
    return None


# ---------------------------------------------------------------------------
# MultiServerMCPClient
# ---------------------------------------------------------------------------
class MultiServerMCPClient:
    """Dynamic MCP client that manages tool discovery, scoping, and invocation.

    Each agent gets its own scoped client that can only access tools
    permitted by the least-privilege AGENT_SERVER_MAP.

    Usage:
        client = MultiServerMCPClient(agent_name="risk")
        tools = client.get_langchain_tools()
        result = await client.invoke("gdelt_search_events", {"query": "conflict"})
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.allowed_tools = get_agent_allowed_tools(agent_name)
        self.servers = get_agent_servers(agent_name)
        self._tool_cache: dict[str, dict] = {}

    def get_available_tools(self) -> list[dict]:
        """Return the list of tools this agent is allowed to use."""
        all_tools = list_tools()
        allowed_set = set(self.allowed_tools)
        return [t for t in all_tools if t["name"] in allowed_set]

    def get_tool_categories(self) -> dict[str, list[str]]:
        """Return tools grouped by server category."""
        result = {}
        for server in self.servers:
            available = [t for t in server.tools if t in self.allowed_tools]
            if available:
                result[server.name] = available
        return result

    async def invoke(self, tool_name: str, params: dict, use_cache: bool = True) -> dict:
        """Invoke an MCP tool with scope validation, caching, and audit logging.

        Args:
            tool_name: Name of the tool to invoke
            params: Parameters to pass to the tool
            use_cache: Whether to check Redis cache first (default True)

        Returns:
            dict with 'result', 'cached', 'tool', 'latency_ms', 'scope_valid'
        """
        start = time.time()

        # Scope validation
        if not is_tool_allowed_for_agent(tool_name, self.agent_name):
            latency = int((time.time() - start) * 1000)
            logger.warning(f"[{self.agent_name}] Scope violation: tool '{tool_name}' not allowed")
            _update_tool_health(tool_name, False, latency, "scope_violation")
            return {
                "result": None,
                "error": f"Tool '{tool_name}' not allowed for agent '{self.agent_name}'",
                "cached": False,
                "tool": tool_name,
                "latency_ms": latency,
                "scope_valid": False,
            }

        # Cache check
        if use_cache:
            import hashlib
            input_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
            cached_result = await cache_get(f"mcp:{tool_name}:{input_hash}")
            if cached_result is not None:
                latency = int((time.time() - start) * 1000)
                await audit_log(tool=tool_name, agent=self.agent_name,
                               input_hash=input_hash, latency_ms=latency, was_cached=True)
                _update_tool_health(tool_name, True, latency)
                return {"result": cached_result, "cached": True, "tool": tool_name, "latency_ms": latency, "scope_valid": True}

        # Invoke tool
        try:
            result = await invoke_tool(tool_name, params)
            latency = int((time.time() - start) * 1000)

            # Cache the result
            if use_cache:
                tool_info = get_tool(tool_name)
                ttl = tool_info.get("cache_ttl", 3600) if tool_info else 3600
                await cache_set(f"mcp:{tool_name}:{input_hash}", result, ttl=ttl)

            # Audit log
            await audit_log(tool=tool_name, agent=self.agent_name,
                           input_hash=input_hash, latency_ms=latency, was_cached=False)

            _update_tool_health(tool_name, True, latency)
            return {"result": result, "cached": False, "tool": tool_name, "latency_ms": latency, "scope_valid": True}

        except PermissionError as e:
            latency = int((time.time() - start) * 1000)
            _update_tool_health(tool_name, False, latency, str(e))
            return {"result": None, "error": f"Permission denied: {e}", "cached": False, "tool": tool_name, "latency_ms": latency, "scope_valid": True}
        except ValueError as e:
            latency = int((time.time() - start) * 1000)
            _update_tool_health(tool_name, False, latency, str(e))
            return {"result": None, "error": f"Invalid input: {e}", "cached": False, "tool": tool_name, "latency_ms": latency, "scope_valid": True}
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            _update_tool_health(tool_name, False, latency, str(e))
            return {"result": None, "error": str(e), "cached": False, "tool": tool_name, "latency_ms": latency, "scope_valid": True}

    def get_langchain_tools(self) -> list:
        """Convert allowed MCP tools to LangChain Tool objects for ReAct integration.

        Each tool is wrapped with async coroutine that goes through the
        scoped invoke method (with caching, audit, scope validation).
        """
        from langchain_core.tools import Tool

        tools = []
        for tool_info in self.get_available_tools():
            name = tool_info["name"]
            agent = self.agent_name

            async def _make_coroutine(tool_name: str, ag: str):
                async def arun(query: str) -> str:
                    try:
                        params = json.loads(query) if query.startswith("{") else {"query": query}
                    except json.JSONDecodeError:
                        params = {"query": query}
                    client = MultiServerMCPClient(ag)
                    result = await client.invoke(tool_name, params)
                    if result.get("error"):
                        return f"Error: {result['error']}"
                    return json.dumps(result["result"], default=str)
                return arun

            def _make_sync(tool_name: str, ag: str):
                def run(query: str) -> str:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    try:
                        params = json.loads(query) if query.startswith("{") else {"query": query}
                    except json.JSONDecodeError:
                        params = {"query": query}
                    client = MultiServerMCPClient(ag)
                    result = loop.run_until_complete(client.invoke(tool_name, params))
                    if result.get("error"):
                        return f"Error: {result['error']}"
                    return json.dumps(result["result"], default=str)
                return run

            tool = Tool(
                name=name,
                description=tool_info["description"],
                func=_make_sync(name, agent),
                coroutine=_make_coroutine(name, agent)(),
            )
            tools.append(tool)

        return tools

    async def health_check(self) -> dict:
        """Check health of all servers this agent has access to."""
        results = {}
        for server in self.servers:
            if server.health_check_tool:
                try:
                    resp = await self.invoke(server.health_check_tool, {}, use_cache=False)
                    results[server.name] = "ok" if resp.get("result") is not None else "error"
                except Exception:
                    results[server.name] = "error"
            else:
                results[server.name] = "unknown"
        return {"agent": self.agent_name, "servers": results}


# ---------------------------------------------------------------------------
# Singleton clients per agent
# ---------------------------------------------------------------------------
_agent_clients: dict[str, MultiServerMCPClient] = {}


def get_mcp_client(agent_name: str) -> MultiServerMCPClient:
    """Get or create a scoped MCP client for an agent."""
    if agent_name not in _agent_clients:
        _agent_clients[agent_name] = MultiServerMCPClient(agent_name)
        logger.info(f"Created MCP client for agent '{agent_name}' with {len(_agent_clients[agent_name].allowed_tools)} tools")
    return _agent_clients[agent_name]


def get_all_mcp_clients() -> dict[str, MultiServerMCPClient]:
    """Return all created MCP clients."""
    return _agent_clients


def init_all_mcp_clients():
    """Pre-initialize MCP clients for all 7 agents."""
    for agent_name in AGENT_SERVER_MAP:
        get_mcp_client(agent_name)
    logger.info(f"Initialized MCP clients for {len(_agent_clients)} agents")
