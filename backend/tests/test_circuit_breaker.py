"""Tests for CircuitBreaker and retry logic in secure_mcp.py."""

import pytest
import asyncio
import time
from backend.mcp.secure_mcp import (
    CircuitBreaker,
    get_circuit_breaker,
    _circuit_breakers,
    RETRY_MAX_ATTEMPTS,
    RETRY_BASE_DELAY,
    RETRY_BACKOFF_FACTOR,
)


# ---------------------------------------------------------------------------
# CircuitBreaker: state transitions
# ---------------------------------------------------------------------------
class TestCircuitBreakerStates:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreaker.CLOSED

    def test_transitions_to_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_remains_closed_below_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.CLOSED

    def test_transitions_to_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitBreaker.HALF_OPEN

    def test_half_open_back_to_open_on_failure(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitBreaker.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitBreaker.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb._failure_count == 0


# ---------------------------------------------------------------------------
# CircuitBreaker: allow_call
# ---------------------------------------------------------------------------
class TestCircuitBreakerAllowCall:
    def test_closed_allows_calls(self):
        cb = CircuitBreaker()
        assert cb.allow_call() is True

    def test_open_blocks_calls(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        assert cb.allow_call() is False

    def test_half_open_allows_limited_calls(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, half_open_max_calls=1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitBreaker.HALF_OPEN
        assert cb.allow_call() is True
        assert cb.allow_call() is False  # exceeded max

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb._failure_count == 0


# ---------------------------------------------------------------------------
# get_circuit_breaker: per-tool instances
# ---------------------------------------------------------------------------
class TestCircuitBreakerRegistry:
    def test_returns_same_instance_for_same_tool(self):
        cb1 = get_circuit_breaker("test_tool_a")
        cb2 = get_circuit_breaker("test_tool_a")
        assert cb1 is cb2

    def test_returns_different_instance_for_different_tool(self):
        cb1 = get_circuit_breaker("test_tool_b")
        cb2 = get_circuit_breaker("test_tool_c")
        assert cb1 is not cb2


# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------
class TestRetryConfig:
    def test_max_attempts_is_at_least_2(self):
        assert RETRY_MAX_ATTEMPTS >= 2

    def test_base_delay_is_positive(self):
        assert RETRY_BASE_DELAY > 0

    def test_backoff_factor_is_at_least_1(self):
        assert RETRY_BACKOFF_FACTOR >= 1


# ---------------------------------------------------------------------------
# Integration: SecureMCPExecutor with circuit breaker
# ---------------------------------------------------------------------------
class TestSecureMCPWithCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_after_failures(self):
        """After enough failures, the circuit breaker should block calls."""
        from backend.mcp.secure_mcp import SecureMCPExecutor
        from unittest.mock import AsyncMock, patch

        executor = SecureMCPExecutor("test_agent_cb")

        # Reset circuit breaker for the test tool
        tool_name = "test_cb_tool_block"
        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]

        cb = get_circuit_breaker(tool_name)
        cb.failure_threshold = 2

        # Force the circuit breaker open by recording failures
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

        # Now execute should be blocked by circuit breaker
        with patch("backend.mcp.secure_mcp.is_tool_allowed_for_agent", return_value=True), \
             patch("backend.mcp.secure_mcp.get_server_for_tool", return_value=None), \
             patch("backend.mcp.secure_mcp._check_rate_limit", return_value=True), \
             patch("backend.mcp.secure_mcp.sanitize_input", return_value=({}, [])), \
             patch("backend.mcp.secure_mcp.validate_inputs", return_value=[]), \
             patch("backend.mcp.secure_mcp.get_tool_schema_with_fallback", return_value={"required": []}):
            result = await executor.execute(tool_name, {"query": "test"})
            assert result["success"] is False
            assert any("Circuit breaker OPEN" in w for w in result["warnings"])

        # Clean up
        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Executor should retry on TimeoutError and record attempts."""
        from backend.mcp.secure_mcp import SecureMCPExecutor
        from unittest.mock import AsyncMock, patch
        import asyncio

        executor = SecureMCPExecutor("test_agent_retry")
        tool_name = "test_retry_tool"

        # Reset circuit breaker
        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]

        call_count = 0

        async def mock_invoke(name, params):
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError()

        cb = CircuitBreaker(failure_threshold=10)

        with patch("backend.mcp.secure_mcp.is_tool_allowed_for_agent", return_value=True), \
             patch("backend.mcp.secure_mcp.get_server_for_tool", return_value=None), \
             patch("backend.mcp.secure_mcp._check_rate_limit", return_value=True), \
             patch("backend.mcp.secure_mcp.sanitize_input", return_value=({}, [])), \
             patch("backend.mcp.secure_mcp.validate_inputs", return_value=[]), \
             patch("backend.mcp.secure_mcp.get_tool_schema_with_fallback", return_value={"required": []}), \
             patch("backend.mcp.registry.get_tool", return_value=None), \
             patch("backend.mcp.secure_mcp.cache_get", return_value=None), \
             patch("backend.mcp.registry.invoke_tool", side_effect=mock_invoke), \
             patch("backend.mcp.secure_mcp.get_circuit_breaker", return_value=cb):

            result = await executor.execute(tool_name, {"query": "test"}, timeout_seconds=1)

            assert result["success"] is False
            assert call_count == RETRY_MAX_ATTEMPTS
            assert any("failed after" in w for w in result["warnings"])

        # Clean up
        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]

    @pytest.mark.asyncio
    async def test_non_retryable_error_no_retry(self):
        """PermissionError should not be retried."""
        from backend.mcp.secure_mcp import SecureMCPExecutor
        from unittest.mock import patch

        executor = SecureMCPExecutor("test_agent_noretry")
        tool_name = "test_noretry_tool"

        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]

        call_count = 0

        async def mock_invoke(name, params):
            nonlocal call_count
            call_count += 1
            raise PermissionError("access denied")

        cb = CircuitBreaker(failure_threshold=10)

        with patch("backend.mcp.secure_mcp.is_tool_allowed_for_agent", return_value=True), \
             patch("backend.mcp.secure_mcp.get_server_for_tool", return_value=None), \
             patch("backend.mcp.secure_mcp._check_rate_limit", return_value=True), \
             patch("backend.mcp.secure_mcp.sanitize_input", return_value=({}, [])), \
             patch("backend.mcp.secure_mcp.validate_inputs", return_value=[]), \
             patch("backend.mcp.secure_mcp.get_tool_schema_with_fallback", return_value={"required": []}), \
             patch("backend.mcp.registry.get_tool", return_value=None), \
             patch("backend.mcp.secure_mcp.cache_get", return_value=None), \
             patch("backend.mcp.registry.invoke_tool", side_effect=mock_invoke), \
             patch("backend.mcp.secure_mcp.get_circuit_breaker", return_value=cb):

            result = await executor.execute(tool_name, {"query": "test"}, timeout_seconds=1)

            assert result["success"] is False
            assert call_count == 1  # No retries for PermissionError
            assert any("Permission denied" in w for w in result["warnings"])

        if tool_name in _circuit_breakers:
            del _circuit_breakers[tool_name]
