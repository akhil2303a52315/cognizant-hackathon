"""Tests for FallbackEngine: tiered fallbacks, cost/ROI, one-click execution."""

import pytest
from unittest.mock import AsyncMock, patch
from backend.fallback_engine import FallbackEngine, fallback_engine, FALLBACK_TEMPLATES
from backend.state import AgentOutput, FallbackOption


def _make_state(risk_score=70.0) -> dict:
    return {
        "query": "Taiwan chip crisis impact on EV battery supply chain",
        "agent_outputs": [
            AgentOutput(agent="risk", confidence=80.0, contribution="High risk",
                         key_points=[], model_used="t", provider="t"),
            AgentOutput(agent="supply", confidence=60.0, contribution="Moderate",
                         key_points=[], model_used="t", provider="t"),
        ],
        "predictions": [
            {"metric": "disruption_probability", "method": "ensemble",
             "point_estimate": 0.55, "ci_lower": 0.35, "ci_upper": 0.75,
             "confidence": 0.7, "horizon_days": 90, "data_points_used": 1000},
            {"metric": "price", "method": "ensemble",
             "point_estimate": 2.5, "ci_lower": 1.8, "ci_upper": 3.2,
             "confidence": 0.6, "horizon_days": 90, "data_points_used": 100},
        ],
        "risk_score": risk_score,
        "debate_rounds": [],
    }


# ---------------------------------------------------------------------------
# Template validation
# ---------------------------------------------------------------------------
def test_all_tiers_represented():
    tiers = {t.tier for t in FALLBACK_TEMPLATES.values()}
    assert 1 in tiers
    assert 2 in tiers
    assert 3 in tiers


def test_template_count():
    assert len(FALLBACK_TEMPLATES) == 9  # 3 per tier


def test_tier1_has_mcp_tools():
    tier1 = [t for t in FALLBACK_TEMPLATES.values() if t.tier == 1]
    for t in tier1:
        assert t.mcp_tool is not None, f"Tier 1 '{t.name}' missing MCP tool"


def test_tier3_may_not_have_mcp():
    tier3 = [t for t in FALLBACK_TEMPLATES.values() if t.tier == 3]
    # Tier 3 may have None MCP tools (strategic, manual execution)
    for t in tier3:
        assert t.cost_estimate_usd > 0
        assert t.time_to_implement_days > 30  # strategic = longer


def test_all_templates_have_positive_roi():
    for name, t in FALLBACK_TEMPLATES.items():
        assert t.roi_pct > 0, f"{name} has non-positive ROI"
        assert t.risk_reduction_pct > 0, f"{name} has non-positive risk reduction"
        assert t.confidence > 0, f"{name} has zero confidence"


def test_cost_increases_by_tier():
    tier1_avg = sum(t.cost_estimate_usd for t in FALLBACK_TEMPLATES.values() if t.tier == 1) / 3
    tier2_avg = sum(t.cost_estimate_usd for t in FALLBACK_TEMPLATES.values() if t.tier == 2) / 3
    tier3_avg = sum(t.cost_estimate_usd for t in FALLBACK_TEMPLATES.values() if t.tier == 3) / 3
    assert tier1_avg < tier2_avg < tier3_avg


# ---------------------------------------------------------------------------
# FallbackEngine: generate_fallbacks
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_high_risk_all_tiers():
    engine = FallbackEngine()
    state = _make_state(risk_score=75.0)
    result = await engine.generate_fallbacks(state)
    fallbacks = result["tiered_fallbacks"]
    tiers = {f["tier"] for f in fallbacks}
    assert 1 in tiers
    assert 2 in tiers
    assert 3 in tiers


@pytest.mark.asyncio
async def test_medium_risk_tier1_and_2():
    engine = FallbackEngine()
    state = _make_state(risk_score=45.0)
    result = await engine.generate_fallbacks(state)
    fallbacks = result["tiered_fallbacks"]
    tiers = {f["tier"] for f in fallbacks}
    assert 1 in tiers
    assert 2 in tiers
    assert 3 not in tiers


@pytest.mark.asyncio
async def test_low_risk_tier2_only():
    engine = FallbackEngine()
    state = _make_state(risk_score=15.0)
    result = await engine.generate_fallbacks(state)
    fallbacks = result["tiered_fallbacks"]
    tiers = {f["tier"] for f in fallbacks}
    assert 2 in tiers
    assert 1 not in tiers


@pytest.mark.asyncio
async def test_fallbacks_sorted_by_tier():
    engine = FallbackEngine()
    state = _make_state(risk_score=75.0)
    result = await engine.generate_fallbacks(state)
    fallbacks = result["tiered_fallbacks"]
    tiers = [f["tier"] for f in fallbacks]
    assert tiers == sorted(tiers)


@pytest.mark.asyncio
async def test_fallbacks_have_required_fields():
    engine = FallbackEngine()
    state = _make_state(risk_score=75.0)
    result = await engine.generate_fallbacks(state)
    for f in result["tiered_fallbacks"]:
        assert "tier" in f
        assert "name" in f
        assert "cost_estimate_usd" in f
        assert "time_to_implement_days" in f
        assert "risk_reduction_pct" in f
        assert "roi_pct" in f
        assert "confidence" in f


# ---------------------------------------------------------------------------
# FallbackEngine: one-click execution
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_execute_fallback_with_mcp():
    engine = FallbackEngine()
    fallback = {
        "name": "Near-Shoring Emergency",
        "tier": 1,
        "cost_estimate_usd": 150000,
        "mcp_tool": "supplier_search",
        "mcp_params": {"product": "chips", "region": "nearshore"},
    }

    mock_result = {"success": True, "result": {"suppliers": []}}
    with patch("backend.mcp.secure_mcp.secure_invoke", new_callable=AsyncMock, return_value=mock_result):
        result = await engine.execute_fallback(fallback, "supply")

    assert result["success"] is True
    assert result["fallback"] == "Near-Shoring Emergency"


@pytest.mark.asyncio
async def test_execute_fallback_no_mcp_tool():
    engine = FallbackEngine()
    fallback = {
        "name": "Vertical Integration",
        "tier": 3,
        "mcp_tool": None,
        "mcp_params": None,
    }
    result = await engine.execute_fallback(fallback, "supply")
    assert result["success"] is False
    assert "manual execution" in result["error"].lower()


@pytest.mark.asyncio
async def test_execute_fallback_mcp_failure():
    engine = FallbackEngine()
    fallback = {
        "name": "Test Fallback",
        "tier": 1,
        "mcp_tool": "nonexistent_tool",
        "mcp_params": {},
    }

    mock_result = {"success": False, "warnings": ["Tool not found"]}
    with patch("backend.mcp.secure_mcp.secure_invoke", new_callable=AsyncMock, return_value=mock_result):
        result = await engine.execute_fallback(fallback, "supply")

    assert result["success"] is False


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
def test_fallback_engine_singleton():
    from backend.fallback_engine import fallback_engine
    assert isinstance(fallback_engine, FallbackEngine)
