"""GDELT Real-Time Geopolitical Events MCP Tools — No API key needed."""
import httpx
import os
from datetime import datetime, timedelta

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"


def _mock_gdelt_events(query: str) -> dict:
    return {
        "query": query,
        "events": [
            {"title": f"Supply chain disruption reported in {query}", "url": "https://example.com/1",
             "date": datetime.utcnow().strftime("%Y-%m-%d"), "tone": -3.2, "country": "CN", "themes": "supply_chain,trade"},
            {"title": f"Geopolitical tension affecting {query}", "url": "https://example.com/2",
             "date": datetime.utcnow().strftime("%Y-%m-%d"), "tone": -5.1, "country": "TW", "themes": "semiconductor,geopolitics"},
            {"title": f"Trade policy changes impacting {query}", "url": "https://example.com/3",
             "date": datetime.utcnow().strftime("%Y-%m-%d"), "tone": -1.8, "country": "US", "themes": "tariff,trade_policy"},
        ],
        "total": 3,
        "mock": True
    }


def _mock_gdelt_tone(query: str) -> dict:
    return {
        "query": query,
        "avg_tone": -3.4,
        "tone_distribution": {"very_negative": 15, "negative": 35, "neutral": 30, "positive": 15, "very_positive": 5},
        "trend": "deteriorating",
        "mock": True
    }


async def gdelt_events(params: dict) -> dict:
    """Search GDELT for real-time geopolitical events related to supply chain.
    
    Args:
        query: Search query (e.g., 'semiconductor Taiwan', 'supply chain disruption')
        max_records: Maximum number of records to return (default: 10)
        tone_threshold: Minimum tone filter (negative = bad news, default: -10)
    """
    query = params.get("query", "supply chain")
    max_records = params.get("max_records", 10)
    tone_threshold = params.get("tone_threshold", -10)

    try:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d%H%M%S")
        end_date = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        url = f"{GDELT_BASE}?query={query}&mode=artlist&maxrecords={max_records}&format=json&startdatetime={start_date}&enddatetime={end_date}&toneabs={abs(tone_threshold)}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 429:
                return _mock_gdelt_events(query)
            data = resp.json()

        articles = data.get("articles", [])
        events = []
        for a in articles[:max_records]:
            events.append({
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "date": a.get("seendate", ""),
                "tone": float(a.get("tone", 0)),
                "country": a.get("sourcecountry", ""),
                "themes": a.get("themes", ""),
                "language": a.get("language", ""),
            })

        return {"query": query, "events": events, "total": len(events), "mock": False}

    except Exception:
        return _mock_gdelt_events(query)


async def gdelt_tone(params: dict) -> dict:
    """Get GDELT tone analysis for a topic (sentiment over time).
    
    Args:
        query: Search query for tone analysis
        days: Number of days to analyze (default: 30)
    """
    query = params.get("query", "supply chain")
    days = params.get("days", 30)

    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y%m%d%H%M%S")
        end_date = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        url = f"{GDELT_BASE}?query={query}&mode=tonechart&format=json&startdatetime={start_date}&enddatetime={end_date}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 429:
                return _mock_gdelt_tone(query)
            data = resp.json()

        tone_data = data.get("tonechart", [])
        if tone_data:
            bins = tone_data[0].get("bins", []) if tone_data else []
            avg_tone = sum(float(b.get("key", 0)) * int(b.get("count", 0)) for b in bins) / max(sum(int(b.get("count", 0)) for b in bins), 1)
        else:
            avg_tone = 0

        return {
            "query": query,
            "avg_tone": round(avg_tone, 2),
            "days_analyzed": days,
            "raw_bins": tone_data[0].get("bins", [])[:10] if tone_data else [],
            "mock": False
        }

    except Exception:
        return _mock_gdelt_tone(query)


TOOLS = [
    {
        "name": "gdelt_events",
        "description": "Search GDELT for real-time geopolitical events affecting supply chains. Returns articles with tone, country, themes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g., 'semiconductor Taiwan')"},
                "max_records": {"type": "integer", "description": "Max results (default: 10)", "default": 10},
                "tone_threshold": {"type": "number", "description": "Tone filter threshold (default: -10)", "default": -10}
            },
            "required": ["query"]
        },
        "handler": gdelt_events,
        "cache_ttl": 1800,
    },
    {
        "name": "gdelt_tone",
        "description": "Analyze GDELT tone/sentiment for a topic over time. Returns average tone and distribution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic to analyze"},
                "days": {"type": "integer", "description": "Days to analyze (default: 30)", "default": 30}
            },
            "required": ["query"]
        },
        "handler": gdelt_tone,
        "cache_ttl": 3600,
    },
]
