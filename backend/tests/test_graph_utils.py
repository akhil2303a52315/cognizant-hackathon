"""Tests for graph_utils: safe_execute_node and node_error_handler."""

import pytest
from backend.graph_utils import safe_execute_node, node_error_handler


# ---------------------------------------------------------------------------
# safe_execute_node
# ---------------------------------------------------------------------------
class TestSafeExecuteNode:
    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        async def good_node(state):
            return {"predictions": [1, 2, 3]}

        result = await safe_execute_node(
            "predictions", good_node, {"predictions": []}, {}
        )
        assert result == {"predictions": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_failure_returns_fallback(self):
        async def bad_node(state):
            raise RuntimeError("boom")

        result = await safe_execute_node(
            "predictions", bad_node, {"predictions": []}, {}
        )
        assert result["predictions"] == []
        assert "_node_error" in result
        assert "boom" in result["_node_error"]
        assert "_node_latency_ms" in result

    @pytest.mark.asyncio
    async def test_failure_with_error_log_level(self):
        async def bad_node(state):
            raise ValueError("bad input")

        result = await safe_execute_node(
            "debate", bad_node, {"debate_rounds": []}, {}, log_level="error"
        )
        assert result["debate_rounds"] == []
        assert "bad input" in result["_node_error"]

    @pytest.mark.asyncio
    async def test_fallback_does_not_mutate_original(self):
        """Ensure the fallback dict is not mutated across calls."""
        fallback = {"predictions": []}

        async def bad_node(state):
            raise RuntimeError("fail")

        result1 = await safe_execute_node("n1", bad_node, fallback, {})
        result2 = await safe_execute_node("n2", bad_node, fallback, {})

        # Original fallback should be unchanged
        assert "_node_error" not in fallback
        # Results should have error info
        assert "_node_error" in result1
        assert "_node_error" in result2

    @pytest.mark.asyncio
    async def test_state_is_passed_to_fn(self):
        async def check_state(state):
            query = state.get("query", "")
            return {"result": f"processed: {query}"}

        result = await safe_execute_node(
            "test_node", check_state, {"result": ""}, {"query": "chip shortage"}
        )
        assert result == {"result": "processed: chip shortage"}


# ---------------------------------------------------------------------------
# node_error_handler decorator
# ---------------------------------------------------------------------------
class TestNodeErrorHandler:
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        @node_error_handler(fallback={"predictions": []})
        async def predictions_node(state):
            return {"predictions": [42]}

        result = await predictions_node({"query": "test"})
        assert result == {"predictions": [42]}

    @pytest.mark.asyncio
    async def test_decorator_failure_returns_fallback(self):
        @node_error_handler(fallback={"predictions": []})
        async def predictions_node(state):
            raise ConnectionError("DB down")

        result = await predictions_node({"query": "test"})
        assert result["predictions"] == []
        assert "_node_error" in result
        assert "DB down" in result["_node_error"]

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        @node_error_handler(fallback={"x": 0})
        async def my_custom_node(state):
            return {"x": 1}

        assert my_custom_node.__name__ == "my_custom_node"

    @pytest.mark.asyncio
    async def test_decorator_error_log_level(self):
        @node_error_handler(fallback={"debate_rounds": []}, log_level="error")
        async def debate_node(state):
            raise RuntimeError("critical failure")

        result = await debate_node({"query": "test"})
        assert result["debate_rounds"] == []
        assert "critical failure" in result["_node_error"]
