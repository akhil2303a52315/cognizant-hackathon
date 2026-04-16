"""Knowledge Platform MCP Tools — Wikipedia, Arxiv, World Bank, Reddit. No API keys needed (except Reddit optional)."""
import httpx
import os
import xml.etree.ElementTree as ET

WIKI_REST = "https://en.wikipedia.org/api/rest_v1"
WIKI_MW = "https://en.wikipedia.org/w/api.php"
ARXIV_BASE = "https://export.arxiv.org/api/query"
WORLDBANK_BASE = "https://api.worldbank.org/v2"
REDDIT_BASE = "https://www.reddit.com"


def _mock_reddit_sentiment(subreddit: str) -> dict:
    return {
        "subreddit": subreddit,
        "posts": [
            {"title": f"Supply chain disruption discussed in r/{subreddit}", "score": 42, "num_comments": 15, "mock": True},
            {"title": "Logistics challenges in 2024", "score": 28, "num_comments": 8, "mock": True},
            {"title": "New trade regulations impact", "score": 19, "num_comments": 5, "mock": True},
        ],
        "total": 3,
        "mock": True
    }


async def wikipedia_search(params: dict) -> dict:
    """Search Wikipedia for articles. No API key needed.
    
    Args:
        query: Search query
        limit: Max results (default: 5)
    """
    query = params.get("query", "supply chain")
    limit = params.get("limit", 5)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(WIKI_MW, params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "format": "json",
                "origin": "*"
            }, headers={"User-Agent": "SupplyChainGPT/1.0 (research@supplychaingpt.ai)"})
            data = resp.json()

        search_results = data.get("query", {}).get("search", [])
        results = [{
            "title": s.get("title", ""),
            "snippet": s.get("snippet", "")[:200].replace('<span class="searchmatch">', '').replace('</span>', ''),
            "url": f"https://en.wikipedia.org/wiki/{s.get('title', '').replace(' ', '_')}",
            "wordcount": s.get("wordcount", 0),
        } for s in search_results]

        return {"query": query, "results": results, "mock": False}
    except Exception:
        return {"query": query, "results": [{"title": f"Wikipedia: {query}", "mock": True}], "mock": True}


async def wikipedia_summary(params: dict) -> dict:
    """Get Wikipedia article summary. No API key needed.
    
    Args:
        title: Article title (e.g., 'TSMC', 'Supply_chain_management')
    """
    title = params.get("title", "Supply_chain_management")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(WIKI_MW, params={
                "action": "query",
                "titles": title,
                "prop": "extracts|info",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "format": "json",
                "origin": "*"
            }, headers={"User-Agent": "SupplyChainGPT/1.0 (research@supplychaingpt.ai)"})
            data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values())) if pages else {}
        
        return {
            "title": page.get("title", title),
            "extract": page.get("extract", ""),
            "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
            "pageid": page.get("pageid", 0),
            "mock": False
        }
    except Exception:
        return {"title": title, "extract": f"Summary for {title} unavailable.", "mock": True}


async def arxiv_search(params: dict) -> dict:
    """Search Arxiv for research papers. No API key needed.
    
    Args:
        query: Search query (e.g., 'supply chain risk management')
        max_results: Max papers (default: 5)
    """
    query = params.get("query", "supply chain risk")
    max_results = params.get("max_results", 5)

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(ARXIV_BASE, params={
                "search_query": f"all:{query}",
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            })
            root = ET.fromstring(resp.text)

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            papers.append({
                "title": entry.findtext("atom:title", "", ns).strip().replace("\n", " "),
                "summary": entry.findtext("atom:summary", "", ns).strip()[:300],
                "published": entry.findtext("atom:published", "", ns),
                "link": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else "",
                "authors": [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)],
            })

        return {"query": query, "papers": papers, "total": len(papers), "mock": False}
    except Exception:
        return {"query": query, "papers": [], "mock": True}


async def worldbank_indicator(params: dict) -> dict:
    """Get World Bank country indicator data. No API key needed.
    
    Args:
        country: Country code (e.g., 'US', 'CN', 'TW', 'JP')
        indicator: World Bank indicator code (e.g., 'NY.GDP.MKTP.CD' for GDP, 'NE.TRD.GNFS.ZS' for trade % GDP)
        years: Number of recent years (default: 5)
    """
    country = params.get("country", "US")
    indicator = params.get("indicator", "NY.GDP.MKTP.CD")
    years = params.get("years", 5)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(f"{WORLDBANK_BASE}/country/{country}/indicator/{indicator}", params={
                "format": "json",
                "per_page": years,
                "date": f"2019:2024"
            })
            data = resp.json()

        if len(data) < 2:
            return {"country": country, "indicator": indicator, "values": [], "mock": True}

        records = data[1] or []
        values = [{
            "date": r.get("date", ""),
            "value": r.get("value"),
            "indicator_name": r.get("indicator", {}).get("value", ""),
        } for r in records if r.get("value") is not None]

        return {"country": country, "indicator": indicator, "values": values, "mock": False}
    except Exception:
        return {"country": country, "indicator": indicator, "values": [], "mock": True}


