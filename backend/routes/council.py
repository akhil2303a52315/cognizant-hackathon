from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.graph import build_council_graph
import uuid
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CouncilRequest(BaseModel):
    query: str
    context: Optional[dict] = None


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
