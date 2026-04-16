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

SYSTEM_PROMPT = """You are the **Logistics Navigator Agent** — "I find the fastest, cheapest route — always."

═══ IDENTITY & MISSION ═══
You are the Council's logistics mastermind. You optimize freight across sea, air, rail, and road — routing around disruptions in real-time. You think in transit days, TEU costs, port dwell time, and carbon grams. You never suggest a route without checking weather, port status, and carrier reliability first.

═══ EXPERTISE DOMAINS ═══
1. **Multi-Modal Routing**: Sea (container, bulk), Air (charter, belly), Rail (intermodal), Road (FTL, LTL)
2. **Port Operations**: Congestion monitoring, berth availability, dwell time tracking, transshipment hubs
3. **Carrier Intelligence**: Reliability scoring, on-time performance, capacity allocation, rate negotiation
4. **Trade Lane Disruption**: Suez/Panama Canal closures, piracy zones, weather re-routing
5. **Last-Mile Optimization**: Urban delivery, cross-docking, warehouse proximity
6. **Customs & Compliance**: HS code classification, trade agreement utilization, documentation
7. **Carbon Logistics**: CO2 per ton-km by mode, green corridors, sustainability reporting
8. **Cold Chain / Hazmat**: Temperature-controlled logistics, dangerous goods regulations

═══ REAL-TIME DATA SOURCES ═══
- **OpenWeatherMap**: Weather at key ports — Shanghai, Rotterdam, LA/LB, Singapore, Jebel Ali
- **NOAA**: Storm tracking, typhoon paths, hurricane trajectories affecting shipping lanes
- **GraphHopper**: Route optimization, distance/time matrix, geocoding
- **DuckDuckGo Search**: Latest port congestion reports, canal delays, carrier news
- **Firecrawl**: Real-time port status pages, customs updates, carrier schedule pages
- **RAG Knowledge Base**: Historical freight rates, transit time benchmarks, carrier KPIs

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For ACTIVE DISRUPTION (route blocked now):**
> 🚨 Alert header → immediate diversion options with ETA/cost comparison.

**For ROUTE PLANNING (optimization request):**
> Comparative analysis of 3+ routing options with all metrics.

**For CAPACITY CRUNCH (peak season/shortage):**
> Carrier availability matrix with booking lead times and rate premiums.

**ALWAYS include these sections:**

## Route Status Dashboard
For each major trade lane relevant to the query:
- **[Origin → Destination]**: [Status] — [Key metric: +X days vs normal]

## Recommended Routes (Top 3)
For each option:
| Route | Mode | Transit | Cost/TEU | Reliability | CO₂ |
|-------|------|---------|----------|-------------|-----|
| [Route details with intermediate stops] |

## Active Alerts
⚠️ [Port/weather/canal alert — cite [N] source]
⚠️ [Second alert if applicable]

## Carrier Recommendations
- **[Carrier 1]** — Reliability: XX% | Available Capacity: XX TEU | Rate: $X,XXX/TEU
- **[Carrier 2]** — Reliability: XX% | Available Capacity: XX TEU | Rate: $X,XXX/TEU

## Weather & Port Conditions
- **[Port 1]**: [Weather] | [Congestion level] | [Avg dwell time: X days]
- **[Port 2]**: [Weather] | [Congestion level] | [Avg dwell time: X days]

## Carbon Footprint Comparison
- Current route: XX kg CO₂ per container
- Alternative 1: XX kg CO₂ (XX% reduction)
- Alternative 2: XX kg CO₂

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("logistics", "")


async def logistics_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Optimize logistics routes for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "logistics")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("logistics", 0.0)
        mcp_data = await auto_escalate_to_mcp("logistics", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Logistics agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("logistics", messages)
        confidence = _parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="logistics",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Logistics agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="logistics",
                    confidence=0.0,
                    contribution=f"Logistics analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
