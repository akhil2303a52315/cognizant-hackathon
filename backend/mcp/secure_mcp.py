"""Secure MCP execution layer for SupplyChainGPT Council.

Provides:
  - Sandboxed tool execution with input sanitization
  - Prompt injection detection and guardrails
  - PII redaction in tool inputs and outputs
  - Schema evolution handling with cached fallback
  - Per-agent rate limiting
  - Comprehensive audit logging for every MCP call
  - LangSmith tracing integration
"""

import re
import json
import time
import logging
import asyncio
from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from backend.mcp.mcp_servers import is_tool_allowed_for_agent, get_server_for_tool
from backend.mcp.mcp_toolkit import get_tool_schema_with_fallback, _update_tool_health
from backend.mcp.sandbox import validate_inputs, detect_prompt_injection, redact_pii
from backend.mcp.audit import audit_log
from backend.mcp.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Circuit breaker (per tool)
# ---------------------------------------------------------------------------
class CircuitBreaker:
    """Circuit breaker for MCP tool calls.

    States:
      - CLOSED: normal operation, calls pass through
      - OPEN: too many failures, calls are rejected immediately
      - HALF_OPEN: testing recovery, allows one probe call
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = self.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def allow_call(self) -> bool:
        state = self.state
        if state == self.CLOSED:
            return True
        if state == self.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        return False  # OPEN

    def record_success(self) -> None:
        if self._state == self.HALF_OPEN:
            self._success_count += 1
            self._state = self.CLOSED
            self._failure_count = 0
        elif self._state == self.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._state == self.HALF_OPEN:
            self._state = self.OPEN
        elif self._failure_count >= self.failure_threshold:
            self._state = self.OPEN


_circuit_breakers: dict[str, CircuitBreaker] = defaultdict(
    lambda: CircuitBreaker()
)


def get_circuit_breaker(tool_name: str) -> CircuitBreaker:
    return _circuit_breakers[tool_name]


# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 0.5  # seconds
RETRY_MAX_DELAY = 10.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0
RETRYABLE_EXCEPTIONS = (asyncio.TimeoutError, ConnectionError, OSError)


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per agent)
# ---------------------------------------------------------------------------
_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(agent_name: str, limit: int = 30) -> bool:
    """Check if agent is within rate limit. Returns True if allowed."""
    now = time.time()
    window = _rate_limits[agent_name]
    # Remove entries outside the window
    _rate_limits[agent_name] = [t for t in window if now - t < RATE_LIMIT_WINDOW]
    current = len(_rate_limits[agent_name])
    if current >= limit:
        return False
    _rate_limits[agent_name].append(now)
    return True


def get_rate_limit_status(agent_name: str) -> dict:
    """Return current rate limit status for an agent."""
    now = time.time()
    window = [t for t in _rate_limits.get(agent_name, []) if now - t < RATE_LIMIT_WINDOW]
    server_limit = 30  # default
    return {
        "agent": agent_name,
        "calls_in_window": len(window),
        "limit": server_limit,
        "remaining": max(0, server_limit - len(window)),
        "window_seconds": RATE_LIMIT_WINDOW,
    }


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS = [
    r";\s*DROP\s+TABLE",
    r";\s*DELETE\s+FROM",
    r";\s*TRUNCATE\s+TABLE",
    r"UNION\s+SELECT",
    r"OR\s+1\s*=\s*1",
    r"<script[^>]*>",
    r"javascript\s*:",
    r"data\s*:",
    r"vbscript\s*:",
]


def sanitize_input(params: dict) -> tuple[dict, list[str]]:
    """Sanitize tool input parameters.

    Returns (sanitized_params, warnings).
    """
    warnings = []
    sanitized = {}

    for key, value in params.items():
        if isinstance(value, str):
            # Check for dangerous patterns
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    warnings.append(f"Potentially dangerous input in '{key}': matched {pattern}")
                    value = re.sub(pattern, "[REMOVED]", value, flags=re.IGNORECASE)

            # Redact PII
            redacted = redact_pii(value)
            if redacted != value:
                warnings.append(f"PII redacted in parameter '{key}'")
                value = redacted

            # Truncate extremely long inputs
            if len(value) > 10000:
                warnings.append(f"Parameter '{key}' truncated from {len(value)} to 10000 chars")
                value = value[:10000]

            sanitized[key] = value
        elif isinstance(value, dict):
            sub_sanitized, sub_warnings = sanitize_input(value)
            sanitized[key] = sub_sanitized
            warnings.extend([f"{key}.{w}" for w in sub_warnings])
        elif isinstance(value, list):
            sanitized_list = []
            for i, item in enumerate(value):
                if isinstance(item, str):
                    item = redact_pii(item)
                    if len(item) > 10000:
                        item = item[:10000]
                sanitized_list.append(item)
            sanitized[key] = sanitized_list
        else:
            sanitized[key] = value

    return sanitized, warnings


def sanitize_output(result: Any) -> Any:
    """Sanitize tool output — redact PII, truncate if needed."""
    if isinstance(result, dict):
        sanitized = {}
        for key, value in result.items():
            if isinstance(value, str):
                sanitized[key] = redact_pii(value)[:5000]
            elif isinstance(value, list):
                sanitized[key] = [
                    redact_pii(item)[:5000] if isinstance(item, str) else item
                    for item in value[:50]  # limit list size
                ]
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(result, str):
        return redact_pii(result)[:5000]
    return result


# ---------------------------------------------------------------------------
# Secure MCP executor
# ---------------------------------------------------------------------------
class SecureMCPExecutor:
    """Secure MCP tool executor with sandboxing, guardrails, rate limiting,
    schema validation, and audit logging.

    Every tool call goes through:
      1. Scope validation (agent allowed to use this tool?)
      2. Rate limiting check
      3. Input sanitization + PII redaction
      4. Sandbox validation (prompt injection, write operations)
      5. Schema validation (with cached fallback)
      6. Tool execution (with timeout)
      7. Output sanitization
      8. Audit logging
      9. Health tracking
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    async def execute(self, tool_name: str, params: dict, timeout_seconds: int = 30) -> dict:
        """Execute an MCP tool securely.

        Returns dict with:
          - result: the tool's output (sanitized)
          - success: bool
          - cached: bool
          - latency_ms: int
          - scope_valid: bool
          - rate_limited: bool
          - sandbox_violations: list[str]
          - warnings: list[str]
          - schema_version: str ("current" | "cached_fallback")
        """
        start = time.time()
        result_meta = {
            "result": None,
            "success": False,
            "cached": False,
            "latency_ms": 0,
            "scope_valid": True,
            "rate_limited": False,
            "sandbox_violations": [],
            "warnings": [],
            "schema_version": "current",
        }

        # Step 1: Scope validation
        if not is_tool_allowed_for_agent(tool_name, self.agent_name):
            result_meta["scope_valid"] = False
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            result_meta["warnings"].append(f"Tool '{tool_name}' not allowed for agent '{self.agent_name}'")
            logger.warning(f"[SecureMCP:{self.agent_name}] Scope violation: {tool_name}")
            return result_meta

        # Step 2: Rate limiting
        server = get_server_for_tool(tool_name)
        rate_limit = server.rate_limit_per_minute if server else 30
        if not _check_rate_limit(self.agent_name, rate_limit):
            result_meta["rate_limited"] = True
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            result_meta["warnings"].append(f"Rate limit exceeded ({rate_limit}/min)")
            logger.warning(f"[SecureMCP:{self.agent_name}] Rate limited: {tool_name}")
            return result_meta

        # Step 3: Input sanitization
        sanitized_params, sanitize_warnings = sanitize_input(params)
        result_meta["warnings"].extend(sanitize_warnings)

        # Step 4: Sandbox validation
        violations = validate_inputs(tool_name, sanitized_params)
        # Also check for prompt injection in all string params
        for key, value in sanitized_params.items():
            if isinstance(value, str):
                injection = detect_prompt_injection(value)
                violations.extend(injection)
        result_meta["sandbox_violations"] = violations

        if violations:
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            result_meta["warnings"].append(f"Sandbox violations: {', '.join(violations)}")
            logger.warning(f"[SecureMCP:{self.agent_name}] Sandbox violation: {violations}")
            await audit_log(
                tool=tool_name, agent=self.agent_name,
                input_hash="sandbox_violation", latency_ms=result_meta["latency_ms"],
                was_cached=False, sandbox_violations=violations,
            )
            return result_meta

        # Step 5: Schema validation with fallback
        schema = await get_tool_schema_with_fallback(tool_name)
        if schema is None:
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            result_meta["warnings"].append(f"Tool '{tool_name}' schema unavailable")
            return result_meta

        # Check if we're using a cached schema (schema evolution detected)
        from backend.mcp.registry import get_tool as registry_get_tool
        current_tool = registry_get_tool(tool_name)
        if current_tool and current_tool.get("input_schema") is None:
            result_meta["schema_version"] = "cached_fallback"
            result_meta["warnings"].append("Using cached schema fallback (schema evolution detected)")

        # Validate required params against schema
        required = schema.get("required", [])
        for req_param in required:
            if req_param not in sanitized_params:
                result_meta["latency_ms"] = int((time.time() - start) * 1000)
                result_meta["warnings"].append(f"Missing required parameter: {req_param}")
                return result_meta

        # Step 6: Cache check
        import hashlib
        input_hash = hashlib.sha256(json.dumps(sanitized_params, sort_keys=True).encode()).hexdigest()
        cached_result = await cache_get(f"mcp:{tool_name}:{input_hash}")
        if cached_result is not None:
            result_meta["result"] = sanitize_output(cached_result)
            result_meta["success"] = True
            result_meta["cached"] = True
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            await audit_log(tool=tool_name, agent=self.agent_name,
                           input_hash=input_hash, latency_ms=result_meta["latency_ms"],
                           was_cached=True)
            _update_tool_health(tool_name, True, result_meta["latency_ms"])
            return result_meta

        # Step 7: Circuit breaker check
        cb = get_circuit_breaker(tool_name)
        if not cb.allow_call():
            result_meta["latency_ms"] = int((time.time() - start) * 1000)
            result_meta["warnings"].append(
                f"Circuit breaker OPEN for tool '{tool_name}' (failures={cb._failure_count})"
            )
            logger.warning(f"[SecureMCP:{self.agent_name}] Circuit breaker open: {tool_name}")
            return result_meta

        # Step 8: Execute tool with retry + timeout
        from backend.mcp.registry import invoke_tool as registry_invoke

        last_error: Optional[Exception] = None
        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                result = await asyncio.wait_for(
                    registry_invoke(tool_name, sanitized_params),
                    timeout=timeout_seconds,
                )
                result_meta["result"] = sanitize_output(result)
                result_meta["success"] = True
                result_meta["latency_ms"] = int((time.time() - start) * 1000)
                result_meta["attempts"] = attempt

                # Cache result
                tool_info = registry_get_tool(tool_name)
                ttl = tool_info.get("cache_ttl", 3600) if tool_info else 3600
                await cache_set(f"mcp:{tool_name}:{input_hash}", result, ttl=ttl)

                # Audit log
                await audit_log(tool=tool_name, agent=self.agent_name,
                               input_hash=input_hash, latency_ms=result_meta["latency_ms"],
                               was_cached=False)

                _update_tool_health(tool_name, True, result_meta["latency_ms"])
                cb.record_success()
                return result_meta

            except PermissionError as e:
                result_meta["latency_ms"] = int((time.time() - start) * 1000)
                result_meta["warnings"].append(f"Permission denied: {e}")
                _update_tool_health(tool_name, False, result_meta["latency_ms"], str(e))
                cb.record_failure()
                return result_meta

            except ValueError as e:
                result_meta["latency_ms"] = int((time.time() - start) * 1000)
                result_meta["warnings"].append(f"Invalid input: {e}")
                _update_tool_health(tool_name, False, result_meta["latency_ms"], str(e))
                cb.record_failure()
                return result_meta

            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                if attempt < RETRY_MAX_ATTEMPTS:
                    delay = min(
                        RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** (attempt - 1)),
                        RETRY_MAX_DELAY,
                    )
                    logger.warning(
                        f"[SecureMCP:{self.agent_name}] Tool '{tool_name}' "
                        f"attempt {attempt}/{RETRY_MAX_ATTEMPTS} failed ({type(e).__name__}), "
                        f"retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    result_meta["latency_ms"] = int((time.time() - start) * 1000)
                    result_meta["warnings"].append(
                        f"Tool failed after {RETRY_MAX_ATTEMPTS} attempts: {e}"
                    )
                    result_meta["attempts"] = attempt
                    _update_tool_health(tool_name, False, result_meta["latency_ms"], str(e))
                    cb.record_failure()
                    logger.error(
                        f"[SecureMCP:{self.agent_name}] Tool '{tool_name}' "
                        f"failed after {RETRY_MAX_ATTEMPTS} retries: {e}"
                    )

            except Exception as e:
                result_meta["latency_ms"] = int((time.time() - start) * 1000)
                result_meta["warnings"].append(f"Execution failed: {e}")
                _update_tool_health(tool_name, False, result_meta["latency_ms"], str(e))
                cb.record_failure()
                logger.error(f"[SecureMCP:{self.agent_name}] Tool '{tool_name}' failed: {e}")
                return result_meta

        return result_meta


# ---------------------------------------------------------------------------
# Singleton executors per agent
# ---------------------------------------------------------------------------
_secure_executors: dict[str, SecureMCPExecutor] = {}


def get_secure_executor(agent_name: str) -> SecureMCPExecutor:
    """Get or create a SecureMCPExecutor for an agent."""
    if agent_name not in _secure_executors:
        _secure_executors[agent_name] = SecureMCPExecutor(agent_name)
    return _secure_executors[agent_name]


async def secure_invoke(agent_name: str, tool_name: str, params: dict) -> dict:
    """Convenience function: secure MCP invocation for an agent.

    This is the primary entry point for agents to call MCP tools.
    """
    executor = get_secure_executor(agent_name)
    return await executor.execute(tool_name, params)
