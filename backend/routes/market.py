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


@router.post("/supply-chain-stocks")
async def supply_chain_stocks(symbols: list[str] = None):
    """Get real-time quotes for supply chain stocks with caching and freshness info.
    
    Args:
        symbols: List of stock symbols to fetch (optional, defaults to major supply chain stocks)
    """
    import asyncio
    import time
    
    # Default to comprehensive list of 30 supply chain stocks if none provided
    if not symbols:
        symbols = [
            # Semiconductors
            "NVDA", "TSM", "ASML", "AMD", "AVGO", "MU", "QCOM", "INTC", "AMAT", "LRCX",
            # Automotive
            "TSLA", "TM", "F", "GM", "STLA", "HMC",
            # Pharma
            "LLY", "JNJ", "PFE", "MRK", "AZN", "NVO",
            # Industrial / Manufacturing
            "CAT", "HON", "GE", "DE",
            # Electronics / Tech
            "AAPL", "MSFT", "AMZN", "BABA", "SONY",
            # Logistics
            "ZTO", "FDX", "UPS", "MAERSK"
        ]
    
    # Use Yahoo Finance multiple quotes tool for better performance
    try:
        result = await invoke_tool("yahoo_multiple_quotes", {"symbols": symbols})
        stocks = result.get("stocks", [])
    except Exception as e:
        # Fallback to individual quotes if batch fails
        tasks = []
        for i, symbol in enumerate(symbols):
            # Add small delay for every 5th request to avoid rate limits
            if i > 0 and i % 5 == 0:
                tasks.append(asyncio.sleep(0.1))  # 100ms delay
            tasks.append(invoke_tool("yahoo_stock_quote", {"symbol": symbol}))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out sleep results and process stock data
        stock_results = [r for r in results if not isinstance(r, type(asyncio.sleep(0)))]
        
        stocks = []
        for i, symbol in enumerate(symbols):
            result = stock_results[i] if i < len(stock_results) else None
            if isinstance(result, Exception) or result is None:
                stocks.append({
                    "symbol": symbol,
                    "error": str(result) if result else "No data",
                    "timestamp": time.time(),
                    "data_freshness": "error"
                })
            else:
                stocks.append(result)
    
    return {
        "stocks": stocks,
        "timestamp": time.time(),
        "count": len(stocks),
        "market_hours": any(s.get("market_hours", False) for s in stocks if not isinstance(s, dict) or not s.get("error"))
    }


