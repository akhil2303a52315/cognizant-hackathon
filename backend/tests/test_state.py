"""Tests for CouncilState and all Pydantic models (Day 3-5)."""

import pytest
from backend.state import (
    AgentOutput, Evidence, Action, DebateRound, FallbackOption,
    Prediction, BrandSentiment, CouncilState,
)


# ---------------------------------------------------------------------------
# AgentOutput
# ---------------------------------------------------------------------------
def test_agent_output_valid():
    o = AgentOutput(agent="risk", confidence=85.0, contribution="High risk",
                    key_points=["point1"], model_used="groq:llama3", provider="groq")
    assert o.agent == "risk"
    assert o.confidence == 85.0
    assert len(o.key_points) == 1


def test_agent_output_defaults():
    o = AgentOutput(agent="supply", confidence=0.0, contribution="",
                    key_points=[], model_used="test", provider="test")
    assert o.key_points == []


# ---------------------------------------------------------------------------
# DebateRound
# ---------------------------------------------------------------------------
def test_debate_round_valid():
    r = DebateRound(
        round_number=1, phase="analysis",
        agent_contributions=[{"agent": "risk", "point": "test", "confidence": 80, "challenges": []}],
        key_disagreements=["gap1"], consensus_points=["agree1"],
        round_confidence=75.0,
    )
    assert r.round_number == 1
    assert r.phase == "analysis"
    assert len(r.key_disagreements) == 1
    assert r.round_confidence == 75.0


def test_debate_round_phases():
    for phase in ["analysis", "challenge", "validation"]:
        r = DebateRound(round_number=1, phase=phase,
                        agent_contributions=[], key_disagreements=[],
                        consensus_points=[], round_confidence=50.0)
        assert r.phase == phase


# ---------------------------------------------------------------------------
# FallbackOption
# ---------------------------------------------------------------------------
def test_fallback_option_tier1():
    f = FallbackOption(
        tier=1, name="Near-Shoring", description="Emergency activation",
        cost_estimate_usd=150000, time_to_implement_days=3,
        risk_reduction_pct=25.0, roi_pct=180.0, confidence=0.85,
        mcp_tool="supplier_search", mcp_params={"product": "chips"},
    )
    assert f.tier == 1
    assert f.cost_estimate_usd == 150000
    assert f.mcp_tool == "supplier_search"


def test_fallback_option_no_mcp():
    f = FallbackOption(
        tier=3, name="Vertical Integration", description="Long-term",
        cost_estimate_usd=15000000, time_to_implement_days=365,
        risk_reduction_pct=70.0, roi_pct=250.0, confidence=0.45,
    )
    assert f.mcp_tool is None
    assert f.mcp_params is None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def test_prediction_valid():
    p = Prediction(
        metric="price", horizon_days=90, point_estimate=2.45,
        ci_lower=1.80, ci_upper=3.20, confidence=0.65,
        method="ensemble", data_points_used=10000,
    )
    assert p.metric == "price"
    assert p.ci_lower < p.point_estimate < p.ci_upper


def test_prediction_methods():
    for method in ["prophet", "lstm_stub", "monte_carlo", "ensemble", "simple_trend"]:
        p = Prediction(metric="test", horizon_days=30, point_estimate=1.0,
                       ci_lower=0.5, ci_upper=1.5, confidence=0.5,
                       method=method, data_points_used=100)
        assert p.method == method


# ---------------------------------------------------------------------------
# BrandSentiment
# ---------------------------------------------------------------------------
def test_brand_sentiment_crisis():
    b = BrandSentiment(
        overall_sentiment="crisis", sentiment_score=-0.8,
        trending_topics=["chip shortage"], crisis_keywords=["shortage", "crisis"],
        recommended_actions=["Issue statement"],
        crisis_comm_draft="PRESS RELEASE: ...",
        ad_pivot_recommendation="Shift to reassurance",
        competitor_activity="Competitor X diversifying",
    )
    assert b.overall_sentiment == "crisis"
    assert b.sentiment_score < 0
    assert b.crisis_comm_draft is not None


def test_brand_sentiment_minimal():
    b = BrandSentiment(
        overall_sentiment="neutral", sentiment_score=0.0,
        trending_topics=[], crisis_keywords=[], recommended_actions=[],
    )
    assert b.crisis_comm_draft is None
    assert b.ad_pivot_recommendation is None


# ---------------------------------------------------------------------------
# CouncilState structure
# ---------------------------------------------------------------------------
def test_council_state_keys():
    state = CouncilState(
        query="test", messages=[], risk_score=None,
        recommendation=None, confidence=None, debate_history=[],
        fallback_options=[], agent_outputs=[], evidence=[],
        round_number=1, llm_calls_log=[], session_id=None,
        context=None, debate_rounds=[], predictions=[],
        tiered_fallbacks=[], brand_sentiment=None, human_approved=None,
    )
    assert state["query"] == "test"
    assert state["round_number"] == 1
    assert state["debate_rounds"] == []
    assert state["human_approved"] is None
