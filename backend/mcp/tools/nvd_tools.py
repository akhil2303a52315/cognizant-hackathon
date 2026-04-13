"""NIST NVD MCP Tools — Cyber vulnerability data for supply chain infrastructure risk."""
import httpx
import os

NVD_BASE = "https://services.nvd.nist.gov/rest/json"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.nist_nvd_api_key or os.getenv("NIST_NVD_API_KEY", "")
    except Exception:
        return os.getenv("NIST_NVD_API_KEY", "")


def _mock_cve(cve_id: str) -> dict:
    return {
        "cve_id": cve_id,
        "description": "Potential supply chain infrastructure vulnerability",
        "cvss_v3_score": 7.5,
        "severity": "HIGH",
        "published": "2025-01-10",
        "mock": True,
    }


def _mock_search(keyword: str) -> dict:
    return {
        "keyword": keyword,
        "vulnerabilities": [
            {"cve_id": "CVE-2025-0001", "description": f"Vulnerability related to {keyword}", "cvss_score": 8.1, "severity": "HIGH", "mock": True},
            {"cve_id": "CVE-2025-0002", "description": f"Infrastructure risk: {keyword}", "cvss_score": 6.5, "severity": "MEDIUM", "mock": True},
        ],
        "total_results": 2,
        "mock": True,
    }


async def cve_search(params: dict) -> dict:
    """Search CVEs by keyword from NIST NVD.

    Args:
        keyword: Search keyword (e.g., 'supply chain', 'SCADA', 'industrial control')
        results_per_page: Max results (default: 10)
    """
    keyword = params.get("keyword", "supply chain")
    results_per_page = min(params.get("results_per_page", 10), 50)
    key = _get_key()

    headers = {}
    if key:
        headers["apiKey"] = key

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{NVD_BASE}/cves/2.0", params={
                "keywordSearch": keyword,
                "resultsPerPage": results_per_page,
            }, headers=headers)
            data = resp.json()

        vulnerabilities = []
        for vuln in data.get("vulnerabilities", [])[:results_per_page]:
            cve = vuln.get("cve", {})
            descriptions = cve.get("descriptions", [])
            desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")

            metrics = cve.get("metrics", {})
            cvss_v3 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV31") else {}
            cvss_v2 = metrics.get("cvssMetricV2", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV2") else {}

            score = cvss_v3.get("baseScore") or cvss_v2.get("baseScore") or 0
            severity = cvss_v3.get("baseSeverity") or "UNKNOWN"

            vulnerabilities.append({
                "cve_id": cve.get("id", ""),
                "description": desc[:500],
                "cvss_score": score,
                "severity": severity,
                "published": cve.get("published", ""),
                "last_modified": cve.get("lastModified", ""),
                "url": f"https://nvd.nist.gov/vuln/detail/{cve.get('id', '')}",
            })

        return {
            "keyword": keyword,
            "vulnerabilities": vulnerabilities,
            "total_results": data.get("totalResults", 0),
            "mock": False,
        }
    except Exception:
        return _mock_search(keyword)


async def cve_by_cpe(params: dict) -> dict:
    """Search CVEs by CPE (Common Platform Enumeration) name from NIST NVD.

    Args:
        cpe_name: CPE name (e.g., 'cpe:2.3:a:siemens:*:*:*:*:*:*:*:*:*')
        results_per_page: Max results (default: 10)
    """
    cpe_name = params.get("cpe_name", "cpe:2.3:a:siemens:*:*:*:*:*:*:*:*:*")
    results_per_page = min(params.get("results_per_page", 10), 50)
    key = _get_key()

    headers = {}
    if key:
        headers["apiKey"] = key

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{NVD_BASE}/cves/2.0", params={
                "cpeName": cpe_name,
                "resultsPerPage": results_per_page,
            }, headers=headers)
            data = resp.json()

        vulnerabilities = []
        for vuln in data.get("vulnerabilities", [])[:results_per_page]:
            cve = vuln.get("cve", {})
            descriptions = cve.get("descriptions", [])
            desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")

            metrics = cve.get("metrics", {})
            cvss_v3 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV31") else {}
            score = cvss_v3.get("baseScore", 0)
            severity = cvss_v3.get("baseSeverity", "UNKNOWN")

            vulnerabilities.append({
                "cve_id": cve.get("id", ""),
                "description": desc[:500],
                "cvss_score": score,
                "severity": severity,
                "published": cve.get("published", ""),
            })

        return {
            "cpe_name": cpe_name,
            "vulnerabilities": vulnerabilities,
            "total_results": data.get("totalResults", 0),
            "mock": False,
        }
    except Exception:
        return _mock_search(cpe_name)


