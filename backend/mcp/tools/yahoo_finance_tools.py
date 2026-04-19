"""
Yahoo Finance MCP Tools
Provides real-time stock data using Yahoo Finance API
"""

import asyncio
import time
from typing import Dict, Any, Optional
import yfinance as yf

def _get_market_status() -> bool:
    """Check if US market is currently open."""
    import datetime
    from datetime import timezone
    
    now = datetime.datetime.now(timezone.utc)
    # Convert to Eastern Time (US market timezone)
    eastern_tz = datetime.timezone(datetime.timedelta(hours=-5))  # EST
    eastern_time = now.astimezone(eastern_tz)
    
    # Check if it's weekday
    if eastern_time.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return False
    
    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = eastern_time.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = eastern_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= eastern_time <= market_close

def _mock_stock_data(symbol: str) -> Dict[str, Any]:
    """Generate mock stock data for testing."""
    import random
    
    mock_prices = {
        'NVDA': 145.67, 'TSM': 142.30, 'ASML': 780.45, 'AMD': 125.80, 'AVGO': 680.20,
        'MU': 78.50, 'QCOM': 155.30, 'INTC': 42.15, 'AMAT': 185.60, 'LRCX': 245.80,
        'TSLA': 245.30, 'TM': 185.40, 'F': 12.45, 'GM': 38.90, 'STLA': 17.80, 'HMC': 32.60,
        'LLY': 625.40, 'JNJ': 158.70, 'PFE': 28.90, 'MRK': 132.80, 'AZN': 78.50, 'NVO': 105.30,
        'CAT': 312.40, 'HON': 198.70, 'GE': 178.90, 'DE': 425.60,
        'AAPL': 178.60, 'MSFT': 415.20, 'AMZN': 178.30, 'BABA': 87.50, 'SONY': 98.40,
        'ZTO': 22.80, 'FDX': 254.30, 'UPS': 156.80, 'MAERSK': 1680.50
    }
    
    base_price = mock_prices.get(symbol, 100.0)
    change = round(random.uniform(-5, 5), 2)
    change_percent = round((change / base_price) * 100, 2)
    
    return {
        "symbol": symbol,
        "current_price": round(base_price + change, 2),
        "change": change,
        "change_percent": change_percent,
        "high": round(base_price + random.uniform(0, 10), 2),
        "low": round(base_price - random.uniform(0, 10), 2),
        "open": round(base_price, 2),
        "prev_close": base_price,
        "timestamp": time.time(),
        "data_freshness": "mock",
        "market_hours": _get_market_status(),
        "mock": True
    }

