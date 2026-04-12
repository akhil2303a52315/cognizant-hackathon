from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
from backend.graph import build_council_graph
from backend.llm.router import llm_router
from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
from backend.agents.supply_agent import SYSTEM_PROMPT as SUPPLY_PROMPT
from backend.agents.logistics_agent import SYSTEM_PROMPT as LOGISTICS_PROMPT
from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
from backend.agents.finance_agent import SYSTEM_PROMPT as FINANCE_PROMPT
from backend.agents.brand_agent import SYSTEM_PROMPT as BRAND_PROMPT
from backend.agents.moderator import SYSTEM_PROMPT as MODERATOR_PROMPT
from backend.ws.events import EventType, Topic, emit_event
import uuid
import time
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

AGENT_PROMPTS = {
    "risk": RISK_PROMPT,
    "supply": SUPPLY_PROMPT,
    "logistics": LOGISTICS_PROMPT,
    "market": MARKET_PROMPT,
    "finance": FINANCE_PROMPT,
    "brand": BRAND_PROMPT,
}


class CouncilRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    ws_session_id: Optional[str] = None


class CouncilResponse(BaseModel):
    session_id: str
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    agent_outputs: list = []
    evidence: list = []
    round_number: int = 0
    status: str = "pending"
    latency_ms: int = 0


@router.post("/analyze", response_model=CouncilResponse)
async def council_analyze(request: CouncilRequest):
    session_id = str(uuid.uuid4())
    start = time.time()

    try:
        graph = build_council_graph()
        compiled = graph.compile()

        initial_state = {
            "query": request.query,
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": session_id,
            "context": request.context,
        }

        result = await compiled.ainvoke(initial_state)

        latency_ms = int((time.time() - start) * 1000)

        return CouncilResponse(
            session_id=session_id,
            recommendation=result.get("recommendation"),
            confidence=result.get("confidence"),
            agent_outputs=[o.model_dump() for o in result.get("agent_outputs", [])],
            evidence=[e.model_dump() for e in result.get("evidence", [])],
            round_number=result.get("round_number", 0),
            status=result.get("status", "complete"),
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error(f"Council analysis failed: {e}")
        raise HTTPException(500, f"Council analysis failed: {e}")


@router.post("/stream")
async def council_stream(request: CouncilRequest):
    """SSE streaming endpoint — streams each agent's output token by token."""
    session_id = str(uuid.uuid4())

    ws_sid = request.ws_session_id

    async def event_generator():
        # Send session start
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        await emit_event(EventType.COUNCIL_TOKEN, {"type": "start", "session_id": session_id}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Stream each agent in sequence
        agent_outputs = {}
        for agent_name, system_prompt in AGENT_PROMPTS.items():
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': agent_name})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_START, {"agent": agent_name}, session_id=ws_sid, topic=Topic.COUNCIL)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze for: {request.query}"},
            ]

            full_response = ""
            try:
                async for token in llm_router.stream_with_fallback(agent_name, messages):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'agent': agent_name, 'content': token})}\n\n"
                    await emit_event(EventType.COUNCIL_TOKEN, {"agent": agent_name, "content": token}, session_id=ws_sid, topic=Topic.COUNCIL)
            except Exception as e:
                full_response = f"Agent {agent_name} unavailable: {e}"
                yield f"data: {json.dumps({'type': 'agent_error', 'agent': agent_name, 'error': str(e)})}\n\n"
                await emit_event(EventType.COUNCIL_AGENT_ERROR, {"agent": agent_name, "error": str(e)}, session_id=ws_sid, topic=Topic.COUNCIL)

            agent_outputs[agent_name] = full_response
            yield f"data: {json.dumps({'type': 'agent_done', 'agent': agent_name})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_DONE, {"agent": agent_name}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Moderator synthesis
        yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'moderator'})}\n\n"
        await emit_event(EventType.COUNCIL_AGENT_START, {"agent": "moderator"}, session_id=ws_sid, topic=Topic.COUNCIL)

        synth_prompt = (
            f"{MODERATOR_PROMPT}\n\n"
            f"Query: {request.query}\n\n"
            f"Agent outputs:\n"
        )
        for name, output in agent_outputs.items():
            synth_prompt += f"\n--- {name.upper()} ---\n{output}\n"

        synth_messages = [
            {"role": "system", "content": MODERATOR_PROMPT},
            {"role": "user", "content": synth_prompt},
        ]

        synthesis = ""
        try:
            async for token in llm_router.stream_with_fallback("moderator", synth_messages):
                synthesis += token
                yield f"data: {json.dumps({'type': 'token', 'agent': 'moderator', 'content': token})}\n\n"
                await emit_event(EventType.COUNCIL_TOKEN, {"agent": "moderator", "content": token}, session_id=ws_sid, topic=Topic.COUNCIL)
        except Exception as e:
            synthesis = f"Synthesis failed: {e}"
            yield f"data: {json.dumps({'type': 'agent_error', 'agent': 'moderator', 'error': str(e)})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_ERROR, {"agent": "moderator", "error": str(e)}, session_id=ws_sid, topic=Topic.COUNCIL)

        yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'moderator'})}\n\n"
        await emit_event(EventType.COUNCIL_AGENT_DONE, {"agent": "moderator"}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Send final result
        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'recommendation': synthesis})}\n\n"
        await emit_event(EventType.COUNCIL_COMPLETE, {"session_id": session_id, "recommendation": synthesis}, session_id=ws_sid, topic=Topic.COUNCIL)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/export/{session_id}")
async def export_council_pdf(session_id: str):
    """Export a council session as a PDF report."""
    try:
        from backend.tools.pdf_export import generate_pdf
    except ImportError:
        raise HTTPException(500, "PDF export not available (reportlab not installed)")

    # Build session data from stored results or placeholder
    session_data = {
        "session_id": session_id,
        "query": "Council session export",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_outputs": [],
        "debate_history": [],
        "recommendation": "Session data not persisted yet — export shows template.",
        "risk_scores": [],
    }

    # Try to load from DB if available
    try:
        from backend.db.neon import execute_query
        rows = await execute_query(
            "SELECT * FROM council_sessions WHERE session_id = $1", session_id
        )
        if rows:
            row = dict(rows[0])
            session_data["query"] = row.get("query", session_data["query"])
            session_data["recommendation"] = row.get("recommendation", session_data["recommendation"])
            session_data["timestamp"] = str(row.get("created_at", session_data["timestamp"]))
            if row.get("agent_outputs"):
                import json as _json
                session_data["agent_outputs"] = _json.loads(row["agent_outputs"]) if isinstance(row["agent_outputs"], str) else row["agent_outputs"]
            if row.get("risk_scores"):
                import json as _json
                session_data["risk_scores"] = _json.loads(row["risk_scores"]) if isinstance(row["risk_scores"], str) else row["risk_scores"]
    except Exception:
        pass

    try:
        pdf_bytes = await generate_pdf(session_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=council_{session_id[:8]}.pdf"},
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(500, f"PDF export failed: {e}")
