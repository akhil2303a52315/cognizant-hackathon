from typing import TypedDict, List, Optional
from pydantic import BaseModel


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


class CouncilState(TypedDict):
    query: str
    messages: List[dict]
    risk_score: Optional[float]
    recommendation: Optional[str]
    confidence: Optional[float]
    debate_history: List[dict]
    fallback_options: List[Action]
    agent_outputs: List[AgentOutput]
    evidence: List[Evidence]
    round_number: int
    llm_calls_log: List[dict]
    session_id: Optional[str]
    context: Optional[dict]
