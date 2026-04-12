from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _news_search(params: dict):
    query = params.get("query", "")
    date_range = params.get("date_range", "7d")

    # Try Firecrawl web_search first
    try:
        from backend.mcp.tools.firecrawl_tools import _web_search
        result = await _web_search({"query": query, "num_results": 10})
        if not result.get("mock"):
            articles = []
            for r in result.get("results", []):
                articles.append({
                    "title": r.get("title", ""),
                    "source": r.get("url", ""),
                    "description": r.get("content", "")[:300],
                    "url": r.get("url", ""),
                })
            return {"articles": articles, "query": query, "source": "firecrawl"}
    except Exception:
        pass

    # Try NewsAPI
    try:
        import os
        from newsapi import NewsApiClient
        api = NewsApiClient(api_key=os.environ.get("NEWSAPI_KEY", ""))
        articles = api.get_everything(q=query, language="en", sort_by="relevancy", page_size=10)
        return {"articles": articles.get("articles", []), "query": query}
    except Exception:
        return _mock_news(query)


def _mock_news(query: str) -> dict:
    return {
        "articles": [
            {"title": f"Supply chain update: {query}", "source": "MockNews", "description": f"Latest developments related to {query}"},
            {"title": f"Market analysis: {query} impact", "source": "MockAnalysis", "description": f"Analysis of {query} on global supply chains"},
        ],
        "query": query,
        "mock": True,
    }


async def _gdelt_query(params: dict):
    event_type = params.get("event_type", "conflict")
    country = params.get("country", "US")
    return {
        "events": [
            {"event_type": event_type, "country": country, "date": "2025-01-15", "severity": "medium", "source": "GDELT mock"},
        ],
        "mock": True,
    }


async def _supplier_financials(params: dict):
    supplier_name = params.get("supplier_name", "")
    return {
        "supplier": supplier_name,
        "financial_health": {
            "credit_rating": "BBB+",
            "revenue_trend": "stable",
            "debt_ratio": 0.35,
            "payment_reliability": 0.92,
        },
        "mock": True,
    }


def register():
    register_tool(
        name="news_search",
        description="Search news articles related to supply chain topics",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "date_range": {"type": "string", "description": "Date range (e.g., 7d, 30d)", "default": "7d"},
            },
            "required": ["query"],
        },
        handler=_news_search,
        category="news",
        cache_ttl=300,
    )
    register_tool(
        name="gdelt_query",
        description="Query GDELT event database for geopolitical events",
        input_schema={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Event type filter"},
                "country": {"type": "string", "description": "Country code", "default": "US"},
            },
            "required": ["event_type"],
        },
        handler=_gdelt_query,
        category="news",
        cache_ttl=600,
    )
    register_tool(
        name="supplier_financials",
        description="Get financial health data for a supplier",
        input_schema={
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string", "description": "Supplier name"},
            },
            "required": ["supplier_name"],
        },
        handler=_supplier_financials,
        category="news",
        cache_ttl=3600,
    )
