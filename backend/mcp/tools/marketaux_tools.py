"""MarketAux MCP Tools — Financial news with market sentiment and tickers."""
import httpx
import os

MARKETAUX_BASE = "https://api.marketaux.com/v1"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.marketaux_api_key or os.getenv("MARKETAUX_API_KEY", "")
    except Exception:
        return os.getenv("MARKETAUX_API_KEY", "")


def _mock_news(query: str) -> dict:
    return {"query": query, "articles": [], "mock": True}


async def news_with_tickers(params: dict) -> dict:
    """Get financial news filtered by stock tickers from MarketAux.

    Args:
        symbols: Comma-separated tickers (e.g., 'AAPL,TSM')
        limit: Max articles (default: 5)
    """
    symbols = params.get("symbols", "AAPL")
    limit = params.get("limit", 5)
    key = _get_key()

    if not key:
        return _mock_news(symbols)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKETAUX_BASE}/news/all", params={
                "symbols": symbols, "limit": limit, "api_token": key,
            })
            data = resp.json()

        articles = data.get("data", [])
        if articles:
            results = []
            for a in articles[:limit]:
                entities = a.get("entities", [])
                tickers = [e.get("symbol", "") for e in entities if e.get("symbol")]
                sentiment = {}
                for e in entities:
                    if e.get("sentiment_score"):
                        sentiment[e.get("symbol", "")] = e["sentiment_score"]
                results.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "source": a.get("source", ""),
                    "published_at": a.get("published_at", ""),
                    "tickers": tickers,
                    "sentiment": sentiment,
                })
            return {"symbols": symbols, "articles": results, "count": len(results), "mock": False}

        return _mock_news(symbols)
    except Exception:
        return _mock_news(symbols)


async def market_sentiment(params: dict) -> dict:
    """Get aggregated market sentiment for tickers from MarketAux.

    Args:
        symbols: Comma-separated tickers
    """
    symbols = params.get("symbols", "AAPL,MSFT,GOOGL")
    key = _get_key()

    if not key:
        return {"symbols": symbols, "sentiment": {}, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKETAUX_BASE}/news/sentiment", params={
                "symbols": symbols, "api_token": key,
            })
            data = resp.json()

        if data.get("data"):
            sentiment = {}
            for sym, info in data["data"].items():
                sentiment[sym] = {
                    "sentiment_score": info.get("sentiment", 0),
                    "articles_count": info.get("articles_count", 0),
                }
            return {"symbols": symbols, "sentiment": sentiment, "mock": False}

        return {"symbols": symbols, "sentiment": {}, "mock": True}
    except Exception:
        return {"symbols": symbols, "sentiment": {}, "mock": True}


async def trending_tickers(params: dict) -> dict:
    """Get trending financial news (most mentioned tickers) from MarketAux."""
    key = _get_key()

    if not key:
        return {"tickers": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MARKETAUX_BASE}/news/all", params={
                "api_token": key, "limit": 10, "sort": "hot",
            })
            data = resp.json()

        articles = data.get("data", [])
        if articles:
            # Extract trending tickers from articles
            ticker_counts = {}
            for a in articles:
                for e in a.get("entities", []):
                    sym = e.get("symbol", "")
                    if sym:
                        ticker_counts[sym] = ticker_counts.get(sym, 0) + 1
            tickers = [{"symbol": s, "mentions": c} for s, c in sorted(ticker_counts.items(), key=lambda x: -x[1])[:10]]
            return {"tickers": tickers, "article_count": len(articles), "mock": False}

        return {"tickers": [], "mock": True}
    except Exception:
        return {"tickers": [], "mock": True}


TOOLS = [
    {
        "name": "marketaux_news",
        "description": "Get financial news filtered by tickers with sentiment. Uses MarketAux API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "string", "description": "Comma-separated tickers (e.g., 'AAPL,TSM')"},
                "limit": {"type": "integer", "description": "Max articles", "default": 5}
            },
            "required": ["symbols"]
        },
        "handler": news_with_tickers,
        "cache_ttl": 600,
    },
    {
        "name": "marketaux_sentiment",
        "description": "Get market sentiment scores for tickers. Uses MarketAux API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "string", "description": "Comma-separated tickers", "default": "AAPL,MSFT,GOOGL"}
            },
            "required": []
        },
        "handler": market_sentiment,
        "cache_ttl": 1800,
    },
    {
        "name": "marketaux_trending",
        "description": "Get trending/most mentioned tickers. Uses MarketAux API.",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "handler": trending_tickers,
        "cache_ttl": 600,
    },
]
