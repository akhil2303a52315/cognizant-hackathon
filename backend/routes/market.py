"""Market Data API — Real-time stocks, forex, commodities, company data for frontend."""
from fastapi import APIRouter
from backend.mcp.registry import invoke_tool

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/ticker")
async def market_ticker():
    """Get real-time market ticker data (stocks, forex, commodities) for dashboard."""
    import asyncio

    # Fetch multiple data sources in parallel
    tasks = [
        invoke_tool("stock_quote", {"symbol": "TSM"}),
        invoke_tool("stock_quote", {"symbol": "INTC"}),
        invoke_tool("stock_quote", {"symbol": "AAPL"}),
        invoke_tool("stock_quote", {"symbol": "NVDA"}),
        invoke_tool("exchange_rate", {"base": "USD", "quote": "EUR,CNY,JPY,TWD,KRW,GBP"}),
        invoke_tool("fred_commodity_price", {"commodity": "crude_oil"}),
        invoke_tool("fred_commodity_price", {"commodity": "copper"}),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    stocks = []
    for i, sym in enumerate(["TSM", "INTC", "AAPL", "NVDA"]):
        r = results[i]
        if isinstance(r, Exception):
            stocks.append({"symbol": sym, "error": str(r)})
        else:
            stocks.append(r)

    forex = results[4] if not isinstance(results[4], Exception) else {"rates": {}, "mock": True}
    commodities = []
    for i, name in enumerate(["crude_oil", "copper"]):
        r = results[5 + i]
        if isinstance(r, Exception):
            commodities.append({"commodity": name, "error": str(r)})
        else:
            commodities.append(r)

    return {
        "stocks": stocks,
        "forex": forex,
        "commodities": commodities,
        "timestamp": __import__("time").time(),
    }


@router.get("/company/{symbol}")
async def company_overview(symbol: str):
    """Get full company overview: profile + quote + financials."""
    import asyncio

    tasks = [
        invoke_tool("company_profile", {"symbol": symbol}),
        invoke_tool("stock_quote", {"symbol": symbol}),
        invoke_tool("company_financials", {"symbol": symbol}),
        invoke_tool("wikipedia_summary", {"title": symbol}),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    profile = results[0] if not isinstance(results[0], Exception) else {}
    quote = results[1] if not isinstance(results[1], Exception) else {}
    financials = results[2] if not isinstance(results[2], Exception) else {}
    wiki = results[3] if not isinstance(results[3], Exception) else {}

    return {
        "symbol": symbol,
        "profile": profile,
        "quote": quote,
        "financials": financials,
        "wikipedia": wiki,
    }


@router.get("/risk-dashboard")
async def risk_dashboard():
    """Get risk dashboard data: earthquakes, disasters, weather for key supplier regions."""
    import asyncio

    # Key supply chain regions
    regions = [
        {"name": "Taiwan (Semiconductors)", "lat": 25.0, "lon": 121.5},
        {"name": "Japan (Electronics)", "lat": 35.6, "lon": 139.7},
        {"name": "China (Manufacturing)", "lat": 31.2, "lon": 121.4},
        {"name": "South Korea (Memory Hub)", "lat": 37.5, "lon": 127.0},
        {"name": "Germany (Automotive Hub)", "lat": 52.5, "lon": 13.4},
        {"name": "USA (West Coast Logistics)", "lat": 34.0, "lon": -118.2},
        {"name": "Vietnam (Textile/Assembly)", "lat": 21.0, "lon": 105.8},
        {"name": "Brazil (Iron/Agri Hub)", "lat": -23.5, "lon": -46.6},
    ]

    tasks = []
    for r in regions:
        tasks.append(invoke_tool("earthquake_check", {"latitude": r["lat"], "longitude": r["lon"], "min_magnitude": 4.0, "days": 30}))
        tasks.append(invoke_tool("weather_forecast", {"latitude": r["lat"], "longitude": r["lon"], "days": 3}))

    tasks.append(invoke_tool("disaster_alerts", {"limit": 5}))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    region_data = []
    for i, r in enumerate(regions):
        eq = results[i * 2] if not isinstance(results[i * 2], Exception) else {"earthquakes": [], "mock": True}
        wx = results[i * 2 + 1] if not isinstance(results[i * 2 + 1], Exception) else {"forecast": [], "mock": True}
        region_data.append({
            "name": r["name"],
            "earthquakes": eq,
            "weather": wx,
        })

    disasters = results[-1] if not isinstance(results[-1], Exception) else {"alerts": [], "mock": True}

    return {
        "regions": region_data,
        "global_disasters": disasters,
    }


@router.get("/brand-intel")
async def brand_intelligence():
    """Get brand intelligence data: competitor ads, social sentiment, Wikipedia."""
    import asyncio

    tasks = [
        invoke_tool("reddit_sentiment", {"subreddit": "supplychain", "limit": 5}),
        invoke_tool("reddit_sentiment", {"subreddit": "logistics", "limit": 5}),
        invoke_tool("wikipedia_search", {"query": "supply chain management technology", "limit": 5}),
        invoke_tool("arxiv_search", {"query": "supply chain brand resilience", "max_results": 3}),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "supplychain_reddit": results[0] if not isinstance(results[0], Exception) else {},
        "logistics_reddit": results[1] if not isinstance(results[1], Exception) else {},
        "wiki_articles": results[2] if not isinstance(results[2], Exception) else {},
        "research_papers": results[3] if not isinstance(results[3], Exception) else {},
    }