async def cve_details(params: dict) -> dict:
    """Get details for a specific CVE from NIST NVD.

    Args:
        cve_id: CVE ID (e.g., 'CVE-2024-0001')
    """
    cve_id = params.get("cve_id", "CVE-2024-0001")
    key = _get_key()

    headers = {}
    if key:
        headers["apiKey"] = key

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{NVD_BASE}/cves/2.0", params={
                "cveId": cve_id,
            }, headers=headers)
            data = resp.json()

        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return _mock_cve(cve_id)

        cve = vulns[0].get("cve", {})
        descriptions = cve.get("descriptions", [])
        desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")

        metrics = cve.get("metrics", {})
        cvss_v3 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV31") else {}
        score = cvss_v3.get("baseScore", 0)
        severity = cvss_v3.get("baseSeverity", "UNKNOWN")

        references = [{"url": r.get("url", ""), "source": r.get("source", "")} for r in cve.get("references", [])]

        weaknesses = [w.get("description", [{}])[0].get("value", "") for w in cve.get("weaknesses", [])]

        return {
            "cve_id": cve.get("id", cve_id),
            "description": desc,
            "cvss_v3_score": score,
            "severity": severity,
            "attack_vector": cvss_v3.get("attackVector", ""),
            "published": cve.get("published", ""),
            "last_modified": cve.get("lastModified", ""),
            "references": references,
            "weaknesses": weaknesses,
            "url": f"https://nvd.nist.gov/vuln/detail/{cve.get('id', cve_id)}",
            "mock": False,
        }
    except Exception:
        return _mock_cve(cve_id)


async def recent_cves(params: dict) -> dict:
    """Get recently published CVEs from NIST NVD.

    Args:
        days_back: Number of days to look back (default: 7)
        severity_filter: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
        results_per_page: Max results (default: 10)
    """
    import datetime
    days_back = params.get("days_back", 7)
    severity_filter = params.get("severity_filter", "")
    results_per_page = min(params.get("results_per_page", 10), 50)
    key = _get_key()

    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=days_back)

    headers = {}
    if key:
        headers["apiKey"] = key

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{NVD_BASE}/cves/2.0", params={
                "pubStartDate": start_date.strftime("%Y-%m-%dT00:00:00.000"),
                "pubEndDate": end_date.strftime("%Y-%m-%dT23:59:59.999"),
                "resultsPerPage": results_per_page,
            }, headers=headers)
            data = resp.json()

        vulnerabilities = []
        for vuln in data.get("vulnerabilities", [])[:results_per_page]:
            cve = vuln.get("cve", {})
            descriptions = cve.get("descriptions", [])
            desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")

            metrics = cve.get("metrics", {})
            cvss_v3 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV31") else {}
            score = cvss_v3.get("baseScore", 0)
            severity = cvss_v3.get("baseSeverity", "UNKNOWN")

            if severity_filter and severity != severity_filter:
                continue

            vulnerabilities.append({
                "cve_id": cve.get("id", ""),
                "description": desc[:300],
                "cvss_score": score,
                "severity": severity,
                "published": cve.get("published", ""),
            })

        return {
            "days_back": days_back,
            "vulnerabilities": vulnerabilities,
            "total_results": data.get("totalResults", 0),
            "mock": False,
        }
    except Exception:
        return _mock_search("recent CVEs")


TOOLS = [
    {
        "name": "nvd_cve_search",
        "description": "Search CVEs by keyword (supply chain, SCADA, industrial control). Uses NIST NVD API. Critical for Risk Sentinel cyber risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword (e.g., 'supply chain', 'SCADA', 'industrial control')"},
                "results_per_page": {"type": "integer", "description": "Max results (max 50)", "default": 10}
            },
            "required": ["keyword"]
        },
        "handler": cve_search,
        "cache_ttl": 3600,
    },
    {
        "name": "nvd_cve_by_cpe",
        "description": "Search CVEs by CPE name (vendor/product). Uses NIST NVD API. Best for specific infrastructure vulnerability checks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cpe_name": {"type": "string", "description": "CPE name (e.g., 'cpe:2.3:a:siemens:*:*:*:*:*:*:*:*:*')"},
                "results_per_page": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["cpe_name"]
        },
        "handler": cve_by_cpe,
        "cache_ttl": 3600,
    },
    {
        "name": "nvd_cve_details",
        "description": "Get full details for a specific CVE. Uses NIST NVD API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cve_id": {"type": "string", "description": "CVE ID (e.g., 'CVE-2024-0001')"}
            },
            "required": ["cve_id"]
        },
        "handler": cve_details,
        "cache_ttl": 86400,
    },
    {
        "name": "nvd_recent_cves",
        "description": "Get recently published CVEs (last N days). Uses NIST NVD API. Best for ongoing cyber risk monitoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {"type": "integer", "description": "Days to look back", "default": 7},
                "severity_filter": {"type": "string", "description": "Filter: CRITICAL, HIGH, MEDIUM, LOW"},
                "results_per_page": {"type": "integer", "description": "Max results", "default": 10}
            }
        },
        "handler": recent_cves,
        "cache_ttl": 3600,
    },
]
