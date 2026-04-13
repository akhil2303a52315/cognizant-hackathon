"""Tests for LangGraph workflow: node execution, conditional edges, state flow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.graph import (
    rag_prefetch, mcp_escalation, predictions_node, debate_node,
    fallback_node, brand_enhancement_node, needs_brand_enhancement,
    build_council_graph,
)
from backend.state import AgentOutput


def _make_full_state() -> dict:
    return {
        "query": "Taiwan chip crisis impact on EV battery supply chain",
        "messages": [],
        "risk_score": None,
        "recommendation": None,
        "confidence": None,
        "debate_history": [],
        "fallback_options": [],
        "agent_outputs": [
            AgentOutput(agent="risk", confidence=80.0, contribution="High risk",
                         key_points=["chip shortage"], model_used="t", provider="t"),
            AgentOutput(agent="supply", confidence=60.0, contribution="Moderate",
                         key_points=["alternatives"], model_used="t", provider="t"),
            AgentOutput(agent="logistics", confidence=70.0, contribution="Delays",
                         key_points=["port delays"], model_used="t", provider="t"),
            AgentOutput(agent="market", confidence=55.0, contribution="Price hike",
                         key_points=["inflation"], model_used="t", provider="t"),
            AgentOutput(agent="finance", confidence=65.0, contribution="Hedging",
                         key_points=["exposure"], model_used="t", provider="t"),
            AgentOutput(agent="brand", confidence=40.0, contribution="Brand risk",
                         key_points=["sentiment"], model_used="t", provider="t"),
        ],
        "evidence": [],
        "round_number": 1,
        "llm_calls_log": [],
        "session_id": "test-session",
        "context": {
            "rag_contexts": {"risk": "context", "moderator": "context"},
            "mcp_contexts": {},
            "rag_meta": {},
        },
        "debate_rounds": [],
        "predictions": [],
        "tiered_fallbacks": [],
        "brand_sentiment": None,
        "human_approved": None,
    }


# ---------------------------------------------------------------------------
# RAG prefetch node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rag_prefetch_no_query():
    state = {"query": "", "context": {}}
    result = await rag_prefetch(state)
    assert "context" in result


@pytest.mark.asyncio
async def test_rag_prefetch_with_query():
    state = {"query": "chip shortage", "context": {}}
    # Patch at the source module since graph.py uses lazy import
    with patch("backend.rag.agent_rag_integration.prefetch_rag_for_all_agents",
               new_callable=AsyncMock, return_value={"risk": "context"}):
        result = await rag_prefetch(state)
    assert "context" in result


# ---------------------------------------------------------------------------
# MCP escalation node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mcp_escalation_no_query():
    state = {"query": "", "context": {}}
    result = await mcp_escalation(state)
    assert "context" in result


@pytest.mark.asyncio
async def test_mcp_escalation_with_rag_context():
    state = {"query": "chip shortage", "context": {"rag_contexts": {"risk": "confidence: 50%"}}}
    with patch("backend.mcp.agent_mcp_integration.prefetch_mcp_for_all_agents",
               new_callable=AsyncMock, return_value={"risk": "mcp data"}):
        result = await mcp_escalation(state)
    assert "context" in result
    assert result["context"]["rag_meta"]["risk"] == 0.5


# ---------------------------------------------------------------------------
# Predictions node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_predictions_node_no_query():
    state = {"query": ""}
    result = await predictions_node(state)
    assert result["predictions"] == []


@pytest.mark.asyncio
async def test_predictions_node_with_query():
    state = {"query": "chip shortage", "context": {}}
    with patch("backend.predictions_engine.generate_predictions_for_debate",
               new_callable=AsyncMock,
               return_value=[{"metric": "price", "method": "ensemble", "point_estimate": 2.5}]):
        result = await predictions_node(state)
    assert len(result["predictions"]) > 0


# ---------------------------------------------------------------------------
# Debate node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_debate_node_success():
    state = _make_full_state()
    mock_debate_result = {
        "debate_rounds": [{"round_number": 1, "phase": "analysis", "round_confidence": 60}],
        "confidence": 0.65, "risk_score": 70.0,
        "recommendation": "Take action", "fallback_options": [],
        "debate_history": [{"round": 1, "phase": "analysis", "confidence": 60}],
    }
    # Patch debate_engine at its source module
    with patch("backend.debate_engine.debate_engine") as mock_engine:
        mock_engine.run_debate = AsyncMock(return_value=mock_debate_result)
        result = await debate_node(state)

    assert len(result["debate_rounds"]) > 0
    assert result["confidence"] == 0.65


@pytest.mark.asyncio
async def test_debate_node_failure():
    state = _make_full_state()
    with patch("backend.debate_engine.debate_engine") as mock_engine:
        mock_engine.run_debate = AsyncMock(side_effect=Exception("LLM down"))
        result = await debate_node(state)

    assert result["confidence"] == 0.0
    assert result["risk_score"] == 50.0
    assert "failed" in result["recommendation"].lower()


# ---------------------------------------------------------------------------
# Fallback node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fallback_node():
    state = _make_full_state()
    state["risk_score"] = 70.0
    with patch("backend.fallback_engine.fallback_engine") as mock_engine:
        mock_engine.generate_fallbacks = AsyncMock(
            return_value={"tiered_fallbacks": [{"tier": 1, "name": "Near-Shoring"}]}
        )
        result = await fallback_node(state)
    assert len(result["tiered_fallbacks"]) > 0


# ---------------------------------------------------------------------------
# Brand enhancement node
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_brand_enhancement_node():
    state = _make_full_state()
    with patch("backend.brand_agent_enhancement.brand_enhancer") as mock_enhancer:
        mock_enhancer.run_full_enhancement = AsyncMock(
            return_value={"brand_sentiment": {"overall_sentiment": "crisis", "sentiment_score": -0.7}}
        )
        result = await brand_enhancement_node(state)
    assert result["brand_sentiment"]["overall_sentiment"] == "crisis"


@pytest.mark.asyncio
async def test_brand_enhancement_node_failure():
    state = _make_full_state()
    with patch("backend.brand_agent_enhancement.brand_enhancer") as mock_enhancer:
        mock_enhancer.run_full_enhancement = AsyncMock(side_effect=Exception("MCP down"))
        result = await brand_enhancement_node(state)
    assert result["brand_sentiment"] is None


# ---------------------------------------------------------------------------
# Conditional edge: needs_brand_enhancement
# ---------------------------------------------------------------------------
def test_needs_brand_enhancement_low_confidence():
    state = {
        "query": "chip crisis",
        "agent_outputs": [
            AgentOutput(agent="brand", confidence=35.0, contribution="",
                         key_points=[], model_used="t", provider="t"),
        ],
    }
    assert needs_brand_enhancement(state) == "brand_enhancement"


def test_needs_brand_enhancement_keyword():
    state = {
        "query": "brand reputation crisis for chip makers",
        "agent_outputs": [
            AgentOutput(agent="brand", confidence=80.0, contribution="",
                         key_points=[], model_used="t", provider="t"),
        ],
    }
    assert needs_brand_enhancement(state) == "brand_enhancement"


def test_skip_brand_enhancement():
    state = {
        "query": "supply chain logistics optimization",
        "agent_outputs": [
            AgentOutput(agent="brand", confidence=85.0, contribution="",
                         key_points=[], model_used="t", provider="t"),
        ],
    }
    assert needs_brand_enhancement(state) == "skip_brand"


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------
def test_build_council_graph():
    graph = build_council_graph()
    assert graph is not None
    # Verify all nodes exist
    node_names = set(graph.nodes.keys())
    expected_nodes = {
        "moderator", "rag_prefetch", "mcp_escalation",
        "risk", "supply", "logistics", "market", "finance", "brand",
        "predictions", "debate", "fallback", "brand_enhancement", "synthesize",
    }
    assert expected_nodes.issubset(node_names), f"Missing nodes: {expected_nodes - node_names}"


def test_graph_has_entry_point():
    graph = build_council_graph()
    # Entry point should be moderator
    assert "moderator" in graph.nodes
