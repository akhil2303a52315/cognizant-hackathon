"""Tests for MCP server definitions, agent scopes, and tool manifest."""

import pytest
from backend.mcp.mcp_servers import (
    MCP_SERVERS, AGENT_SERVER_MAP, MCPServerDef,
    get_agent_allowed_tools, get_agent_servers, get_server_for_tool,
    is_tool_allowed_for_agent, get_all_server_definitions, get_tool_manifest,
)


def test_all_servers_defined():
    expected = ["news_geopolitical", "shipping_logistics", "erp_inventory",
                "finance_market", "web_intel", "rag"]
    for name in expected:
        assert name in MCP_SERVERS, f"Missing server: {name}"


def test_server_structure():
    for name, server in MCP_SERVERS.items():
        assert isinstance(server, MCPServerDef)
        assert len(server.tools) > 0, f"{name} has no tools"
        assert len(server.allowed_agents) > 0, f"{name} has no allowed agents"
        assert server.rate_limit_per_minute > 0
        assert server.description


def test_agent_server_map_complete():
    expected_agents = ["risk", "supply", "logistics", "market", "finance", "brand", "moderator"]
    for agent in expected_agents:
        assert agent in AGENT_SERVER_MAP, f"Missing agent: {agent}"
        servers = AGENT_SERVER_MAP[agent]
        assert len(servers) > 0, f"{agent} has no servers"


def test_moderator_has_all_servers():
    assert len(AGENT_SERVER_MAP["moderator"]) == len(MCP_SERVERS)


def test_get_agent_allowed_tools():
    risk_tools = get_agent_allowed_tools("risk")
    assert "news_search" in risk_tools or "gdelt_search_events" in risk_tools
    # Risk should NOT have shipping tools
    assert "route_optimize" not in risk_tools


def test_logistics_has_shipping():
    log_tools = get_agent_allowed_tools("logistics")
    assert "route_optimize" in log_tools
    # Logistics should NOT have finance tools
    assert "finnhub_stock_quote" not in log_tools


def test_is_tool_allowed():
    assert is_tool_allowed_for_agent("route_optimize", "logistics") is True
    assert is_tool_allowed_for_agent("route_optimize", "risk") is False
    assert is_tool_allowed_for_agent("rag_query", "risk") is True


def test_get_server_for_tool():
    server = get_server_for_tool("route_optimize")
    assert server is not None
    assert server.name == "shipping_logistics"

    server = get_server_for_tool("nonexistent_tool")
    assert server is None


def test_get_agent_servers():
    servers = get_agent_servers("risk")
    names = [s.name for s in servers]
    assert "news_geopolitical" in names
    assert "rag" in names


def test_tool_manifest():
    manifest = get_tool_manifest()
    assert "servers" in manifest
    assert "agent_scopes" in manifest
    assert manifest["total_tools"] > 0
    assert manifest["total_servers"] == len(MCP_SERVERS)


def test_all_server_definitions():
    defs = get_all_server_definitions()
    assert len(defs) == len(MCP_SERVERS)
    for name, d in defs.items():
        assert "tools" in d
        assert "allowed_agents" in d
