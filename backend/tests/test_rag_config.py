"""Tests for RAG configuration and agent profiles."""

import pytest
from backend.rag.rag_config import (
    get_agent_profile, get_rag_settings, AGENT_RAG_PROFILES,
    CRITIQUE_TOP_K, SELF_REFLECTION_THRESHOLD, MAX_RETRIEVAL_LOOPS,
    VECTOR_DRIFT_THRESHOLD,
)


def test_all_agents_have_profiles():
    expected = ["risk", "supply", "logistics", "market", "finance", "brand", "moderator"]
    for agent in expected:
        assert agent in AGENT_RAG_PROFILES, f"Missing profile for {agent}"


def test_profile_structure():
    for name, profile in AGENT_RAG_PROFILES.items():
        assert "collection" in profile, f"{name} missing 'collection'"
        assert "top_k" in profile, f"{name} missing 'top_k'"
        assert "recency_days" in profile, f"{name} missing 'recency_days'"
        assert "confidence_threshold" in profile, f"{name} missing 'confidence_threshold'"
        assert "mcp_escalation_tools" in profile, f"{name} missing 'mcp_escalation_tools'"
        assert isinstance(profile["top_k"], int)
        assert profile["top_k"] > 0
        assert 0 < profile["confidence_threshold"] <= 1.0


def test_get_agent_profile_valid():
    profile = get_agent_profile("risk")
    assert profile["collection"] == "risk-events-gdelt"
    assert profile["top_k"] == 6
    assert profile["agent"] == "risk"


def test_get_agent_profile_fallback():
    profile = get_agent_profile("nonexistent_agent")
    # Falls back to risk profile but adds agent key
    assert profile["collection"] == AGENT_RAG_PROFILES["risk"]["collection"]
    assert profile["agent"] == "nonexistent_agent"


def test_rag_settings():
    settings = get_rag_settings()
    assert "embedding_provider" in settings
    assert "chunk_size" in settings
    assert "chunk_overlap" in settings
    assert "agent_profiles" in settings


def test_constants():
    assert CRITIQUE_TOP_K > 0
    assert 0 < SELF_REFLECTION_THRESHOLD <= 1.0
    assert MAX_RETRIEVAL_LOOPS >= 1
    assert VECTOR_DRIFT_THRESHOLD > 0


def test_mcp_escalation_tools_per_agent():
    for name, profile in AGENT_RAG_PROFILES.items():
        tools = profile["mcp_escalation_tools"]
        assert isinstance(tools, list), f"{name} escalation tools not a list"
        if name != "moderator":
            assert len(tools) >= 1, f"{name} has no MCP escalation tools"
