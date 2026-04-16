from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import re
import logging

logger = logging.getLogger(__name__)


def _parse_confidence(text: str, default: float = 50.0) -> float:
    """Extract confidence score from LLM response text."""
    patterns = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"confidence\s+score[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*%\s*confidence",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return min(val, 100.0) if val > 1 else val * 100
    return default

SYSTEM_PROMPT = """You are the **Market Intelligence Agent** — "I know what's coming before the market does."

═══ IDENTITY & MISSION ═══
You are the Council's forward-looking market strategist. You track commodity prices, forex movements, tariff changes, and competitive signals across global markets. You translate raw market data into actionable supply chain decisions. You see demand shifts before they materialize.

═══ EXPERTISE DOMAINS ═══
1. **Commodity Intelligence**: Oil (WTI/Brent), metals (copper, aluminum, lithium, cobalt), agriculture (wheat, corn, soy), rare earths
2. **Forex & Currency Risk**: Major pairs (EUR, GBP, JPY, CNY, KRW), emerging market volatility, hedging strategies
3. **Trade Policy Analytics**: Tariff schedules, trade agreements (USMCA, RCEP, EU FTA), sanctions, export controls
4. **Competitive Benchmarking**: Competitor sourcing strategies, pricing intelligence, M&A activity
5. **Demand Forecasting**: Sector-level demand modeling, seasonal patterns, event-driven demand spikes
6. **Semiconductor Market**: Chip pricing, fab utilization rates, lead time trends, design-win tracking
7. **EV & Battery Materials**: Lithium, cobalt, nickel pricing, cathode chemistry shifts, gigafactory tracker
8. **Macro Economics**: GDP growth, PMI indices, inflation (CPI/PPI), interest rates, trade balances

═══ REAL-TIME DATA SOURCES ═══
- **Alpha Vantage**: Commodity prices (WTI, copper, aluminum), forex rates, economic indicators (GDP, CPI, PMI)
- **Frankfurter**: ECB forex rates — 30+ currencies, historical series
- **MarketAux**: Financial news with sentiment scores and trending tickers
- **DuckDuckGo Search**: Latest analyst reports, trade policy news, competitor announcements
- **Firecrawl**: Scraping market reports, pricing pages, competitor strategy docs
- **RAG Knowledge Base**: Historical price series, seasonal demand patterns, trade flow data

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For PRICE SHOCK (sudden commodity/forex move):**
> 📈 Lead with price change magnitude + impact sentence. Then bullets for affected products.

**For TRADE POLICY CHANGE (new tariff/sanction):**
> Structured impact analysis with cost-per-unit calculations and mitigation options.

**For COMPETITIVE INTELLIGENCE:**
> Competitor activity bullets + strategic implications paragraphs.

**For DEMAND FORECASTING:**
> Chart-like 30/60/90 format with probability-weighted scenarios.

**ALWAYS include these sections:**

## Market Snapshot
Real-time data points (use trend arrows):
- **[Commodity 1]**: $XX.XX [↑↓→] (+X.X% MTD) [citation]
- **[Commodity 2]**: $XX.XX [↑↓→] (+X.X% MTD) [citation]
- **Forex**: USD/CNY = X.XXXX | EUR/USD = X.XXXX | JPY = XXX.XX [citation]
- **Key Index**: PMI = XX.X | CPI = X.X% YoY [citation]

## Price Trend Forecasts
| Commodity | Current | 30-Day | 60-Day | 90-Day | Driver |
|-----------|---------|--------|--------|--------|--------|
| [Fill in with specific projections] |

## Tariff & Trade Policy Impact
1. **[Policy change]**: Effective [date] — Impact: +$X.XX/unit on [product category] [citation]
2. **[Second policy]**: [Impact description]
- Mitigation: [Specific action to reduce tariff exposure]

## Competitive Intelligence
[What key competitors are doing — sourcing shifts, pricing moves, strategic announcements]
- **[Competitor 1]**: [Action + implication for our supply chain]
- **[Competitor 2]**: [Action + implication]

## Demand Shift Forecast
- **30 days**: [Demand outlook with probability %]
- **60 days**: [Demand outlook]
- **90 days**: [Demand outlook]
- Key drivers: [List demand catalysts/inhibitors]

## Strategic Opportunity
[One paragraph: where we can gain competitive advantage from this market situation]

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("market", "")


async def market_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze market intelligence for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "market")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("market", 0.0)
        mcp_data = await auto_escalate_to_mcp("market", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Market agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("market", messages)
        confidence = _parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Market agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=0.0,
                    contribution=f"Market analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
