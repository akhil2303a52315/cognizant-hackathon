"""Tests for BrandAgentEnhancer: sentiment analysis, crisis comms, ad pivot."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.brand_agent_enhancement import BrandAgentEnhancer, brand_enhancer
from backend.state import BrandSentiment, AgentOutput


def _make_state() -> dict:
    return {
        "query": "Taiwan chip crisis impact on EV battery supply chain",
        "agent_outputs": [
            AgentOutput(agent="brand", confidence=35.0, contribution="Significant brand risk detected",
                         key_points=["consumer sentiment dropping"], model_used="t", provider="t"),
        ],
        "context": {"rag_contexts": {"brand": "Historical brand data"}, "mcp_contexts": {}},
    }


def _mock_llm_response(content: str):
    mock = MagicMock()
    mock.content = content
    return mock


# ---------------------------------------------------------------------------
# Sentiment JSON parsing
# ---------------------------------------------------------------------------
def test_parse_sentiment_json_valid():
    enhancer = BrandAgentEnhancer()
    text = '''```json
    {"overall_sentiment": "crisis", "sentiment_score": -0.65,
     "trending_topics": ["chips"], "crisis_keywords": ["shortage"],
     "recommended_actions": ["Issue statement"]}
    ```'''
    result = enhancer._parse_sentiment_json(text)
    assert result["overall_sentiment"] == "crisis"
    assert result["sentiment_score"] == -0.65
    assert "chips" in result["trending_topics"]


def test_parse_sentiment_json_bare():
    enhancer = BrandAgentEnhancer()
    text = '{"overall_sentiment": "neutral", "sentiment_score": 0.0, "trending_topics": [], "crisis_keywords": [], "recommended_actions": []}'
    result = enhancer._parse_sentiment_json(text)
    assert result["overall_sentiment"] == "neutral"


def test_parse_sentiment_json_no_json():
    enhancer = BrandAgentEnhancer()
    result = enhancer._parse_sentiment_json("No JSON here at all")
    assert result["overall_sentiment"] == "neutral"
    assert result["sentiment_score"] == 0.0


def test_parse_sentiment_json_partial():
    enhancer = BrandAgentEnhancer()
    text = '{"overall_sentiment": "negative", "sentiment_score": -0.3}'
    result = enhancer._parse_sentiment_json(text)
    assert result["overall_sentiment"] == "negative"
    assert result["trending_topics"] == []


# ---------------------------------------------------------------------------
# Sentiment analysis (mocked LLM + MCP)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyze_sentiment():
    enhancer = BrandAgentEnhancer()
    state = _make_state()

    sentiment_json = json.dumps({
        "overall_sentiment": "crisis",
        "sentiment_score": -0.7,
        "trending_topics": ["chip shortage", "EV"],
        "crisis_keywords": ["shortage", "crisis"],
        "recommended_actions": ["Issue supplier statement", "Activate crisis comms"],
    })

    with patch("backend.brand_agent_enhancement.llm_router") as mock_router, \
         patch.object(enhancer, "_fetch_brand_mcp_data", new_callable=AsyncMock, return_value="News data"):
        mock_router.invoke_with_fallback = AsyncMock(
            return_value=(_mock_llm_response(sentiment_json), "test")
        )
        result = await enhancer.analyze_sentiment(state)

    assert isinstance(result, BrandSentiment)
    assert result.overall_sentiment == "crisis"
    assert result.sentiment_score < 0
    assert len(result.crisis_keywords) > 0


# ---------------------------------------------------------------------------
# Crisis communication
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_crisis_comm():
    enhancer = BrandAgentEnhancer()
    state = _make_state()
    sentiment = BrandSentiment(
        overall_sentiment="crisis", sentiment_score=-0.8,
        trending_topics=["chips"], crisis_keywords=["shortage"],
        recommended_actions=["Issue statement"],
    )

    with patch("backend.brand_agent_enhancement.llm_router") as mock_router:
        mock_router.invoke_with_fallback = AsyncMock(
            return_value=(_mock_llm_response("FOR IMMEDIATE RELEASE: ..."), "test")
        )
        result = await enhancer.generate_crisis_comm(state, sentiment)

    assert "RELEASE" in result or len(result) > 50


# ---------------------------------------------------------------------------
# Ad pivot
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_recommend_ad_pivot():
    enhancer = BrandAgentEnhancer()
    state = _make_state()
    sentiment = BrandSentiment(
        overall_sentiment="negative", sentiment_score=-0.4,
        trending_topics=[], crisis_keywords=[],
        recommended_actions=[],
    )

    with patch("backend.brand_agent_enhancement.llm_router") as mock_router:
        mock_router.invoke_with_fallback = AsyncMock(
            return_value=(_mock_llm_response("1. Pause awareness campaigns\n2. Shift to reassurance"), "test")
        )
        result = await enhancer.recommend_ad_pivot(state, sentiment)

    assert len(result) > 0


# ---------------------------------------------------------------------------
# Full enhancement pipeline
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_full_enhancement_crisis():
    enhancer = BrandAgentEnhancer()
    state = _make_state()

    sentiment_json = json.dumps({
        "overall_sentiment": "crisis", "sentiment_score": -0.8,
        "trending_topics": ["chips"], "crisis_keywords": ["shortage"],
        "recommended_actions": ["Issue statement"],
    })

    with patch("backend.brand_agent_enhancement.llm_router") as mock_router, \
         patch.object(enhancer, "_fetch_brand_mcp_data", new_callable=AsyncMock, return_value="News"), \
         patch.object(enhancer, "_fetch_competitor_data", new_callable=AsyncMock, return_value="Competitor data"):
        mock_router.invoke_with_fallback = AsyncMock(
            return_value=(_mock_llm_response(sentiment_json), "test")
        )
        result = await enhancer.run_full_enhancement(state)

    assert "brand_sentiment" in result
    bs = result["brand_sentiment"]
    assert bs["overall_sentiment"] == "crisis"


@pytest.mark.asyncio
async def test_run_full_enhancement_positive():
    enhancer = BrandAgentEnhancer()
    state = _make_state()

    sentiment_json = json.dumps({
        "overall_sentiment": "positive", "sentiment_score": 0.5,
        "trending_topics": [], "crisis_keywords": [],
        "recommended_actions": [],
    })

    with patch("backend.brand_agent_enhancement.llm_router") as mock_router, \
         patch.object(enhancer, "_fetch_brand_mcp_data", new_callable=AsyncMock, return_value="News"):
        mock_router.invoke_with_fallback = AsyncMock(
            return_value=(_mock_llm_response(sentiment_json), "test")
        )
        result = await enhancer.run_full_enhancement(state)

    bs = result["brand_sentiment"]
    assert bs["overall_sentiment"] == "positive"
    # Positive sentiment → no crisis comm or ad pivot
    assert bs.get("crisis_comm_draft") is None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
def test_brand_enhancer_singleton():
    assert isinstance(brand_enhancer, BrandAgentEnhancer)
