"""UN Comtrade & Trade Data MCP Tools — Bilateral trade flows, tariff data."""
import httpx
import os

COMTRADE_BASE = "https://comtradeapi.un.org/dataportal/api/v1"


def _mock_trade_flows(partner: str, commodity: str) -> dict:
    return {
        "partner": partner,
        "commodity": commodity,
        "exports_usd": 15_000_000_000,
        "imports_usd": 8_000_000_000,
        "trade_balance": 7_000_000_000,
        "year": 2023,
        "mock": True
    }


async def trade_flows(params: dict) -> dict:
    """Get bilateral trade flow data from UN Comtrade. Free (registration required for high volume).
    
    Args:
        reporter: Reporting country code (e.g., 'USA', 'CHN', 'TWN')
        partner: Partner country code
        year: Year (default: 2023)
        commodity: HS commodity code or description (default: all)
    """
    reporter = params.get("reporter", "USA")
    partner = params.get("partner", "CHN")
    year = params.get("year", 2023)
    commodity = params.get("commodity", "all")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{COMTRADE_BASE}/DataFlow", params={
                "reporterCode": reporter,
                "partnerCode": partner,
                "period": year,
                "typeCode": "C",
                "freqCode": "A",
                "clCode": "HS",
            }, headers={"User-Agent": "SupplyChainGPT/1.0"})
            data = resp.json()

        records = data.get("data", []) if isinstance(data, dict) else []
        if not records:
            return _mock_trade_flows(partner, commodity)

        total_exports = sum(r.get("primaryValue", 0) for r in records if r.get("flowCode") == "X")
        total_imports = sum(r.get("primaryValue", 0) for r in records if r.get("flowCode") == "M")

        return {
            "reporter": reporter,
            "partner": partner,
            "year": year,
            "exports_usd": total_exports,
            "imports_usd": total_imports,
            "trade_balance": total_exports - total_imports,
            "records_count": len(records),
            "mock": False
        }
    except Exception:
        return _mock_trade_flows(partner, commodity)


async def sec_filing(params: dict) -> dict:
    """Get SEC EDGAR filing data for a company. No API key needed (rate-limited).
    
    Args:
        cik: Company CIK number or ticker (e.g., '0001046179' for TSMC)
        filing_type: Filing type (e.g., '10-K', '10-Q', '8-K')
    """
    cik = params.get("cik", "0001046179")
    filing_type = params.get("filing_type", "10-K")

    try:
        # SEC EDGAR full-text search
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://efts.sec.gov/LATEST/search-index", params={
                "q": f"{cik} {filing_type}",
                "dateRange": "1y",
            }, headers={"User-Agent": "SupplyChainGPT/1.0 research@supplychaingpt.ai"})
            data = resp.json()

        filings = data.get("hits", {}).get("hits", [])[:5]
        results = [{
            "title": f.get("_source", {}).get("file_date", ""),
            "filing_type": f.get("_source", {}).get("form_type", ""),
            "file_date": f.get("_source", {}).get("file_date", ""),
            "link": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}",
        } for f in filings]

        return {"cik": cik, "filing_type": filing_type, "filings": results, "mock": False}
    except Exception:
        return {"cik": cik, "filing_type": filing_type, "filings": [], "mock": True}


async def opencorporates_search(params: dict) -> dict:
    """Search OpenCorporates for company data. No API key needed (rate-limited).
    
    Args:
        query: Company name to search
        jurisdiction: Country code filter (e.g., 'us', 'tw')
    """
    query = params.get("query", "TSMC")
    jurisdiction = params.get("jurisdiction", "")

    try:
        params_dict = {"q": query}
        if jurisdiction:
            params_dict["jurisdiction_code"] = jurisdiction

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.opencorporates.com/v0.4/companies/search", params=params_dict)
            data = resp.json()

        companies = data.get("results", {}).get("companies", [])[:5]
        results = [{
            "name": c.get("company", {}).get("name", ""),
            "jurisdiction": c.get("company", {}).get("jurisdiction_code", ""),
            "incorporation_date": c.get("company", {}).get("incorporation_date", ""),
            "status": c.get("company", {}).get("current_status", ""),
            "opencorporates_url": c.get("company", {}).get("opencorporates_url", ""),
        } for c in companies]

        return {"query": query, "companies": results, "mock": False}
    except Exception:
        return {"query": query, "companies": [], "mock": True}


TOOLS = [
    {
        "name": "trade_flows",
        "description": "Get bilateral trade flow data from UN Comtrade. Shows exports/imports between countries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reporter": {"type": "string", "description": "Reporting country (e.g., 'USA', 'CHN')", "default": "USA"},
                "partner": {"type": "string", "description": "Partner country (e.g., 'CHN', 'TWN')", "default": "CHN"},
                "year": {"type": "integer", "description": "Year (default: 2023)", "default": 2023},
                "commodity": {"type": "string", "description": "HS commodity code or 'all'", "default": "all"}
            }
        },
        "handler": trade_flows,
        "cache_ttl": 86400,
    },
    {
        "name": "sec_filing",
        "description": "Get SEC EDGAR filing data for a company. Useful for supplier financial deep analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cik": {"type": "string", "description": "Company CIK number", "default": "0001046179"},
                "filing_type": {"type": "string", "description": "Filing type: '10-K', '10-Q', '8-K'", "default": "10-K"}
            }
        },
        "handler": sec_filing,
        "cache_ttl": 86400,
    },
    {
        "name": "opencorporates_search",
        "description": "Search OpenCorporates for company registration data. Good for supplier verification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company name"},
                "jurisdiction": {"type": "string", "description": "Country code filter (e.g., 'us', 'tw')"}
            },
            "required": ["query"]
        },
        "handler": opencorporates_search,
        "cache_ttl": 86400,
    },
]
