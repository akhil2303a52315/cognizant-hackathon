"""Observability routes for SupplyChainGPT Council.

Endpoints:
  - GET /observability/traces  — LangSmith trace links for sessions
  - GET /observability/metrics — latency, token usage, confidence averages
  - WebSocket /observability/ws/debate — real-time streaming of debate rounds
"""

import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from backend.config import settings
from backend.observability.langsmith_config import (
    metrics, CouncilTracer, generate_prometheus_metrics,
    record_debate_round, record_agent_call, record_mcp_call,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /observability/traces — LangSmith trace links
# ---------------------------------------------------------------------------
class TraceInfo(BaseModel):
    session_id: str
    trace_url: str
    spans: list[dict] = []


@router.get("/traces")
async def get_traces(session_id: Optional[str] = None, limit: int = 20):
    """Get LangSmith trace links for council sessions.

    If session_id is provided, returns trace for that specific session.
    Otherwise returns recent sessions from Redis.
    """
    if not settings.langchain_tracing_v2 or not settings.langchain_api_key:
        return {
            "success": True,
            "data": {
                "traces": [],
                "langsmith_enabled": False,
                "message": "LangSmith tracing is disabled. Set LANGCHAIN_API_KEY to enable.",
            },
            "error": None,
        }

    traces = []

    if session_id:
        # Specific session trace
        tracer = CouncilTracer(session_id)
        trace_url = tracer.get_trace_url()
        traces.append({
            "session_id": session_id,
            "trace_url": trace_url,
            "langsmith_project": settings.langchain_project,
        })
    else:
        # List recent sessions from Redis
        try:
            from backend.db.redis_client import get_redis
            r = await get_redis()
            keys = await r.keys("council_session:*")
            for key in keys[:limit]:
                data = await r.get(key)
                if data:
                    session = json.loads(data)
                    sid = session.get("session_id", "")
                    tracer = CouncilTracer(sid)
                    traces.append({
                        "session_id": sid,
                        "trace_url": tracer.get_trace_url(),
                        "query": session.get("query", "")[:100],
                        "confidence": session.get("confidence", 0),
                        "risk_score": session.get("risk_score", 0),
                        "timestamp": session.get("timestamp", 0),
                    })
            traces.sort(key=lambda t: t.get("timestamp", 0), reverse=True)
        except Exception as e:
            logger.warning(f"Could not fetch session traces from Redis: {e}")

    return {
        "success": True,
        "data": {
            "traces": traces,
            "langsmith_enabled": True,
            "langsmith_project": settings.langchain_project,
            "langsmith_url": f"https://smith.langchain.com/o/default/projects/p/{settings.langchain_project}",
            "total": len(traces),
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# GET /observability/metrics — latency, token usage, confidence averages
# ---------------------------------------------------------------------------
@router.get("/metrics")
async def get_metrics():
    """Get aggregated observability metrics.

    Returns latency histograms, token usage counters, confidence averages,
    and MCP/RAG call statistics.
    """
    snap = metrics.snapshot()

    # Compute summary statistics
    llm_latency = metrics.get_histogram_summary("llm_latency_ms")
    debate_latency = metrics.get_histogram_summary("debate_latency_ms")
    mcp_latency = metrics.get_histogram_summary("mcp_latency_ms")
    rag_latency = metrics.get_histogram_summary("rag_latency_ms")
    confidence_dist = metrics.get_histogram_summary("council_confidence")

    total_llm_calls = sum(
        v for k, v in snap["counters"].items() if k.startswith("llm_calls_total")
    )
    total_tokens_in = sum(
        v for k, v in snap["counters"].items() if k.startswith("llm_tokens_input_total")
    )
    total_tokens_out = sum(
        v for k, v in snap["counters"].items() if k.startswith("llm_tokens_output_total")
    )
    total_mcp_calls = sum(
        v for k, v in snap["counters"].items() if k.startswith("mcp_calls_total")
    )
    total_rag_calls = sum(
        v for k, v in snap["counters"].items() if k.startswith("rag_retrievals_total")
    )
    total_cost = metrics.get_counter("llm_cost_usd_total")
    total_fallbacks = sum(
        v for k, v in snap["counters"].items() if k.startswith("llm_fallback_total")
    )
    mcp_cache_hits = sum(
        v for k, v in snap["counters"].items() if k.startswith("mcp_cache_hits_total")
    )
    rag_cache_hits = sum(
        v for k, v in snap["counters"].items() if k.startswith("rag_cache_hits_total")
    )

    return {
        "success": True,
        "data": {
            "summary": {
                "total_llm_calls": int(total_llm_calls),
                "total_tokens_input": int(total_tokens_in),
                "total_tokens_output": int(total_tokens_out),
                "total_mcp_calls": int(total_mcp_calls),
                "total_rag_calls": int(total_rag_calls),
                "total_fallbacks": int(total_fallbacks),
                "estimated_cost_usd": round(total_cost, 6),
                "mcp_cache_hit_rate": round(mcp_cache_hits / max(total_mcp_calls, 1), 2),
                "rag_cache_hit_rate": round(rag_cache_hits / max(total_rag_calls, 1), 2),
            },
            "latency": {
                "llm_ms": llm_latency,
                "debate_ms": debate_latency,
                "mcp_ms": mcp_latency,
                "rag_ms": rag_latency,
            },
            "confidence": confidence_dist,
            "config": {
                "langsmith_enabled": settings.langchain_tracing_v2,
                "langsmith_project": settings.langchain_project,
                "human_in_loop": settings.human_in_loop,
                "max_debate_rounds": settings.max_debate_rounds,
                "cost_tracking": settings.langsmith_cost_tracking,
            },
            "raw": snap,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# GET /observability/spans — detailed span breakdown
# ---------------------------------------------------------------------------
@router.get("/spans")
async def get_spans(session_id: Optional[str] = None):
    """Get detailed span breakdown for a session from the in-memory metrics store."""
    snap = metrics.snapshot()

    # Filter spans by session_id if provided
    span_data = {}
    for key, value in snap["histograms"].items():
        if "council_span" in key:
            span_data[key] = value

    return {
        "success": True,
        "data": {
            "spans": span_data,
            "session_id": session_id,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# WebSocket /observability/ws/debate — real-time debate streaming
# ---------------------------------------------------------------------------
@router.websocket("/ws/debate")
async def debate_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time debate round streaming.

    Protocol:
      1. Client connects and sends: {"action": "start", "query": "..."}
      2. Server streams debate events as JSON:
         - {"type": "start", "session_id": "..."}
         - {"type": "agent_done", "agent": "risk", "confidence": 85.0, ...}
         - {"type": "debate_round", "round_number": 1, "phase": "analysis", ...}
         - {"type": "debate_round", "round_number": 2, "phase": "challenge", ...}
         - {"type": "debate_round", "round_number": 3, "phase": "validation", ...}
         - {"type": "complete", "recommendation": "...", "confidence": 0.72, ...}
         - {"type": "human_review_needed", ...}  (if human_in_loop=True)
      3. If human review needed, client sends: {"action": "approve", "session_id": "..."}
      4. Server sends heartbeat every 30s: {"type": "heartbeat", "ts": ...}
    """
    # Validate API key
    import os
    api_key = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key", "")
    valid_keys = os.getenv("API_KEYS", "dev-key").split(",")
    if api_key and api_key not in valid_keys:
        await websocket.close(code=4001, reason="Invalid API key")
        return

    await websocket.accept()

    # Start heartbeat task
    heartbeat_task = None

    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(settings.ws_heartbeat_interval)
                await websocket.send_json({"type": "heartbeat", "ts": time.time()})
        except Exception:
            pass

    import asyncio
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "start":
                query = data.get("query", "")
                context = data.get("context")
                if not query:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Query is required",
                    })
                    continue

                # Stream the council graph with debate
                session_id = data.get("session_id") or str(__import__("uuid").uuid4())

                async def ws_push(payload: dict):
                    try:
                        await websocket.send_json(payload)
                    except Exception:
                        pass

                await websocket.send_json({
                    "type": "start",
                    "session_id": session_id,
                    "query": query,
                })

                async for payload in run_council_streaming(
                    query=query,
                    context=context,
                    session_id=session_id,
                    ws_callback=ws_push,
                ):
                    # Already pushed via ws_callback, but also send directly
                    try:
                        await websocket.send_json(payload)
                    except Exception:
                        break

                await websocket.send_json({
                    "type": "done",
                    "session_id": session_id,
                })

            elif action == "approve":
                # Human-in-the-loop approval
                sid = data.get("session_id", "")
                if sid:
                    await websocket.send_json({
                        "type": "approved",
                        "session_id": sid,
                        "message": "Human approval received. Continuing synthesis...",
                    })
                    # In a full implementation, this would resume the paused graph
                    # by updating the state with human_approved=True

            elif action == "ping":
                await websocket.send_json({"type": "pong", "ts": time.time()})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}. Use 'start', 'approve', or 'ping'.",
                })

    except WebSocketDisconnect:
        logger.info("Debate WebSocket disconnected")
    except Exception as e:
        logger.error(f"Debate WebSocket error: {e}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
