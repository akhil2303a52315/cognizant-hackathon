from backend.mcp.registry import register_tool
from backend.config import settings
import logging
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firecrawl client — supports both cloud API and self-hosted instance
# ---------------------------------------------------------------------------

def _get_base_url() -> str:
    """Return Firecrawl API base URL (self-hosted or cloud)."""
    if settings.firecrawl_base_url:
        return settings.firecrawl_base_url.rstrip("/")
    return "https://api.firecrawl.dev/v1"


def _get_headers() -> dict:
    """Return auth headers for Firecrawl API."""
    key = settings.firecrawl_api_key
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _is_configured() -> bool:
    return bool(settings.firecrawl_api_key or settings.firecrawl_base_url)


# ---------------------------------------------------------------------------
# Core Firecrawl operations via REST API (works with both cloud & self-hosted)
# ---------------------------------------------------------------------------

async def _fc_scrape(url: str, formats: list = None) -> dict:
    """Scrape a single URL via Firecrawl REST API."""
    base = _get_base_url()
    headers = _get_headers()
    payload = {"url": url, "formats": formats or ["markdown"]}

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.post(f"{base}/scrape", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def _fc_crawl(url: str, max_depth: int = 2, limit: int = 10) -> dict:
    """Crawl a website via Firecrawl REST API."""
    base = _get_base_url()
    headers = _get_headers()
    payload = {"url": url, "maxDepth": max_depth, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}}

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        r = await client.post(f"{base}/crawl", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def _fc_search(query: str, limit: int = 5) -> dict:
    """Search the web via Firecrawl REST API."""
    base = _get_base_url()
    headers = _get_headers()
    payload = {"query": query, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}}

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.post(f"{base}/search", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def _fc_extract(url: str, schema: dict = None) -> dict:
    """Extract structured data from a URL using Firecrawl extract endpoint."""
    base = _get_base_url()
    headers = _get_headers()
    payload = {"urls": [url]}
    if schema:
        payload["schema"] = schema

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.post(f"{base}/extract", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# MCP Tool Handlers
# ---------------------------------------------------------------------------

async def _web_scrape(params: dict):
    url = params.get("url", "")
    formats = params.get("formats", ["markdown"])

    if not _is_configured():
        return _mock_scrape(url)

    try:
        result = await _fc_scrape(url, formats)
        data = result.get("data", result)
        content = data.get("markdown", data.get("html", data.get("content", "")))
        metadata = data.get("metadata", {})
        return {"content": content, "metadata": metadata, "url": url}
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return _mock_scrape(url, error=str(e))


async def _web_crawl(params: dict):
    url = params.get("url", "")
    max_depth = params.get("max_depth", 2)
    max_pages = params.get("max_pages", 10)

    if not _is_configured():
        return _mock_crawl(url, max_pages)

    try:
        result = await _fc_crawl(url, max_depth, max_pages)
        pages = []
        for doc in result.get("data", []):
            meta = doc.get("metadata", {})
            pages.append({
                "url": meta.get("sourceURL", meta.get("url", "")),
                "content": doc.get("markdown", doc.get("content", "")),
                "metadata": meta,
            })
        return {"pages": pages, "total_pages": len(pages), "url": url}
    except Exception as e:
        logger.error(f"Firecrawl crawl failed: {e}")
        return _mock_crawl(url, max_pages, error=str(e))


async def _web_search(params: dict):
    query = params.get("query", "")
    num_results = params.get("num_results", 5)

    if not _is_configured():
        return _mock_search(query, num_results)

    try:
        result = await _fc_search(query, num_results)
        items = []
        for doc in result.get("data", []):
            meta = doc.get("metadata", {})
            items.append({
                "url": meta.get("sourceURL", meta.get("url", "")),
                "title": meta.get("title", ""),
                "content": doc.get("markdown", doc.get("content", "")),
            })
        return {"results": items, "query": query}
    except Exception as e:
        logger.error(f"Firecrawl search failed: {e}")
        return _mock_search(query, num_results, error=str(e))


async def _web_extract_data(params: dict):
    """Extract structured data from a URL using a JSON schema."""
    url = params.get("url", "")
    schema = params.get("schema", None)

    if not _is_configured():
        return _mock_extract(url)

    try:
        result = await _fc_extract(url, schema)
        data = result.get("data", result)
        return {"extracted": data, "url": url}
    except Exception as e:
        logger.error(f"Firecrawl extract failed: {e}")
        return _mock_extract(url, error=str(e))


async def _web_scrape_supplier(params: dict):
    """Scrape a supplier website for capability and certification data."""
    url = params.get("url", "")
    extract_fields = params.get("extract_fields", ["company_name", "certifications", "capabilities", "products", "contact"])

    if not _is_configured():
        return _mock_supplier(url)

    try:
        # Build a simple schema for supplier data extraction
        schema = {
            "type": "object",
            "properties": {field: {"type": "string"} for field in extract_fields},
        }
        result = await _fc_extract(url, schema)
        data = result.get("data", result)
        # Also get full markdown content
        scrape_result = await _fc_scrape(url, ["markdown"])
        content = scrape_result.get("data", {}).get("markdown", "")
        return {"extracted": data, "content": content, "url": url}
    except Exception as e:
        logger.error(f"Firecrawl supplier scrape failed: {e}")
        return _mock_supplier(url, error=str(e))


async def _web_scrape_news(params: dict):
    """Scrape a news article URL for full content and metadata."""
    url = params.get("url", "")

    if not _is_configured():
        return _mock_news(url)

    try:
        result = await _fc_scrape(url, ["markdown"])
        data = result.get("data", result)
        content = data.get("markdown", data.get("content", ""))
        metadata = data.get("metadata", {})
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "published_date": metadata.get("publishedTime", metadata.get("date", "")),
            "content": content,
            "url": url,
        }
    except Exception as e:
        logger.error(f"Firecrawl news scrape failed: {e}")
        return _mock_news(url, error=str(e))


# ---------------------------------------------------------------------------
# Mock fallbacks
# ---------------------------------------------------------------------------

def _mock_scrape(url: str, error: str = "") -> dict:
    return {"content": f"[Mock scrape] Content from {url}", "metadata": {"url": url, "mock": True}, "url": url, "mock": True, "error": error or None}

def _mock_crawl(url: str, max_pages: int, error: str = "") -> dict:
    return {"pages": [{"url": f"{url}/page/{i}", "content": f"[Mock crawl] Page {i} from {url}", "metadata": {"mock": True}} for i in range(min(max_pages, 3))], "total_pages": min(max_pages, 3), "url": url, "mock": True, "error": error or None}

def _mock_search(query: str, num_results: int, error: str = "") -> dict:
    return {"results": [{"url": f"https://example.com/result/{i}", "title": f"Result {i} for {query}", "content": f"[Mock search] Content about {query} - result {i}"} for i in range(min(num_results, 3))], "query": query, "mock": True, "error": error or None}

def _mock_extract(url: str, error: str = "") -> dict:
    return {"extracted": {"company_name": "Mock Corp", "certifications": "ISO 9001, ISO 14001", "capabilities": "Manufacturing, Assembly"}, "url": url, "mock": True, "error": error or None}

def _mock_supplier(url: str, error: str = "") -> dict:
    return {"extracted": {"company_name": "Mock Supplier Inc", "certifications": "ISO 9001, IATF 16949", "capabilities": "Precision machining, Surface treatment", "products": "Automotive components, Electronic housings", "contact": "sales@mocksupplier.com"}, "content": f"[Mock supplier] Full page content from {url}", "url": url, "mock": True, "error": error or None}

def _mock_news(url: str, error: str = "") -> dict:
    return {"title": "Mock News Article", "author": "Mock Reporter", "published_date": "2026-04-13", "content": f"[Mock news] Full article content from {url}", "url": url, "mock": True, "error": error or None}


# ---------------------------------------------------------------------------
# Tool Registration
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "web_scrape",
        "description": "Scrape a single URL and return clean markdown content using Firecrawl (self-hosted or cloud)",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to scrape"},
                "formats": {"type": "array", "items": {"type": "string"}, "description": "Output formats (markdown, html, rawHtml)", "default": ["markdown"]},
            },
            "required": ["url"],
        },
        "handler": _web_scrape,
        "category": "firecrawl",
        "cache_ttl": 3600,
    },
    {
        "name": "web_crawl",
        "description": "Crawl a website with depth/page limits using Firecrawl — returns all pages as markdown",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Root URL to crawl"},
                "max_depth": {"type": "integer", "description": "Max crawl depth", "default": 2},
                "max_pages": {"type": "integer", "description": "Max pages to crawl", "default": 10},
            },
            "required": ["url"],
        },
        "handler": _web_crawl,
        "category": "firecrawl",
        "cache_ttl": 86400,
    },
    {
        "name": "web_search",
        "description": "Search the web and return scraped results using Firecrawl — returns URLs + content",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        },
        "handler": _web_search,
        "category": "firecrawl",
        "cache_ttl": 1800,
    },
    {
        "name": "web_extract_data",
        "description": "Extract structured JSON data from a URL using a schema — ideal for supplier portals, product pages, regulatory docs",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to extract data from"},
                "schema": {"type": "object", "description": "JSON schema defining fields to extract (optional)", "default": None},
            },
            "required": ["url"],
        },
        "handler": _web_extract_data,
        "category": "firecrawl",
        "cache_ttl": 3600,
    },
    {
        "name": "web_scrape_supplier",
        "description": "Scrape a supplier website and extract structured capability data — certifications, products, contact info, capabilities",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Supplier website URL"},
                "extract_fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to extract", "default": ["company_name", "certifications", "capabilities", "products", "contact"]},
            },
            "required": ["url"],
        },
        "handler": _web_scrape_supplier,
        "category": "firecrawl",
        "cache_ttl": 86400,
    },
    {
        "name": "web_scrape_news",
        "description": "Scrape a news article URL and extract full content with title, author, date — for Brand and Risk agents",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "News article URL to scrape"},
            },
            "required": ["url"],
        },
        "handler": _web_scrape_news,
        "category": "firecrawl",
        "cache_ttl": 1800,
    },
]


def register():
    """Register Firecrawl tools using the legacy register() pattern."""
    for t in TOOLS:
        register_tool(
            name=t["name"],
            description=t["description"],
            input_schema=t["input_schema"],
            handler=t["handler"],
            category=t["category"],
            cache_ttl=t.get("cache_ttl", 3600),
        )
