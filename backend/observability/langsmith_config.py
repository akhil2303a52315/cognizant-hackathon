"""LangSmith tracing configuration for SupplyChainGPT Council.

Provides:
  - Custom callbacks for debate rounds, MCP calls, RAG retrievals
  - Metadata injection: agent_name, round_number, confidence, mcp_tool_used
  - Cost tracking and performance monitoring
  - Trace URL generation for frontend linking
  - Prometheus-compatible metrics export
"""

import os
import time
import logging
import threading
from typing import Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure LangSmith env vars are set before any langchain import
# ---------------------------------------------------------------------------
def configure_langsmith_env():
    """Set environment variables for LangSmith tracing."""
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        logger.info(f"LangSmith tracing ENABLED → project={settings.langchain_project}")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("LangSmith tracing DISABLED (no API key)")


# ---------------------------------------------------------------------------
# In-memory metrics store (thread-safe) — also exported via /metrics
# ---------------------------------------------------------------------------
@dataclass
class _Metrics:
    """Thread-safe in-memory metrics store for Prometheus export."""
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _counters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    _histograms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    _gauges: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def inc_counter(self, name: str, value: float = 1.0, labels: dict | None = None):
        key = _label_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe_histogram(self, name: str, value: float, labels: dict | None = None):
        key = _label_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: dict | None = None):
        key = _label_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def get_counter(self, name: str, labels: dict | None = None) -> float:
        key = _label_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)

    def get_histogram_summary(self, name: str, labels: dict | None = None) -> dict:
        key = _label_key(name, labels)
        with self._lock:
            values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "sum": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "count": n,
            "sum": sum(sorted_vals),
            "avg": sum(sorted_vals) / n,
            "p50": sorted_vals[int(n * 0.5)],
            "p95": sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[-1],
            "p99": sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[-1],
        }

    def get_gauge(self, name: str, labels: dict | None = None) -> float:
        key = _label_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: _hist_summary(v) for k, v in self._histograms.items()},
            }


def _label_key(name: str, labels: dict | None) -> str:
    if not labels:
        return name
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f'{name}{{{label_str}}}'


def _hist_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "sum": 0.0, "avg": 0.0}
    return {"count": len(values), "sum": sum(values), "avg": sum(values) / len(values)}


# Singleton metrics instance
metrics = _Metrics()


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------
# Approximate costs per 1K tokens (USD) — update as providers change
_COST_PER_1K = {
    "groq:llama3": 0.0000,
    "groq:llama3-70b": 0.0000,
    "groq:mixtral": 0.0000,
    "gemini:gemini-pro": 0.0000,
    "gemini:gemini-1.5-flash": 0.0000,
    "openrouter:auto": 0.0005,
    "nvidia:llama3": 0.0000,
    "cohere:command-r": 0.0005,
    "sambanova:llama3": 0.0000,
    "bytez:default": 0.0000,
    "unknown": 0.0005,
}


def estimate_cost(model_used: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for an LLM call."""
    rate = _COST_PER_1K.get(model_used, _COST_PER_1K["unknown"])
    total_1k = (input_tokens + output_tokens) / 1000.0
    return total_1k * rate


def get_total_cost() -> float:
    return metrics.get_counter("llm_cost_usd_total")


# ---------------------------------------------------------------------------
# Custom tracing callbacks
# ---------------------------------------------------------------------------
class CouncilTracer:
    """Custom tracer that injects metadata into LangSmith runs and records metrics.

    Usage:
        tracer = CouncilTracer(session_id="abc123")
        with tracer.trace_agent("risk", round_number=1):
            ...
        with tracer.trace_debate_round(2, phase="challenge"):
            ...
        with tracer.trace_mcp_call("stock_quote", agent="finance"):
            ...
        with tracer.trace_rag_retrieval("risk", top_k=5):
            ...
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._spans: list[dict] = []

    def _record_span(self, span_type: str, name: str, metadata: dict, duration_ms: float):
        span = {
            "session_id": self.session_id,
            "span_type": span_type,
            "name": name,
            "metadata": metadata,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
        }
        self._spans.append(span)

        # Record metrics
        metrics.inc_counter(f"council_spans_total", labels={"type": span_type})
        metrics.observe_histogram(f"council_span_duration_ms", duration_ms, labels={"type": span_type})

    def trace_agent(self, agent_name: str, round_number: int = 1, **extra_meta):
        return _SpanContext(
            on_exit=lambda dur, meta: self._record_span(
                "agent", agent_name,
                {"agent_name": agent_name, "round_number": round_number, **extra_meta, **meta},
                dur,
            )
        )

    def trace_debate_round(self, round_number: int, phase: str = "analysis", **extra_meta):
        return _SpanContext(
            on_exit=lambda dur, meta: self._record_span(
                "debate_round", f"round_{round_number}_{phase}",
                {"round_number": round_number, "phase": phase, **extra_meta, **meta},
                dur,
            )
        )

    def trace_mcp_call(self, tool_name: str, agent: str = "", **extra_meta):
        return _SpanContext(
            on_exit=lambda dur, meta: self._record_span(
                "mcp_call", tool_name,
                {"mcp_tool_used": tool_name, "agent": agent, **extra_meta, **meta},
                dur,
            )
        )

    def trace_rag_retrieval(self, agent: str, top_k: int = 5, **extra_meta):
        return _SpanContext(
            on_exit=lambda dur, meta: self._record_span(
                "rag_retrieval", f"rag_{agent}",
                {"agent": agent, "top_k": top_k, **extra_meta, **meta},
                dur,
            )
        )

    def get_spans(self) -> list[dict]:
        return list(self._spans)

    def get_trace_url(self) -> str:
        """Generate LangSmith trace URL for this session."""
        if not settings.langchain_api_key:
            return ""
        project = settings.langchain_project
        return f"https://smith.langchain.com/o/default/projects/p/{project}?searchModel={self.session_id}"


class _SpanContext:
    """Context manager for timing a traced span."""

    def __init__(self, on_exit):
        self._on_exit = on_exit
        self._start = 0.0
        self._meta: dict = {}

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, *args):
        duration_ms = (time.monotonic() - self._start) * 1000
        self._on_exit(duration_ms, self._meta)

    def add_metadata(self, **kwargs):
        """Add metadata to the span (call inside the with block)."""
        self._meta.update(kwargs)


