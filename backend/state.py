from typing import TypedDict, List, Optional, Annotated
from pydantic import BaseModel
import operator


class AgentOutput(BaseModel):
    agent: str
    confidence: float
    contribution: str
    key_points: List[str]
    model_used: str
    provider: str


class Evidence(BaseModel):
    type: str
    id: str
    tag: Optional[str] = None


class Action(BaseModel):
    type: str
    details: str
    cost_estimate: Optional[float] = None
    time_to_implement: Optional[str] = None


def _list_reducer(current: list, update: list) -> list:
    return current + update if current else (update or [])


class CouncilState(TypedDict):
    query: str
    messages: Annotated[List[dict], operator.add]
    risk_score: Optional[float]
    recommendation: Optional[str]
    confidence: Optional[float]
    debate_history: Annotated[List[dict], operator.add]
    fallback_options: Annotated[List[Action], _list_reducer]
    agent_outputs: Annotated[List[AgentOutput], _list_reducer]
    evidence: Annotated[List[Evidence], _list_reducer]
    round_number: int
    llm_calls_log: Annotated[List[dict], operator.add]
    session_id: Optional[str]
    context: Optional[dict]
