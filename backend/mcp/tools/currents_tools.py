"""Currents API MCP Tools — Alternative real-time news source for Brand and Market agents."""
import httpx
import os

CURRENTS_BASE = "https://api.currentsapi.services/v1"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.currents_api_key or os.getenv("CURRENTS_API_KEY", "")
    except Exception:
        return os.getenv("CURRENTS_API_KEY", "")


def _mock_news(query: str) -> dict:
    return {
        "query": query,
        "articles": [
            {"title": f"Breaking: {query} impact on global markets", "author": "Staff Reporter", "category": "business", "published": "2025-01-15T10:00:00Z", "mock": True},
            {"title": f"Analysis: How {query} affects supply chains", "author": "Industry Analyst", "category": "technology", "published": "2025-01-15T08:00:00Z", "mock": True},
        ],
        "news_count": 2,
        "mock": True,
    }


async def news_search(params: dict) -> dict:
    """Search news articles from Currents API (200+ sources, free tier).

    Args:
        query: Search keywords
        language: Language code (en, zh, de, ja, etc.)
        country: Country code (US, CN, DE, JP, etc.)
        domain: Specific news domain (e.g., 'reuters.com')
    """
    query = params.get("query", "supply chain")
    language = params.get("language", "en")
    country = params.get("country", "")
    domain = params.get("domain", "")
    key = _get_key()

    if not key:
        return _mock_news(query)

    try:
        params_dict = {
            "apiKey": key,
            "keywords": query,
            "language": language,
        }
        if country:
            params_dict["country"] = country
        if domain:
            params_dict["domain"] = domain

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{CURRENTS_BASE}/search", params=params_dict)
            data = resp.json()

        if data.get("news"):
            articles = [{
                "title": a.get("title", ""),
                "description": a.get("description", "")[:300] if a.get("description") else "",
                "url": a.get("url", ""),
                "author": a.get("author", ""),
                "image": a.get("image", ""),
                "category": a.get("category", []),
                "language": a.get("language", ""),
                "published": a.get("published", ""),
                "source": a.get("url", "").split("/")[2] if a.get("url") else "",
            } for a in data["news"][:15]]
            return {
                "query": query,
                "articles": articles,
                "news_count": len(articles),
                "mock": False,
            }

        return _mock_news(query)
    except Exception:
        return _mock_news(query)


async def latest_news(params: dict) -> dict:
    """Get latest news headlines from Currents API.

    Args:
        language: Language code (default: 'en')
        category: Category filter (business, technology, science, health, world, politics)
        country: Country code filter
    """
    language = params.get("language", "en")
    category = params.get("category", "business")
    country = params.get("country", "")
    key = _get_key()

    if not key:
        return _mock_news("latest")

    try:
        params_dict = {
            "apiKey": key,
            "language": language,
        }
        if category:
            params_dict["category"] = category
        if country:
            params_dict["country"] = country

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{CURRENTS_BASE}/latest-news", params=params_dict)
            data = resp.json()

        if data.get("news"):
            articles = [{
                "title": a.get("title", ""),
                "description": a.get("description", "")[:300] if a.get("description") else "",
                "url": a.get("url", ""),
                "author": a.get("author", ""),
                "category": a.get("category", []),
                "published": a.get("published", ""),
            } for a in data["news"][:15]]
            return {
                "category": category,
                "language": language,
                "articles": articles,
                "news_count": len(articles),
                "mock": False,
            }

        return _mock_news("latest")
    except Exception:
        return _mock_news("latest")


async def brand_sentiment_news(params: dict) -> dict:
    """Search news specifically for brand/company sentiment analysis.

    Args:
        brand: Brand or company name (e.g., 'Tesla', 'Apple', 'Samsung')
        language: Language code (default: 'en')
    """
    brand = params.get("brand", "Tesla")
    language = params.get("language", "en")
    key = _get_key()

    if not key:
        return _mock_news(brand)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{CURRENTS_BASE}/search", params={
                "apiKey": key,
                "keywords": brand,
                "language": language,
            })
            data = resp.json()

        if data.get("news"):
            articles = []
            positive_keywords = ["growth", "profit", "gain", "surge", "record", "innovation", "expansion", "launch", "success"]
            negative_keywords = ["crisis", "recall", "loss", "decline", "lawsuit", "scandal", "shortage", "disruption", "bankruptcy"]

            for a in data["news"][:15]:
                text = f"{a.get('title', '')} {a.get('description', '')}".lower()
                pos_count = sum(1 for kw in positive_keywords if kw in text)
                neg_count = sum(1 for kw in negative_keywords if kw in text)

                if pos_count > neg_count:
                    sentiment = "positive"
                elif neg_count > pos_count:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                articles.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", "")[:200] if a.get("description") else "",
                    "url": a.get("url", ""),
                    "published": a.get("published", ""),
                    "sentiment": sentiment,
                    "category": a.get("category", []),
                })

            pos = sum(1 for a in articles if a["sentiment"] == "positive")
            neg = sum(1 for a in articles if a["sentiment"] == "negative")
            neu = sum(1 for a in articles if a["sentiment"] == "neutral")

            return {
                "brand": brand,
                "articles": articles,
                "sentiment_summary": {
                    "positive": pos,
                    "negative": neg,
                    "neutral": neu,
                    "sentiment_score": round((pos - neg) / max(len(articles), 1) * 100, 1),
                },
                "news_count": len(articles),
                "mock": False,
            }

        return _mock_news(brand)
    except Exception:
        return _mock_news(brand)


TOOLS = [
    {
        "name": "currents_news_search",
        "description": "Search news from 200+ sources via Currents API. Best for Market Intelligence and Brand agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"},
                "language": {"type": "string", "description": "Language code (en, zh, de, ja)", "default": "en"},
                "country": {"type": "string", "description": "Country code (US, CN, DE, JP)"},
                "domain": {"type": "string", "description": "Specific news domain (e.g., 'reuters.com')"}
            },
            "required": ["query"]
        },
        "handler": news_search,
        "cache_ttl": 1800,
    },
    {
        "name": "currents_latest_news",
        "description": "Get latest news headlines by category. Uses Currents API. Best for real-time monitoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Language code", "default": "en"},
                "category": {"type": "string", "description": "Category: business, technology, science, health, world, politics", "default": "business"},
                "country": {"type": "string", "description": "Country code"}
            }
        },
        "handler": latest_news,
        "cache_ttl": 600,
    },
    {
        "name": "currents_brand_sentiment",
        "description": "Analyze brand/company sentiment from news. Uses Currents API. Best for Brand Protector agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "Brand or company name (e.g., 'Tesla', 'Apple')"},
                "language": {"type": "string", "description": "Language code", "default": "en"}
            },
            "required": ["brand"]
        },
        "handler": brand_sentiment_news,
        "cache_ttl": 1800,
    },
]
