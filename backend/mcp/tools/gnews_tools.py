"""GNews MCP Tools — Alternative news search, breaking news, topic headlines."""
import httpx
import os

GNEWS_BASE = "https://gnews.io/api/v4"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.gnews_api_key or os.getenv("GNEWS_API_KEY", "")
    except Exception:
        return os.getenv("GNEWS_API_KEY", "")


def _mock_news(query: str) -> dict:
    return {"query": query, "articles": [], "article_count": 0, "mock": True}


async def search_news(params: dict) -> dict:
    """Search news articles from GNews.

    Args:
        query: Search query (e.g., 'supply chain disruption')
        max_results: Max articles (default: 5)
        lang: Language code (default: 'en')
    """
    query = params.get("query", "supply chain")
    max_results = params.get("max_results", 5)
    lang = params.get("lang", "en")
    key = _get_key()

    if not key:
        return _mock_news(query)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GNEWS_BASE}/search", params={
                "q": query, "max": max_results, "lang": lang, "apikey": key,
            })
            data = resp.json()

        articles = data.get("articles", [])
        if articles:
            results = [{
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", ""),
            } for a in articles[:max_results]]
            return {"query": query, "articles": results, "article_count": len(results), "mock": False}

        return _mock_news(query)
    except Exception:
        return _mock_news(query)


async def top_headlines(params: dict) -> dict:
    """Get top headlines from GNews by category.

    Args:
        category: Category (general, world, nation, business, technology, entertainment, sports, science, health)
        max_results: Max articles (default: 5)
    """
    category = params.get("category", "business")
    max_results = params.get("max_results", 5)
    key = _get_key()

    if not key:
        return {"category": category, "articles": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GNEWS_BASE}/top-headlines", params={
                "category": category, "max": max_results, "apikey": key,
            })
            data = resp.json()

        articles = data.get("articles", [])
        if articles:
            results = [{
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", ""),
            } for a in articles[:max_results]]
            return {"category": category, "articles": results, "article_count": len(results), "mock": False}

        return {"category": category, "articles": [], "mock": True}
    except Exception:
        return {"category": category, "articles": [], "mock": True}


TOOLS = [
    {
        "name": "gnews_search",
        "description": "Search news articles. Uses GNews API. Good alternative to NewsAPI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max articles", "default": 5},
                "lang": {"type": "string", "description": "Language code", "default": "en"}
            },
            "required": ["query"]
        },
        "handler": search_news,
        "cache_ttl": 600,
    },
    {
        "name": "gnews_top_headlines",
        "description": "Get top headlines by category. Uses GNews API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: general,business,technology,science,health", "default": "business"},
                "max_results": {"type": "integer", "description": "Max articles", "default": 5}
            },
            "required": []
        },
        "handler": top_headlines,
        "cache_ttl": 600,
    },
]