async def reddit_sentiment(params: dict) -> dict:
    """Get Reddit posts for sentiment analysis. No API key needed (uses public JSON).
    
    Args:
        subreddit: Subreddit name (e.g., 'supplychain', 'logistics')
        limit: Max posts (default: 10)
        sort: Sort order ('hot', 'new', 'top')
    """
    subreddit = params.get("subreddit", "supplychain")
    limit = params.get("limit", 10)
    sort = params.get("sort", "hot")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(f"https://old.reddit.com/r/{subreddit}/{sort}.json", params={
                "limit": limit,
                "raw_json": 1
            }, headers={"User-Agent": "SupplyChainGPT/1.0 (research@supplychaingpt.ai)"})
            if resp.status_code != 200:
                return _mock_reddit_sentiment(subreddit)
            data = resp.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            posts.append({
                "title": d.get("title", ""),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "author": d.get("author", ""),
                "created_utc": d.get("created_utc", 0),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "selftext": d.get("selftext", "")[:200],
            })

        return {"subreddit": subreddit, "posts": posts, "total": len(posts), "mock": False}
    except Exception:
        return {"subreddit": subreddit, "posts": [], "mock": True}


async def oecd_data(params: dict) -> dict:
    """Get OECD data. No API key needed.
    
    Args:
        dataset: OECD dataset code (e.g., 'MEI' for Main Economic Indicators)
        filter: Filter string (e.g., 'USA+CHN.TS.GP.A')
    """
    dataset = params.get("dataset", "MEI")
    filter_str = params.get("filter", "")

    try:
        url = f"https://data.oecd.org/api/sdmx/JSON/data/{dataset}"
        if filter_str:
            url += f"/{filter_str}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        return {"dataset": dataset, "data": data, "mock": False}
    except Exception:
        return {"dataset": dataset, "data": {}, "mock": True}


TOOLS = [
    {
        "name": "wikipedia_search",
        "description": "Search Wikipedia for articles about companies, countries, supply chain topics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default: 5)", "default": 5}
            },
            "required": ["query"]
        },
        "handler": wikipedia_search,
        "cache_ttl": 86400,
    },
    {
        "name": "wikipedia_summary",
        "description": "Get Wikipedia article summary. Useful for supplier company profiles and country risk context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Article title (e.g., 'Taiwan_Semiconductor_Manufacturing')"}
            },
            "required": ["title"]
        },
        "handler": wikipedia_summary,
        "cache_ttl": 86400,
    },
    {
        "name": "arxiv_search",
        "description": "Search Arxiv for supply chain research papers. Good for RAG grounding and academic citations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max papers (default: 5)", "default": 5}
            },
            "required": ["query"]
        },
        "handler": arxiv_search,
        "cache_ttl": 86400,
    },
    {
        "name": "worldbank_indicator",
        "description": "Get World Bank country indicators (GDP, trade %, governance). No API key needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Country code (e.g., 'US', 'CN', 'TW')", "default": "US"},
                "indicator": {"type": "string", "description": "Indicator code (e.g., 'NY.GDP.MKTP.CD' for GDP)", "default": "NY.GDP.MKTP.CD"},
                "years": {"type": "integer", "description": "Recent years (default: 5)", "default": 5}
            }
        },
        "handler": worldbank_indicator,
        "cache_ttl": 86400,
    },
    {
        "name": "reddit_sentiment",
        "description": "Get Reddit posts for sentiment analysis from supply chain subreddits. No API key needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subreddit": {"type": "string", "description": "Subreddit (e.g., 'supplychain', 'logistics')", "default": "supplychain"},
                "limit": {"type": "integer", "description": "Max posts (default: 10)", "default": 10},
                "sort": {"type": "string", "description": "Sort: 'hot', 'new', 'top'", "default": "hot"}
            }
        },
        "handler": reddit_sentiment,
        "cache_ttl": 1800,
    },
    {
        "name": "oecd_data",
        "description": "Get OECD economic and trade data. No API key needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string", "description": "OECD dataset code", "default": "MEI"},
                "filter": {"type": "string", "description": "Filter string (e.g., 'USA+CHN.TS.GP.A')"}
            }
        },
        "handler": oecd_data,
        "cache_ttl": 86400,
    },
]