@router.post("/commodity-prices")
async def get_commodity_prices():
    """Get current commodity prices for Gold, Silver, Copper, Platinum, Crude Oil, and Diesel in Indian Rupees."""
    import time
    from backend.mcp.mcp_toolkit import invoke_tool
    
    # Define the 6 commodities with their Yahoo Finance symbols and units
    commodities = [
        {"name": "Gold", "symbol": "GC=F", "icon": "Gold", "category": "Precious Metals", "unit": "per ounce"},
        {"name": "Silver", "symbol": "SI=F", "icon": "Silver", "category": "Precious Metals", "unit": "per ounce"},
        {"name": "Copper", "symbol": "HG=F", "icon": "Copper", "category": "Industrial Metals", "unit": "per pound"},
        {"name": "Platinum", "symbol": "PL=F", "icon": "Platinum", "category": "Precious Metals", "unit": "per ounce"},
        {"name": "Crude Oil", "symbol": "CL=F", "icon": "Oil", "category": "Energy", "unit": "per barrel"},
        {"name": "Diesel", "symbol": "HO=F", "icon": "Diesel", "category": "Energy", "unit": "per gallon"}  # Heating Oil as diesel proxy
    ]
    
    symbols = [commodity["symbol"] for commodity in commodities]
    
    # Fetch USD/INR conversion rate
    usd_inr_rate = 83.50  # Default fallback rate
    try:
        inr_quote = await invoke_tool("yahoo_stock_quote", {"symbol": "INR=X"})
        if inr_quote and not inr_quote.get("error"):
            usd_inr_rate = inr_quote.get("current_price", 83.50)
    except Exception as e:
        # Use default rate if conversion fails
        pass
    
    # Use Yahoo Finance multiple quotes tool for better performance
    try:
        result = await invoke_tool("yahoo_multiple_quotes", {"symbols": symbols})
        quotes = result.get("stocks", [])
    except Exception as e:
        # Fallback to individual quotes if batch fails
        quotes = []
        for symbol in symbols:
            try:
                quote = await invoke_tool("yahoo_stock_quote", {"symbol": symbol})
                quotes.append(quote)
            except Exception as quote_error:
                quotes.append({
                    "symbol": symbol,
                    "error": str(quote_error),
                    "timestamp": time.time(),
                    "data_freshness": "error"
                })
    
    # Merge commodity data with quotes and convert to INR
    commodity_data = []
    for commodity in commodities:
        quote = next((q for q in quotes if q.get("symbol") == commodity["symbol"]), None)
        
        # Validate that the quote has realistic data (not placeholder values)
        usd_price = quote.get("current_price", 0) if quote else 0
        is_valid_quote = (quote and not quote.get("error") and 
                          usd_price > 0 and 
                          not (commodity["symbol"] == "GC=F" and usd_price < 1000) and  # Gold should be > $1000
                          not (commodity["symbol"] == "SI=F" and usd_price < 10) and    # Silver should be > $10
                          not (commodity["symbol"] == "PL=F" and usd_price < 500))      # Platinum should be > $500
        
        if is_valid_quote:
            # Convert USD prices to INR
            usd_change = quote.get("change", 0)
            usd_prev_close = quote.get("prev_close", 0)
            usd_high = quote.get("high", 0)
            usd_low = quote.get("low", 0)
            usd_open = quote.get("open", 0)
            
            commodity_data.append({
                "name": commodity["name"],
                "symbol": commodity["symbol"],
                "icon": commodity["icon"],
                "category": commodity["category"],
                "unit": commodity["unit"],
                "current_price": round(usd_price * usd_inr_rate, 2),
                "change": round(usd_change * usd_inr_rate, 2),
                "change_percent": quote.get("change_percent", 0),
                "prev_close": round(usd_prev_close * usd_inr_rate, 2),
                "high": round(usd_high * usd_inr_rate, 2),
                "low": round(usd_low * usd_inr_rate, 2),
                "open": round(usd_open * usd_inr_rate, 2),
                "usd_price": usd_price,  # Keep original USD price for reference
                "usd_inr_rate": usd_inr_rate,
                "currency": "INR",
                "currency_symbol": "INR",
                "timestamp": quote.get("timestamp", time.time()),
                "data_freshness": quote.get("data_freshness", "unknown"),
                "market_hours": quote.get("market_hours", False),
                "error": None
            })
        else:
            # Handle error case with realistic mock data in USD, then convert to INR
            # These are realistic current market prices (April 2025 estimates)
            mock_prices_usd = {
                "GC=F": 2420.00,   # Gold ~$2,420/oz
                "SI=F": 32.50,     # Silver ~$32.50/oz
                "HG=F": 4.25,      # Copper ~$4.25/lb
                "PL=F": 980.00,    # Platinum ~$980/oz
                "CL=F": 82.50,     # Crude Oil ~$82.50/barrel
                "HO=F": 2.95       # Heating Oil ~$2.95/gallon
            }
            
            base_price_usd = mock_prices_usd.get(commodity["symbol"], 100.0)
            # Generate realistic random change (-2% to +2%)
            import random
            change_percent = round(random.uniform(-2.0, 2.0), 2)
            change_usd = round(base_price_usd * (change_percent / 100), 2)
            
            # Convert mock prices to INR
            base_price_inr = round(base_price_usd * usd_inr_rate, 2)
            change_inr = round(change_usd * usd_inr_rate, 2)
            
            commodity_data.append({
                "name": commodity["name"],
                "symbol": commodity["symbol"],
                "icon": commodity["icon"],
                "category": commodity["category"],
                "unit": commodity["unit"],
                "current_price": base_price_inr,
                "change": change_inr,
                "change_percent": change_percent,
                "prev_close": round((base_price_usd - change_usd) * usd_inr_rate, 2),
                "high": round((base_price_usd + (base_price_usd * 0.015)) * usd_inr_rate, 2),
                "low": round((base_price_usd - (base_price_usd * 0.015)) * usd_inr_rate, 2),
                "open": base_price_inr,
                "usd_price": base_price_usd,
                "usd_inr_rate": usd_inr_rate,
                "currency": "INR",
                "currency_symbol": "INR",
                "timestamp": time.time(),
                "data_freshness": "mock",
                "market_hours": False,
                "error": quote.get("error") if quote else "No data available"
            })
    
    return {
        "commodities": commodity_data,
        "timestamp": time.time(),
        "count": len(commodity_data),
        "market_hours": any(c.get("market_hours", False) for c in commodity_data),
        "usd_inr_rate": usd_inr_rate,
        "currency": "INR"
    }


