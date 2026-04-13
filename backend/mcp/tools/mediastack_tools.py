"""Mediastack MCP Tools — 435+ curated news feeds across 15 categories."""
import httpx
import os

MEDIASTACK_BASE = "http://api.mediastack.com/v1"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.mediastack_api_key or os.getenv("MEDIASTACK_API_KEY", "")
    except Exception:
        return os.getenv("MEDIASTACK_API_KEY", "")


def _mock_news(query: str) -> dict:
    return {
        "query": query,
        "articles": [
            {"title": f"Supply chain disruption: {query}", "source": "Reuters", "published_at": "2025-01-15T10:00:00Z", "category": "business", "country": "us", "mock": True},
            {"title": f"Global trade impact of {query}", "source": "Bloomberg", "published_at": "2025-01-15T08:30:00Z", "category": "business", "country": "us", "mock": True},
        ],
        "pagination": {"total": 2, "limit": 10, "offset": 0},
        "mock": True,
    }


async def news_search(params: dict) -> dict:
    """Search news articles from 435+ curated feeds via Mediastack.

    Args:
        query: Search keywords
        categories: Comma-separated categories (general, business, technology, science, health, sports, entertainment)
        countries: Comma-separated country codes (us, cn, de, jp, gb, in, tw, kr)
        limit: Max results (default: 10, max: 25 on free tier)
        languages: Comma-separated language codes (en, zh, de, ja)
    """
    query = params.get("query", "supply chain")
    categories = params.get("categories", "business,technology")
    countries = params.get("countries", "us,cn,de,jp")
    limit = min(params.get("limit", 10), 25)
    languages = params.get("languages", "en")
    key = _get_key()

    if not key:
        return _mock_news(query)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{MEDIASTACK_BASE}/news", params={
                "access_key": key,
                "keywords": query,
                "categories": categories,
                "countries": countries,
                "languages": languages,
                "limit": limit,
                "sort": "published_desc",
            })
            data = resp.json()

        if "data" in data and data["data"]:
            articles = [{
                "title": a.get("title", ""),
                "description": a.get("description", "")[:300] if a.get("description") else "",
                "url": a.get("url", ""),
                "source": a.get("source", ""),
                "published_at": a.get("published_at", ""),
                "category": a.get("category", ""),
                "country": a.get("country", ""),
                "language": a.get("language", ""),
            } for a in data["data"]]
            return {
                "query": query,
                "articles": articles,
                "pagination": data.get("pagination", {}),
                "mock": False,
            }

        if "error" in data:
            return {**_mock_news(query), "error": data["error"].get("message", "API error")}

        return _mock_news(query)
    except Exception:
        return _mock_news(query)


async def news_sources(params: dict) -> dict:
    """List available news sources from Mediastack.

    Args:
        categories: Filter by category
        countries: Filter by country
        limit: Max results (default: 20)
    """
    categories = params.get("categories", "business,technology")
    countries = params.get("countries", "")
    limit = min(params.get("limit", 20), 25)
    key = _get_key()

    if not key:
        return {"sources": [{"name": "Reuters", "category": "business", "country": "us", "mock": True}], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{MEDIASTACK_BASE}/sources", params={
                "access_key": key,
                "categories": categories,
                "countries": countries,
                "limit": limit,
            })
            data = resp.json()

        if "data" in data and data["data"]:
            sources = [{
                "name": s.get("name", ""),
                "category": s.get("category", ""),
                "country": s.get("country", ""),
                "language": s.get("language", ""),
                "url": s.get("homepage", ""),
            } for s in data["data"]]
            return {"sources": sources, "count": len(sources), "mock": False}

        return {"sources": [], "mock": True}
    except Exception:
        return {"sources": [], "mock": True}


async def historical_news(params: dict) -> dict:
    """Search historical news from Mediastack (requires paid plan, falls back to recent).

    Args:
        query: Search keywords
        date: Date or date range (YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD)
        categories: Categories filter
        limit: Max results
    """
    query = params.get("query", "supply chain")
    date = params.get("date", "2025-01-01,2025-01-15")
    categories = params.get("categories", "business")
    limit = min(params.get("limit", 10), 25)
    key = _get_key()

    if not key:
        return _mock_news(query)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{MEDIASTACK_BASE}/news", params={
                "access_key": key,
                "keywords": query,
                "date": date,
                "categories": categories,
                "limit": limit,
                "sort": "published_desc",
            })
            data = resp.json()

        if "data" in data and data["data"]:
            articles = [{
                "title": a.get("title", ""),
                "description": a.get("description", "")[:300] if a.get("description") else "",
                "url": a.get("url", ""),
                "source": a.get("source", ""),
                "published_at": a.get("published_at", ""),
            } for a in data["data"]]
            return {"query": query, "date": date, "articles": articles, "mock": False}

        return _mock_news(query)
    except Exception:
        return _mock_news(query)


TOOLS = [
    {
        "name": "mediastack_news_search",
        "description": "Search news from 435+ curated feeds across 15 categories. Uses Mediastack API. Best for Brand and Market agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"},
                "categories": {"type": "string", "description": "Categories: general,business,technology,science,health", "default": "business,technology"},
                "countries": {"type": "string", "description": "Country codes: us,cn,de,jp,gb,in,tw,kr", "default": "us,cn,de,jp"},
                "limit": {"type": "integer", "description": "Max results (max 25)", "default": 10},
                "languages": {"type": "string", "description": "Language codes: en,zh,de,ja", "default": "en"}
            },
            "required": ["query"]
        },
        "handler": news_search,
        "cache_ttl": 1800,
    },
    {
        "name": "mediastack_sources",
        "description": "List available news sources from Mediastack. Uses Mediastack API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categories": {"type": "string", "description": "Filter by category", "default": "business,technology"},
                "countries": {"type": "string", "description": "Filter by country code"},
                "limit": {"type": "integer", "description": "Max results", "default": 20}
            }
        },
        "handler": news_sources,
        "cache_ttl": 86400,
    },
    {
        "name": "mediastack_historical_news",
        "description": "Search historical news articles by date range. Uses Mediastack API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"},
                "date": {"type": "string", "description": "Date range: YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD", "default": "2025-01-01,2025-01-15"},
                "categories": {"type": "string", "description": "Categories filter", "default": "business"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        },
        "handler": historical_news,
        "cache_ttl": 86400,
    },
]
