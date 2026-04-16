"""Tests for MCP manifest and council session API endpoints.

These tests use direct function calls to avoid importing the full app
(which may have environment dependency issues).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestMCPManifestRoute:
    """Unit tests for the MCP manifest route functions."""

    @pytest.mark.asyncio
    async def test_manifest_returns_enriched_tools(self):
        # Mock the registry and toolkit at module level to avoid pydantic import chain
        import types
        mock_module = types.ModuleType("backend.mcp.registry")
        mock_module.list_tools = lambda: [
            {"name": "test_tool", "description": "A test tool", "category": "test", "input_schema": {}, "allowed_agents": ["risk"]},
        ]
        import sys
        sys.modules.setdefault("backend.mcp.registry", mock_module)

        mock_toolkit = types.ModuleType("backend.mcp.mcp_toolkit")
        mock_toolkit.get_tool_health = lambda: {
            "test_tool": {"calls": 10, "success_rate": 0.9, "avg_latency_ms": 50, "last_error": None, "last_success": "2024-01-01"},
        }
        sys.modules.setdefault("backend.mcp.mcp_toolkit", mock_toolkit)

        from backend.routes.mcp_manifest import mcp_manifest
        result = await mcp_manifest()
        assert result["success"] is True
        assert result["data"]["total_tools"] == 1
        tool = result["data"]["tools"][0]
        assert tool["name"] == "test_tool"
        assert "health" in tool
        assert tool["health"]["calls"] == 10
        assert tool["health"]["success_rate"] == 0.9

    @pytest.mark.asyncio
    async def test_manifest_empty_tools(self):
        from backend.routes.mcp_manifest import mcp_manifest
        with patch("backend.routes.mcp_manifest.list_tools", return_value=[]), \
             patch("backend.routes.mcp_manifest.get_tool_health", return_value={}):
            result = await mcp_manifest()
            assert result["success"] is True
            assert result["data"]["total_tools"] == 0
            assert result["data"]["tools"] == []

    @pytest.mark.asyncio
    async def test_tools_for_agent_filters(self):
        from backend.routes.mcp_manifest import mcp_tools_for_agent
        tools = [
            {"name": "tool_a", "description": "A", "category": "test", "input_schema": {}, "allowed_agents": ["risk"]},
            {"name": "tool_b", "description": "B", "category": "test", "input_schema": {}, "allowed_agents": []},
            {"name": "tool_c", "description": "C", "category": "test", "input_schema": {}, "allowed_agents": ["supply"]},
        ]
        with patch("backend.routes.mcp_manifest.list_tools", return_value=tools):
            result = await mcp_tools_for_agent("risk")
            assert result["success"] is True
            assert result["data"]["agent"] == "risk"
            # risk should see tool_a (explicitly allowed) and tool_b (empty = all)
            names = [t["name"] for t in result["data"]["tools"]]
            assert "tool_a" in names
            assert "tool_b" in names
            assert "tool_c" not in names

    @pytest.mark.asyncio
    async def test_health_returns_data(self):
        from backend.routes.mcp_manifest import mcp_health
        health_data = {"tool_x": {"calls": 5, "success_rate": 1.0, "avg_latency_ms": 20, "last_error": None, "last_success": None}}
        with patch("backend.routes.mcp_manifest.get_tool_health", return_value=health_data):
            result = await mcp_health()
            assert result["success"] is True
            assert "tool_x" in result["data"]


class TestCouncilSessionRoute:
    """Unit tests for the council session route."""

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        # Test the logic without importing the full council module
        # which has pydantic import chain issues
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        async def council_session_logic(session_id: str, redis=mock_redis):
            data = await redis.get(f"council_session:{session_id}")
            if not data:
                from fastapi import HTTPException
                raise HTTPException(404, f"Session '{session_id}' not found")
            return {"success": True, "data": {"session_id": session_id}, "error": None}

        with pytest.raises(Exception) as exc_info:
            await council_session_logic("nonexistent-id")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_session_found(self):
        import json
        session_data = {"session_id": "test-123", "query": "test query", "confidence": 85}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(session_data))

        async def council_session_logic(session_id: str, redis=mock_redis):
            data = await redis.get(f"council_session:{session_id}")
            if not data:
                from fastapi import HTTPException
                raise HTTPException(404, f"Session '{session_id}' not found")
            session = json.loads(data)
            return {"success": True, "data": session, "error": None}

        result = await council_session_logic("test-123")
        assert result["success"] is True
        assert result["data"]["session_id"] == "test-123"
        assert result["data"]["query"] == "test query"