@router.post("/forex-rates")
async def get_forex_rates():
    """Get current forex rates for 9 major currencies vs USD."""
    import time
    from backend.mcp.mcp_toolkit import invoke_tool
    
    # Define 9 currencies with their Yahoo Finance symbols
    currencies = [
        {"code": "INR", "name": "Indian Rupee", "country": "India", "flag": "🇮🇳", "symbol": "INR=X"},
        {"code": "AUD", "name": "Australian Dollar", "country": "Australia", "flag": "🇦🇺", "symbol": "AUD=X"},
        {"code": "CNY", "name": "Chinese Yuan", "country": "China", "flag": "🇨🇳", "symbol": "CNY=X"},
        {"code": "EUR", "name": "Euro", "country": "Eurozone", "flag": "🇪🇺", "symbol": "EUR=X"},
        {"code": "GBP", "name": "British Pound", "country": "United Kingdom", "flag": "🇬🇧", "symbol": "GBP=X"},
        {"code": "KWD", "name": "Kuwaiti Dinar", "country": "Kuwait", "flag": "🇰🇼", "symbol": "KWD=X"},
        {"code": "JPY", "name": "Japanese Yen", "country": "Japan", "flag": "🇯🇵", "symbol": "JPY=X"},
        {"code": "USD", "name": "US Dollar", "country": "United States", "flag": "🇺🇸", "symbol": "USD=X"},
        {"code": "SAR", "name": "Saudi Riyal", "country": "Saudi Arabia", "flag": "🇸🇦", "symbol": "SAR=X"},
    ]
    
    symbols = [c["symbol"] for c in currencies]
    
    # Fetch rates from Yahoo Finance
    try:
        result = await invoke_tool("yahoo_multiple_quotes", {"symbols": symbols})
        quotes = result.get("stocks", [])
    except Exception as e:
        quotes = []
    
    # Realistic fallback rates (approximate values as of April 2025)
    fallback_rates = {
        "INR=X": 83.50,
        "AUD=X": 1.52,
        "CNY=X": 7.24,
        "EUR=X": 0.92,
        "GBP=X": 0.79,
        "KWD=X": 0.31,
        "JPY=X": 151.50,
        "USD=X": 1.00,
        "SAR=X": 3.75
    }
    
    # Build currency data
    currency_data = []
    for currency in currencies:
        quote = next((q for q in quotes if q.get("symbol") == currency["symbol"]), None)
        
        # Check if quote is valid
        rate = quote.get("current_price", 0) if quote else 0
        is_valid = quote and not quote.get("error") and rate > 0
        
        if not is_valid:
            rate = fallback_rates.get(currency["symbol"], 1.0)
        
        # Calculate change (use quote data if available, otherwise generate small random change)
        if is_valid and quote.get("change_percent") is not None:
            change_percent = quote.get("change_percent", 0)
        else:
            import random
            change_percent = round(random.uniform(-0.5, 0.5), 2)
        
        currency_data.append({
            "code": currency["code"],
            "name": currency["name"],
            "country": currency["country"],
            "flag": currency["flag"],
            "rate": round(rate, 4),
            "change": round(rate * (change_percent / 100), 4),
            "change_percent": change_percent,
            "symbol": currency["symbol"],
            "timestamp": time.time(),
            "data_freshness": "real_time" if is_valid else "mock"
        })
    
    return {
        "currencies": currency_data,
        "base_currency": "USD",
        "timestamp": time.time(),
        "count": len(currency_data)
    }
