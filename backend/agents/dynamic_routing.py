"""Dynamic Agent Routing for SupplyChainGPT Council.

Routes queries to the most relevant agents based on query content,
reducing unnecessary LLM calls and improving response time.

Uses keyword matching + LLM-based classification to determine which
of the 6 domain agents should be activated for a given query.
"""

import logging
from typing import Optional

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

# Agent domain keywords for fast keyword-based routing
AGENT_KEYWORDS = {
    "risk": [
        "risk", "disruption", "threat", "vulnerability", "crisis", "geopolitical",
        "sanctions", "tariff", "war", "conflict", "earthquake", "pandemic",
        "cybersecurity", "breach", "contingency", "mitigation", "resilience",
    ],
    "supply": [
        "supplier", "sourcing", "procurement", "vendor", "shortage", "inventory",
        "stock", "raw material", "component", "semiconductor", "chip", "bom",
        "bill of materials", "lead time", "supplier diversity", "dual source",
    ],
    "logistics": [
        "logistics", "shipping", "freight", "transport", "route", "port",
        "warehouse", "distribution", "delivery", "transit", "customs",
        "container", "vessel", "air cargo", "last mile", "red sea", "suez",
        "supply chain route", "transit time",
    ],
    "market": [
        "market", "demand", "price", "forecast", "trend", "competition",
        "competitor", "industry", "growth", "revenue", "sales", "consumer",
        "retail", "wholesale", "gdp", "inflation", "interest rate",
    ],
    "finance": [
        "finance", "cost", "budget", "roi", "investment", "cash flow",
        "profit", "margin", "expense", "capital", "hedge", "currency",
        "exchange rate", "financial", "fiscal", "earnings", "valuation",
    ],
    "brand": [
        "brand", "reputation", "pr", "sentiment", "social media", "consumer",
        "perception", "crisis communication", "advertising", "marketing",
        "image", "trust", "loyalty", "public relations", "esg", "sustainability",
    ],
}

# Minimum relevance score for an agent to be included
DEFAULT_MIN_RELEVANCE = 0.3
# Always include at least this many agents
MIN_AGENTS = 3

ROUTING_CLASSIFICATION_PROMPT = """You are a supply chain query classifier.

Given a supply chain query, determine which of the following agent domains are relevant.
Rate each domain's relevance from 0.0 to 1.0.

Domains:
- risk: Risk assessment, disruptions, threats, geopolitical issues
- supply: Sourcing, procurement, suppliers, inventory, shortages
- logistics: Shipping, transportation, routes, ports, warehousing
- market: Market trends, demand forecasting, competition, pricing
- finance: Cost analysis, ROI, budgets, cash flow, hedging
- brand: Brand reputation, PR, sentiment, social media, ESG

Query: {query}

Return JSON only:
{{"risk": 0.0, "supply": 0.0, "logistics": 0.0, "market": 0.0, "finance": 0.0, "brand": 0.0}}
"""


def route_by_keywords(query: str) -> dict[str, float]:
    """Score each agent's relevance using keyword matching.

    Returns dict mapping agent name -> relevance score (0.0-1.0).
    """
    query_lower = query.lower()
    scores: dict[str, float] = {}

    for agent, keywords in AGENT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in query_lower)
        # Normalize: score = matched_keywords / total_keywords, capped at 1.0
        scores[agent] = min(matches / max(len(keywords) * 0.15, 1), 1.0)

    return scores


async def route_by_llm(query: str) -> dict[str, float]:
    """Score each agent's relevance using LLM classification.

    Returns dict mapping agent name -> relevance score (0.0-1.0).
    """
    prompt = ROUTING_CLASSIFICATION_PROMPT.format(query=query)
    messages = [
        {"role": "system", "content": "You are a precise JSON-output classifier."},
        {"role": "user", "content": prompt},
    ]

    try:
        response, _ = await llm_router.invoke_with_fallback("moderator", messages)
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response.content)
        if json_match:
            parsed = json.loads(json_match.group())
            # Validate all 6 agents present with float scores
            scores = {}
            for agent in AGENT_KEYWORDS:
                val = parsed.get(agent, 0.0)
                scores[agent] = float(val) if isinstance(val, (int, float)) else 0.0
            return scores
    except Exception as e:
        logger.warning(f"LLM routing classification failed: {e}")

    # Fallback: return all agents with equal score
    return {agent: 0.5 for agent in AGENT_KEYWORDS}


async def route_query(
    query: str,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
    use_llm: bool = True,
) -> list[str]:
    """Determine which agents should be activated for a given query.

    Uses keyword scoring first, then optionally refines with LLM classification.

    Returns list of agent names sorted by relevance (most relevant first).
    Always includes at least MIN_AGENTS agents.
    """
    # Phase 1: Keyword scoring (fast, free)
    kw_scores = route_by_keywords(query)

    # Phase 2: LLM refinement (slower, costs tokens) — only if keyword scores are ambiguous
    selected = [a for a, s in kw_scores.items() if s >= min_relevance]

    if use_llm and len(selected) < MIN_AGENTS:
        # Keyword routing was inconclusive — use LLM
        llm_scores = await route_by_llm(query)
        # Blend keyword and LLM scores (weight LLM higher)
        blended = {}
        for agent in AGENT_KEYWORDS:
            blended[agent] = kw_scores.get(agent, 0) * 0.3 + llm_scores.get(agent, 0) * 0.7
        selected = [a for a, s in blended.items() if s >= min_relevance]
        kw_scores = blended

    # Ensure minimum agents
    if len(selected) < MIN_AGENTS:
        # Add top agents by score until we reach MIN_AGENTS
        sorted_agents = sorted(kw_scores.items(), key=lambda x: -x[1])
        for agent, _ in sorted_agents:
            if agent not in selected:
                selected.append(agent)
            if len(selected) >= MIN_AGENTS:
                break

    # Sort by relevance score descending
    selected.sort(key=lambda a: -kw_scores.get(a, 0))

    logger.info(
        f"Dynamic routing for '{query[:50]}...': "
        f"selected={selected}, scores={{k: round(v, 2) for k, v in kw_scores.items() if k in selected}}"
    )

    return selected