async def yahoo_stock_quote(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get real-time stock quote from Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'TSLA')
    """
    import time
    symbol = params.get("symbol", "AAPL").upper()
    current_time = time.time()

    try:
        # Use yfinance to get stock data
        ticker = yf.Ticker(symbol)
        
        # Get current market data
        info = ticker.info
        history = ticker.history(period="1d", interval="1m")
        
        if history.empty:
            # Fallback to mock data if no recent data
            return _mock_stock_data(symbol)
        
        # Get the most recent data
        latest = history.iloc[-1]
        
        # Extract current price and change data
        current_price = latest['Close']
        prev_close = info.get('previousClose', current_price)
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
        
        # Determine data freshness
        data_freshness = "real_time"
        is_market_hours = _get_market_status()
        
        # If no current price or it's after hours, mark as stale
        if current_price == 0 or current_price == prev_close:
            data_freshness = "market_closed" if not is_market_hours else "stale"
        
        return {
            "symbol": symbol,
            "current_price": round(float(current_price), 2),
            "change": round(float(change), 2),
            "change_percent": round(float(change_percent), 2),
            "high": round(float(latest['High']), 2),
            "low": round(float(latest['Low']), 2),
            "open": round(float(latest['Open']), 2),
            "prev_close": round(float(prev_close), 2),
            "timestamp": current_time,
            "data_freshness": data_freshness,
            "market_hours": is_market_hours,
            "mock": False,
            "company_name": info.get('shortName', ''),
            "sector": info.get('sector', ''),
            "volume": int(latest['Volume']) if 'Volume' in latest else 0
        }
        
    except Exception as e:
        # Return mock data with error info
        mock_data = _mock_stock_data(symbol)
        mock_data["error"] = str(e)
        mock_data["data_freshness"] = "error"
        return mock_data

async def yahoo_multiple_quotes(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get multiple stock quotes from Yahoo Finance.
    
    Args:
        symbols: List of stock ticker symbols
    """
    symbols = params.get("symbols", [])
    if not symbols:
        return {"stocks": [], "timestamp": time.time(), "count": 0}
    
    # Fetch all stock quotes concurrently
    tasks = [yahoo_stock_quote({"symbol": symbol}) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    stocks = []
    for i, symbol in enumerate(symbols):
        result = results[i]
        if isinstance(result, Exception):
            stocks.append(_mock_stock_data(symbol))
        else:
            stocks.append(result)
    
    return {
        "stocks": stocks,
        "timestamp": time.time(),
        "count": len(stocks),
        "market_hours": any(s.get("market_hours", False) for s in stocks if isinstance(s, dict))
    }

async def yahoo_company_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed company information from Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol
    """
    symbol = params.get("symbol", "AAPL").upper()
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol,
            "company_name": info.get('shortName', ''),
            "sector": info.get('sector', ''),
            "industry": info.get('industry', ''),
            "market_cap": info.get('marketCap', 0),
            "enterprise_value": info.get('enterpriseValue', 0),
            "trailing_pe": info.get('trailingPE', 0),
            "forward_pe": info.get('forwardPE', 0),
            "peg_ratio": info.get('pegRatio', 0),
            "price_to_sales": info.get('priceToSalesTrailing12Months', 0),
            "price_to_book": info.get('priceToBook', 0),
            "enterprise_to_revenue": info.get('enterpriseToRevenue', 0),
            "enterprise_to_ebitda": info.get('enterpriseToEbitda', 0),
            "profit_margins": info.get('profitMargins', 0),
            "gross_margins": info.get('grossMargins', 0),
            "operating_margins": info.get('operatingMargins', 0),
            "return_on_assets": info.get('returnOnAssets', 0),
            "return_on_equity": info.get('returnOnEquity', 0),
            "revenue_growth": info.get('revenueGrowth', 0),
            "earnings_growth": info.get('earningsGrowth', 0),
            "dividend_yield": info.get('dividendYield', 0),
            "dividend_rate": info.get('dividendRate', 0),
            "payout_ratio": info.get('payoutRatio', 0),
            "description": info.get('longBusinessSummary', ''),
            "website": info.get('website', ''),
            "employees": info.get('fullTimeEmployees', 0),
            "country": info.get('country', ''),
            "currency": info.get('currency', 'USD'),
            "exchange": info.get('exchange', ''),
            "quote_type": info.get('quoteType', ''),
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e),
            "timestamp": time.time()
        }

# Register tools
TOOLS = {
    "yahoo_stock_quote": {
        "description": "Get real-time stock quote from Yahoo Finance",
        "parameters": {
            "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'TSLA')"}
        }
    },
    "yahoo_multiple_quotes": {
        "description": "Get multiple stock quotes from Yahoo Finance",
        "parameters": {
            "symbols": {"type": "array", "description": "List of stock ticker symbols"}
        }
    },
    "yahoo_company_info": {
        "description": "Get detailed company information from Yahoo Finance",
        "parameters": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        }
    }
}

def register():
    """Register Yahoo Finance tools with the MCP registry."""
    from backend.mcp.registry import register_tool
    
    register_tool(
        name="yahoo_stock_quote",
        description="Get real-time stock quote from Yahoo Finance",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'TSLA')"}
            },
            "required": ["symbol"]
        },
        handler=yahoo_stock_quote,
        category="financial",
        cache_ttl=60,  # 1 minute cache for stock quotes
        allowed_agents=["finance", "market", "moderator"]
    )
    
    register_tool(
        name="yahoo_multiple_quotes",
        description="Get multiple stock quotes from Yahoo Finance",
        input_schema={
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "description": "List of stock ticker symbols"}
            },
            "required": ["symbols"]
        },
        handler=yahoo_multiple_quotes,
        category="financial",
        cache_ttl=60,  # 1 minute cache for stock quotes
        allowed_agents=["finance", "market", "moderator"]
    )
    
    register_tool(
        name="yahoo_company_info",
        description="Get detailed company information from Yahoo Finance",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["symbol"]
        },
        handler=yahoo_company_info,
        category="financial",
        cache_ttl=3600,  # 1 hour cache for company info
        allowed_agents=["finance", "market", "moderator"]
    )
