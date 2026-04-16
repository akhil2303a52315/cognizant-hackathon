"""Centralized safe execution utilities for LangGraph nodes.

Provides:
  - safe_execute_node: wraps any async node function with error handling,
    logging, metrics, and safe fallback returns
  - NodeResult: structured return type for node outputs
  - node_error_handler: decorator version for node functions
"""

import time
import logging
import functools
from typing import Any, Callable, Coroutine, TypeVar

from backend.observability.langsmith_config import record_agent_call

logger = logging.getLogger(__name__)

T = TypeVar("T")


class NodeResult:
    """Structured result from a safe node execution."""

    def __init__(
        self,
        data: dict,
        success: bool = True,
        error: str | None = None,
        latency_ms: int = 0,
        node_name: str = "",
    ):
        self.data = data
        self.success = success
        self.error = error
        self.latency_ms = latency_ms
        self.node_name = node_name

    def to_dict(self) -> dict:
        return self.data


async def safe_execute_node(
    node_name: str,
    fn: Callable[..., Coroutine[Any, Any, dict]],
    fallback: dict,
    state: dict,
    *,
    log_level: str = "warning",
    record_metric: bool = True,
) -> dict:
    """Execute a graph node safely with error handling, logging, and metrics.

    Args:
        node_name: Name of the node (for logging/metrics).
        fn: Async function to execute. Receives `state` as argument.
        fallback: Dict to return if execution fails.
        state: The current CouncilState to pass to `fn`.
        log_level: Logging level on failure ("warning" or "error").
        record_metric: Whether to record the call via observability.

    Returns:
        The result dict from `fn`, or `fallback` on failure.
    """
    start = time.time()
    try:
        result = await fn(state)
        latency_ms = int((time.time() - start) * 1000)
        if record_metric:
            try:
                record_agent_call(
                    agent_name=node_name,
                    session_id="graph_execution",
                    model_used="graph_node",
                    latency_ms=latency_ms,
                    confidence=0.0,
                    was_fallback=False,
                )
            except Exception:
                pass
        return result
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        error_msg = f"Node '{node_name}' failed: {e}"

        if log_level == "error":
            logger.error(error_msg)
        else:
            logger.warning(error_msg)

        if record_metric:
            try:
                record_agent_call(
                    agent_name=node_name,
                    session_id="graph_execution",
                    model_used="graph_node",
                    latency_ms=latency_ms,
                    confidence=0.0,
                    was_fallback=False,
                )
            except Exception:
                pass

        # Merge error info into fallback
        fallback_with_error = {
            **fallback,
            "_node_error": error_msg,
            "_node_latency_ms": latency_ms,
        }
        return fallback_with_error


def node_error_handler(fallback: dict, log_level: str = "warning"):
    """Decorator that wraps a graph node function with safe_execute_node.

    Usage:
        @node_error_handler(fallback={"predictions": []})
        async def predictions_node(state: CouncilState) -> dict:
            ...

    Args:
        fallback: Dict to return if the node raises an exception.
        log_level: Logging level on failure.
    """

    def decorator(fn: Callable[..., Coroutine[Any, Any, dict]]):
        @functools.wraps(fn)
        async def wrapper(state: dict) -> dict:
            return await safe_execute_node(
                node_name=fn.__name__,
                fn=fn,
                fallback=fallback,
                state=state,
                log_level=log_level,
            )

        return wrapper

    return decorator
