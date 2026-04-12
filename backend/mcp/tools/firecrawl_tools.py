from backend.mcp.registry import register_tool
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

_firecrawl_client = None


def _get_client():
    global _firecrawl_client
    if _firecrawl_client is not None:
        return _firecrawl_client

    if not settings.firecrawl_api_key:
        return None

    try:
        from firecrawl import FirecrawlApp
        _firecrawl_client = FirecrawlApp(api_key=settings.firecrawl_api_key)
        logger.info("Firecrawl client initialized")
        return _firecrawl_client
    except ImportError:
        logger.warning("firecrawl-py not installed — web tools will use mock fallbacks")
        return None
    except Exception as e:
        logger.warning(f"Firecrawl init failed: {e}")
        return None


async def _web_scrape(params: dict):
    url = params.get("url", "")
    formats = params.get("formats", ["markdown"])
    client = _get_client()

    if not client:
        return _mock_scrape(url)

    try:
        result = client.scrape_url(url, params={"formats": formats})
        content = result.get("markdown", result.get("html", result.get("content", "")))
        metadata = result.get("metadata", {})
        return {"content": content, "metadata": metadata, "url": url}
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return _mock_scrape(url, error=str(e))


def _mock_scrape(url: str, error: str = "") -> dict:
    return {
        "content": f"[Mock scrape] Content from {url}",
        "metadata": {"url": url, "mock": True},
        "url": url,
        "mock": True,
        "error": error or None,
    }


async def _web_crawl(params: dict):
    url = params.get("url", "")
    max_depth = params.get("max_depth", 2)
    max_pages = params.get("max_pages", 10)
    client = _get_client()

    if not client:
        return _mock_crawl(url, max_pages)

    try:
        results = client.crawl_url(url, params={"maxDepth": max_depth, "limit": max_pages})
        pages = []
        for doc in results.get("data", []):
            pages.append({
                "url": doc.get("metadata", {}).get("sourceURL", doc.get("metadata", {}).get("url", "")),
                "content": doc.get("markdown", doc.get("content", "")),
                "metadata": doc.get("metadata", {}),
            })
        return {"pages": pages, "total_pages": len(pages), "url": url}
    except Exception as e:
        logger.error(f"Firecrawl crawl failed: {e}")
        return _mock_crawl(url, max_pages, error=str(e))


def _mock_crawl(url: str, max_pages: int, error: str = "") -> dict:
    return {
        "pages": [
            {"url": f"{url}/page/{i}", "content": f"[Mock crawl] Page {i} from {url}", "metadata": {"mock": True}}
            for i in range(min(max_pages, 3))
        ],
        "total_pages": min(max_pages, 3),
        "url": url,
        "mock": True,
        "error": error or None,
    }


async def _web_search(params: dict):
    query = params.get("query", "")
    num_results = params.get("num_results", 5)
    client = _get_client()

    if not client:
        return _mock_search(query, num_results)

    try:
        results = client.search(query, params={"limit": num_results})
        items = []
        for doc in results.get("data", []):
            items.append({
                "url": doc.get("metadata", {}).get("sourceURL", doc.get("metadata", {}).get("url", "")),
                "title": doc.get("metadata", {}).get("title", ""),
                "content": doc.get("markdown", doc.get("content", "")),
            })
        return {"results": items, "query": query}
    except Exception as e:
        logger.error(f"Firecrawl search failed: {e}")
        return _mock_search(query, num_results, error=str(e))


def _mock_search(query: str, num_results: int, error: str = "") -> dict:
    return {
        "results": [
            {"url": f"https://example.com/result/{i}", "title": f"Result {i} for {query}",
             "content": f"[Mock search] Content about {query} - result {i}"}
            for i in range(min(num_results, 3))
        ],
        "query": query,
        "mock": True,
        "error": error or None,
    }


def register():
    register_tool(
        name="web_scrape",
        description="Scrape a single URL and return clean markdown content using Firecrawl",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to scrape"},
                "formats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Output formats",
                    "default": ["markdown"],
                },
            },
            "required": ["url"],
        },
        handler=_web_scrape,
        category="firecrawl",
        cache_ttl=3600,
    )
    register_tool(
        name="web_crawl",
        description="Crawl a website with depth/page limits using Firecrawl",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Root URL to crawl"},
                "max_depth": {"type": "integer", "description": "Max crawl depth", "default": 2},
                "max_pages": {"type": "integer", "description": "Max pages to crawl", "default": 10},
            },
            "required": ["url"],
        },
        handler=_web_crawl,
        category="firecrawl",
        cache_ttl=86400,
    )
    register_tool(
        name="web_search",
        description="Search the web and return scraped results using Firecrawl",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        },
        handler=_web_search,
        category="firecrawl",
        cache_ttl=1800,
    )
