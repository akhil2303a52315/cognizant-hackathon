"""Tests for DebateEngine: 3-round debate, consensus logic, challenge/counter."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.debate_engine import DebateEngine, debate_engine, CONSENSUS_THRESHOLD
from backend.state import AgentOutput, DebateRound


def _make_outputs() -> list[AgentOutput]:
    return [
        AgentOutput(agent="risk", confidence=80.0, contribution="High disruption risk from Taiwan",
                     key_points=["chip shortage"], model_used="groq:llama3", provider="groq"),
        AgentOutput(agent="supply", confidence=60.0, contribution="Moderate supply impact, alternatives available",
                     key_points=["alternative suppliers"], model_used="groq:llama3", provider="groq"),
        AgentOutput(agent="logistics", confidence=70.0, contribution="Route delays expected",
                     key_points=["port delays"], model_used="groq:llama3", provider="groq"),
        AgentOutput(agent="market", confidence=55.0, contribution="Price increase likely",
                     key_points=["price hike"], model_used="groq:llama3", provider="groq"),
        AgentOutput(agent="finance", confidence=65.0, contribution="Moderate financial exposure",
                     key_points=["hedging needed"], model_used="groq:llama3", provider="groq"),
        AgentOutput(agent="brand", confidence=40.0, contribution="Significant brand risk",
                     key_points=["consumer sentiment"], model_used="groq:llama3", provider="groq"),
    ]


def _make_state(outputs=None) -> dict:
    return {
        "query": "Taiwan chip crisis impact on EV battery supply chain",
        "agent_outputs": outputs or _make_outputs(),
        "context": {"rag_contexts": {}, "mcp_contexts": {}},
        "debate_rounds": [],
        "predictions": [],
        "tiered_fallbacks": [],
        "round_number": 1,
    }


# ---------------------------------------------------------------------------
# Unit tests (no LLM calls)
# ---------------------------------------------------------------------------
def test_find_challenge_target():
    engine = DebateEngine()
    outputs = _make_outputs()
    target = engine._find_challenge_target(outputs[0], outputs)
    # Risk (80) should target brand (40) — largest gap
    assert target is not None
    assert target.agent == "brand"


def test_find_challenge_target_no_gap():
    engine = DebateEngine()
    o1 = AgentOutput(agent="a", confidence=50, contribution="", key_points=[], model_used="t", provider="t")
    o2 = AgentOutput(agent="b", confidence=50, contribution="", key_points=[], model_used="t", provider="t")
    target = engine._find_challenge_target(o1, [o1, o2])
    # When gap=0, no target is found (gap > max_gap is False)
    assert target is None


def test_parse_confidence():
    engine = DebateEngine()
    assert engine._parse_confidence("Overall council confidence: 72", 50) == 72.0
    assert engine._parse_confidence("confidence score: 85", 50) == 85.0
    assert engine._parse_confidence("65% confidence", 50) == 65.0
    assert engine._parse_confidence("confidence: 0.72", 50) == 72.0
    assert engine._parse_confidence("no number here", 50) == 50  # fallback


def test_parse_risk_score():
    engine = DebateEngine()
    assert engine._parse_risk_score("Risk score: 68", 50) == 68.0
    assert engine._parse_risk_score("risk: 45", 50) == 45.0
    assert engine._parse_risk_score("no risk here", 50) == 50  # fallback


def test_format_debate_summary():
    engine = DebateEngine()
    rounds = [
        {"round_number": 1, "phase": "analysis", "round_confidence": 60,
         "consensus_points": ["action needed"], "key_disagreements": ["gap"]},
        {"round_number": 2, "phase": "challenge", "round_confidence": 70,
         "consensus_points": ["near-shore"], "key_disagreements": []},
    ]
    summary = engine._format_debate_summary(rounds)
    assert "Round 1" in summary
    assert "Round 2" in summary
    assert "analysis" in summary
    assert "challenge" in summary


def test_generate_fallbacks_high_risk():
    engine = DebateEngine()
    outputs = _make_outputs()
    fallbacks = engine._generate_fallbacks(outputs, risk_score=75)
    assert len(fallbacks) >= 2
    types = [f["type"] for f in fallbacks]
    assert "tier1_immediate" in types


def test_generate_fallbacks_low_risk():
    engine = DebateEngine()
    outputs = _make_outputs()
    # DebateEngine._generate_fallbacks only adds for risk > 30
    fallbacks = engine._generate_fallbacks(outputs, risk_score=20)
    assert len(fallbacks) == 0  # no fallbacks for risk <= 30


def test_merge_challenge_results():
    engine = DebateEngine()
    outputs = _make_outputs()
    round2 = {
        "agent_contributions": [
            {"agent": "risk", "challenged": "brand", "challenge": "test",
             "updated_confidence": 75.0, "model_used": "test"},
            {"agent": "supply", "challenged": "market", "challenge": "test",
             "updated_confidence": 65.0, "model_used": "test"},
        ],
    }
    updated = engine._merge_challenge_results(outputs, round2)
    risk_out = [o for o in updated if o.agent == "risk"][0]
    assert risk_out.confidence == 75.0
    supply_out = [o for o in updated if o.agent == "supply"][0]
    assert supply_out.confidence == 65.0


# ---------------------------------------------------------------------------
# Integration tests (mocked LLM) — simplified to avoid hanging
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_round_analysis_mocked():
    engine = DebateEngine()
    outputs = _make_outputs()

    mock_response = MagicMock()
    mock_response.content = '{"disagreements": ["Risk gap 40%"], "consensus": ["Action needed"]}'

    with patch.object(engine, '_extract_positions', new_callable=AsyncMock,
                      return_value=(['gap'], ['consensus'])):
        result = await engine._round_analysis(outputs, "test query", {})

    assert result["round_number"] == 1
    assert result["phase"] == "analysis"
    assert len(result["agent_contributions"]) == 6
    assert result["round_confidence"] > 0


@pytest.mark.asyncio
async def test_round_challenge_mocked():
    engine = DebateEngine()
    outputs = _make_outputs()

    mock_response = MagicMock()
    mock_response.content = "I challenge their assumption. Updated confidence: 70%"

    with patch("backend.debate_engine.llm_router") as mock_router, \
         patch.object(engine, '_extract_positions_from_challenges',
                      return_value=(['disagree'], ['agree'])):
        mock_router.invoke_with_fallback = AsyncMock(return_value=(mock_response, "test"))
        result = await engine._round_challenge(outputs, "test query", {})

    assert result["round_number"] == 2
    assert result["phase"] == "challenge"
    assert len(result["agent_contributions"]) > 0


@pytest.mark.asyncio
async def test_full_debate_consensus_early_mocked():
    engine = DebateEngine()
    outputs = [
        AgentOutput(agent="risk", confidence=90.0, contribution="Low risk",
                     key_points=[], model_used="t", provider="t"),
        AgentOutput(agent="supply", confidence=88.0, contribution="Stable",
                     key_points=[], model_used="t", provider="t"),
    ]
    state = _make_state(outputs)

    mock_response = MagicMock()
    mock_response.content = 'Council confidence: 89. Risk score: 20'

    with patch("backend.debate_engine.llm_router") as mock_router, \
         patch.object(engine, '_extract_positions', new_callable=AsyncMock,
                      return_value=([], ['Low risk'])):
        mock_router.invoke_with_fallback = AsyncMock(return_value=(mock_response, "test"))
        result = await engine.run_debate(state)

    assert len(result["debate_rounds"]) >= 1
    assert result["confidence"] is not None


@pytest.mark.asyncio
async def test_full_debate_no_outputs():
    engine = DebateEngine()
    # Use explicit state dict to avoid any state leakage
    state = {
        "query": "test",
        "agent_outputs": [],
        "context": {},
        "debate_rounds": [],
        "predictions": [],
        "tiered_fallbacks": [],
        "round_number": 1,
    }
    result = await engine.run_debate(state)
    assert result["recommendation"] == "No agent outputs to debate."
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_debate_engine_singleton():
    from backend.debate_engine import debate_engine
    assert isinstance(debate_engine, DebateEngine)
