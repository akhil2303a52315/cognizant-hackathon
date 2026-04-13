"""Shodan MCP Tools — IoT device search, industrial control system monitoring, exploit DB."""
import httpx
import os

SHODAN_BASE = "https://api.shodan.io"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.shodan_api_key or os.getenv("SHODAN_API_KEY", "")
    except Exception:
        return os.getenv("SHODAN_API_KEY", "")


def _mock_device_search(query: str) -> dict:
    return {"query": query, "total": 0, "matches": [], "mock": True}


async def device_search(params: dict) -> dict:
    """Search Shodan for internet-connected devices (ICS, SCADA, industrial systems).

    Uses Shodan's free search API. Critical for supply chain cyber risk assessment.

    Args:
        query: Search query (e.g., 'port:502 modbus', 'scada', 'product:siemens')
        limit: Max results (default: 5)
    """
    query = params.get("query", "scada")
    limit = params.get("limit", 5)
    key = _get_key()

    if not key:
        return _mock_device_search(query)

    try:
        # Try the search API first (requires membership)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{SHODAN_BASE}/shodan/host/search", params={
                "query": query, "limit": limit, "key": key,
            })
            data = resp.json()

        if "matches" in data:
            matches = []
            for m in data["matches"][:limit]:
                matches.append({
                    "ip": m.get("ip_str", ""),
                    "port": m.get("port", 0),
                    "org": m.get("org", ""),
                    "product": m.get("product", ""),
                    "vulns": list(m.get("vulns", [])[:3]),
                    "hostnames": m.get("hostnames", [])[:2],
                    "country": m.get("location", {}).get("country_name", ""),
                })
            return {
                "query": query,
                "total": data.get("total", 0),
                "matches": matches,
                "mock": False,
            }

        # Fallback: use Shodan InternetDB (free, no key needed) for specific IPs
        if data.get("error"):
            return {**_mock_device_search(query), "error": data["error"], "note": "Shodan search requires paid plan. Use shodan_host_info for free InternetDB lookups."}

        return _mock_device_search(query)
    except Exception:
        return _mock_device_search(query)


async def host_info(params: dict) -> dict:
    """Get info about a host from Shodan InternetDB (free, no key needed).

    Args:
        ip: IP address to look up
    """
    ip = params.get("ip", "8.8.8.8")

    try:
        # Shodan InternetDB is free and requires no API key
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://internetdb.shodan.io/{ip}")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "ip": ip,
                    "hostnames": data.get("hostnames", []),
                    "cpes": data.get("cpes", [])[:5],
                    "vulns": data.get("vulns", [])[:5],
                    "tags": data.get("tags", []),
                    "ports": data.get("ports", []),
                    "note": data.get("note", ""),
                    "source": "shodan_internetdb",
                    "mock": False,
                }
            elif resp.status_code == 404:
                return {"ip": ip, "note": "No data found for this IP", "mock": False}
    except Exception:
        pass

    # Fallback to paid API if InternetDB fails
    key = _get_key()
    if key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{SHODAN_BASE}/shodan/host/{ip}", params={"key": key})
                data = resp.json()
            if "ip_str" in data:
                return {
                    "ip": data["ip_str"],
                    "org": data.get("org", ""),
                    "country": data.get("country_name", ""),
                    "ports": data.get("ports", []),
                    "vulns": list(data.get("vulns", [])[:5]),
                    "mock": False,
                }
        except Exception:
            pass

    return {"ip": ip, "mock": True}


async def exploit_search(params: dict) -> dict:
    """Search Shodan Exploit DB for known vulnerabilities.

    Args:
        query: Exploit search query (e.g., 'apache', 'siemens')
    """
    query = params.get("query", "apache")
    key = _get_key()

    if not key:
        return {"query": query, "total": 0, "matches": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"https://exploits.shodan.io/api/search", params={
                "query": query, "key": key,
            })
            data = resp.json()

        if "matches" in data:
            matches = []
            for m in data["matches"][:5]:
                matches.append({
                    "title": m.get("title", ""),
                    "cve": m.get("cve", ""),
                    "source": m.get("source", ""),
                    "platform": m.get("platform", ""),
                })
            return {"query": query, "total": data.get("total", 0), "matches": matches, "mock": False}

        return {"query": query, "total": 0, "matches": [], "mock": True}
    except Exception:
        return {"query": query, "total": 0, "matches": [], "mock": True}


TOOLS = [
    {
        "name": "shodan_device_search",
        "description": "Search IoT/ICS/SCADA devices. Critical for cyber supply chain risk. Uses Shodan API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search (e.g., 'port:502 modbus', 'scada')"},
                "limit": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["query"]
        },
        "handler": device_search,
        "cache_ttl": 1800,
    },
    {
        "name": "shodan_host_info",
        "description": "Get host details (ports, vulns, org). Uses Shodan API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "IP address"}
            },
            "required": ["ip"]
        },
        "handler": host_info,
        "cache_ttl": 3600,
    },
    {
        "name": "shodan_exploit_search",
        "description": "Search exploit DB for vulnerabilities. Uses Shodan API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Exploit search (e.g., 'apache', 'siemens')"}
            },
            "required": ["query"]
        },
        "handler": exploit_search,
        "cache_ttl": 86400,
    },
]