# ---------------------------------------------------------------------------
# Record helpers — call these from agent/debate/MCP/RAG code
# ---------------------------------------------------------------------------
def record_agent_call(agent_name: str, session_id: str, model_used: str,
                      input_tokens: int = 0, output_tokens: int = 0,
                      confidence: float = 0.0, latency_ms: float = 0.0,
                      was_fallback: bool = False):
    """Record metrics for a single agent LLM call."""
    labels = {"agent": agent_name, "model": model_used}
    metrics.inc_counter("llm_calls_total", labels=labels)
    metrics.inc_counter("llm_tokens_input_total", input_tokens, labels=labels)
    metrics.inc_counter("llm_tokens_output_total", output_tokens, labels=labels)
    metrics.observe_histogram("llm_latency_ms", latency_ms, labels=labels)
    metrics.observe_histogram("council_confidence", confidence, labels={"agent": agent_name})
    if was_fallback:
        metrics.inc_counter("llm_fallback_total", labels={"agent": agent_name})
    if settings.langsmith_cost_tracking:
        cost = estimate_cost(model_used, input_tokens, output_tokens)
        metrics.inc_counter("llm_cost_usd_total", cost, labels=labels)


def record_debate_round(session_id: str, round_number: int, phase: str,
                        confidence: float, risk_score: float, latency_ms: float):
    """Record metrics for a debate round."""
    labels = {"phase": phase, "round": str(round_number)}
    metrics.inc_counter("debate_rounds_total", labels=labels)
    metrics.observe_histogram("debate_latency_ms", latency_ms, labels=labels)
    metrics.observe_histogram("debate_confidence", confidence, labels=labels)
    metrics.set_gauge("debate_risk_score", risk_score, labels={"session_id": session_id})


def record_mcp_call(tool_name: str, agent: str, latency_ms: float,
                     was_cached: bool = False, success: bool = True):
    """Record metrics for an MCP tool call."""
    labels = {"tool": tool_name, "agent": agent}
    metrics.inc_counter("mcp_calls_total", labels=labels)
    metrics.observe_histogram("mcp_latency_ms", latency_ms, labels=labels)
    if was_cached:
        metrics.inc_counter("mcp_cache_hits_total", labels={"tool": tool_name})
    if not success:
        metrics.inc_counter("mcp_errors_total", labels={"tool": tool_name})


def record_rag_retrieval(agent: str, top_k: int, latency_ms: float,
                          documents_retrieved: int, was_cached: bool = False):
    """Record metrics for a RAG retrieval."""
    labels = {"agent": agent}
    metrics.inc_counter("rag_retrievals_total", labels=labels)
    metrics.observe_histogram("rag_latency_ms", latency_ms, labels=labels)
    metrics.observe_histogram("rag_documents_retrieved", documents_retrieved, labels=labels)
    if was_cached:
        metrics.inc_counter("rag_cache_hits_total", labels=labels)


# ---------------------------------------------------------------------------
# Prometheus text format export
# ---------------------------------------------------------------------------
def generate_prometheus_metrics() -> str:
    """Generate Prometheus text-format metrics for /metrics endpoint."""
    lines = []
    snap = metrics.snapshot()

    # Counters
    for key, value in snap["counters"].items():
        metric_name = key.split('{')[0]
        lines.append(f"# HELP council_{metric_name} Cumulative counter for {metric_name}")
        lines.append(f"# TYPE council_{metric_name} counter")
        lines.append(f"council_{key} {value}")
    # Gauges
    for key, value in snap["gauges"].items():
        metric_name = key.split('{')[0]
        lines.append(f"# HELP council_{metric_name} Current gauge for {metric_name}")
        lines.append(f"# TYPE council_{metric_name} gauge")
        lines.append(f"council_{key} {value}")
    # Histograms (summary style)
    for key, summary in snap["histograms"].items():
        metric_name = key.split('{')[0]
        lines.append(f"# HELP council_{metric_name} Latency summary for {metric_name}")
        lines.append(f"# TYPE council_{metric_name} summary")
        lines.append(f'council_{metric_name}_count {summary["count"]}')
        lines.append(f'council_{metric_name}_sum {summary["sum"]:.2f}')
        lines.append(f'council_{metric_name}{{quantile="0.5"}} {summary["p50"]:.2f}')
        lines.append(f'council_{metric_name}{{quantile="0.95"}} {summary["p95"]:.2f}')
        lines.append(f'council_{metric_name}{{quantile="0.99"}} {summary["p99"]:.2f}')

    # Static info
    lines.append(f'# HELP council_info Build info')
    lines.append(f'# TYPE council_info gauge')
    lines.append(f'council_info{{version="{settings.version}"}} 1')
    lines.append(f'# HELP council_agents_total Number of domain agents')
    lines.append(f'# TYPE council_agents_total gauge')
    lines.append(f'council_agents_total 6')

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Initialize on import
# ---------------------------------------------------------------------------
configure_langsmith_env()
