from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _social_sentiment(params: dict):
    brand = params.get("brand", "")
    platform = params.get("platform", "all")

    # Try Firecrawl web_search for real sentiment data
    try:
        from backend.mcp.tools.firecrawl_tools import _web_search
        result = await _web_search({"query": f"{brand} sentiment review feedback", "num_results": 5})
        if not result.get("mock"):
            content_snippets = [r.get("content", "")[:200] for r in result.get("results", [])]
            return {
                "brand": brand,
                "platform": platform,
                "sentiment_score": 0.0,
                "sentiment_trend": "unknown",
                "mention_count_7d": 0,
                "snippets": content_snippets,
                "source": "firecrawl",
                "top_topics": [],
            }
    except Exception:
        pass

    # Mock fallback
    return {
        "brand": brand,
        "platform": platform,
        "sentiment_score": 0.72,
        "sentiment_trend": "declining",
        "mention_count_7d": 15420,
        "negative_pct": 18.5,
        "positive_pct": 62.3,
        "neutral_pct": 19.2,
        "top_topics": ["product quality", "delivery delays", "pricing"],
        "mock": True,
    }


async def _competitor_ads(params: dict):
    competitor = params.get("competitor", "")
    region = params.get("region", "global")
    return {
        "competitor": competitor,
        "region": region,
        "ad_spend_estimate_usd": 2500000,
        "active_campaigns": 8,
        "top_channels": ["Google Ads", "LinkedIn", "Industry publications"],
        "messaging_themes": ["innovation", "reliability", "cost savings"],
        "market_share_change_pct": 2.1,
        "mock": True,
    }


async def _content_generate(params: dict):
    content_type = params.get("content_type", "crisis_comms")
    topic = params.get("topic", "")
    tone = params.get("tone", "professional")
    try:
        from backend.llm.router import llm_router
        messages = [
            {"role": "system", "content": f"You are a brand communications expert. Generate {content_type} content in a {tone} tone."},
            {"role": "user", "content": f"Generate {content_type} about: {topic}"},
        ]
        response, model = await llm_router.invoke_with_fallback("brand", messages)
        return {"content": response.content, "content_type": content_type, "model_used": model}
    except Exception as e:
        return _mock_content(content_type, topic)


def _mock_content(content_type: str, topic: str) -> dict:
    return {
        "content": f"[Draft {content_type}] Regarding {topic}: We are actively monitoring the situation and working with our supply chain partners to ensure continuity. Our priority remains delivering quality products to our customers.",
        "content_type": content_type,
        "mock": True,
    }


def register():
    register_tool(
        name="social_sentiment",
        description="Get social media sentiment analysis for a brand",
        input_schema={
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "Brand name"},
                "platform": {"type": "string", "description": "Platform filter", "default": "all"},
            },
            "required": ["brand"],
        },
        handler=_social_sentiment,
        category="social",
        cache_ttl=300,
    )
    register_tool(
        name="competitor_ads",
        description="Get competitor advertising intelligence",
        input_schema={
            "type": "object",
            "properties": {
                "competitor": {"type": "string", "description": "Competitor name"},
                "region": {"type": "string", "description": "Region", "default": "global"},
            },
            "required": ["competitor"],
        },
        handler=_competitor_ads,
        category="social",
        cache_ttl=7200,
    )
    register_tool(
        name="content_generate",
        description="Generate brand communications content using LLM",
        input_schema={
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "description": "Type of content", "default": "crisis_comms"},
                "topic": {"type": "string", "description": "Topic to write about"},
                "tone": {"type": "string", "description": "Tone", "default": "professional"},
            },
            "required": ["topic"],
        },
        handler=_content_generate,
        category="social",
        cache_ttl=0,
    )
