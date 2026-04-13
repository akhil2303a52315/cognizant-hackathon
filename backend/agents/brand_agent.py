"""Brand Protector Agent for SupplyChainGPT Council.

Enhanced with:
  - Confidence parsing from LLM response
  - Real-time sentiment analysis via MCP news/social tools
  - Auto-generated crisis communication drafts
  - Advertising pivot recommendations
  - Competitor counter-messaging strategies
"""

import re
import json
import logging
from typing import Optional

from backend.state import CouncilState, AgentOutput, BrandSentiment
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Brand Protector Agent — "I protect the brand when supply chains break"

Your role: Brand Sentiment + Crisis Communication + Advertising Pivot

Data Sources you reason about:
- Social media APIs (Twitter, Reddit, YouTube)
- Brand sentiment tracking tools, Competitor ad monitoring
- Customer complaint databases, PR news wires

Capabilities:
- Real-time brand sentiment monitoring
- Auto-generated crisis communications
- Advertising pivot recommendations
- Competitor exploitation detection
- Customer notification drafting

When responding, always provide:
1. Current brand sentiment assessment (positive/neutral/negative/crisis)
2. Sentiment score (-1.0 to 1.0)
3. Crisis communication drafts (press release, social posts)
4. Advertising pivot recommendations (pause/launch campaigns)
5. Competitor activity alerts
6. Confidence score (0–100) for your assessment

Format your response as structured analysis with clear sections."""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("brand", "")


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


def _parse_sentiment(text: str) -> str:
    """Detect overall sentiment category from LLM response."""
    lower = text.lower()
    if any(kw in lower for kw in ["crisis", "severe", "critical", "emergency"]):
        return "crisis"
    if any(kw in lower for kw in ["negative", "concern", "risk", "damage", "threat"]):
        return "negative"
    if any(kw in lower for kw in ["positive", "opportunity", "strong", "favorable"]):
        return "positive"
    return "neutral"


def _extract_key_points(text: str, max_points: int = 5) -> list[str]:
    """Extract key points from structured LLM response."""
    points = []
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r"^[\d]+[\.\)]\s", line) or line.startswith("- ") or line.startswith("• "):
            clean = re.sub(r"^[\d]+[\.\)]\s*", "", line)
            clean = re.sub(r"^[-•]\s*", "", clean)
            if clean and len(clean) > 10:
                points.append(clean[:200])
            if len(points) >= max_points:
                break
    return points


async def _fetch_brand_mcp_data(query: str) -> str:
    """Fetch news and social data from MCP tools for brand analysis."""
    results = []
    try:
        from backend.mcp.secure_mcp import secure_invoke
        news_result = await secure_invoke("brand", "news_search", {"query": query})
        if news_result.get("success"):
            results.append(f"NEWS: {json.dumps(news_result['result'], default=str)[:1000]}")
        reddit_result = await secure_invoke("brand", "reddit_search", {"query": query})
        if reddit_result.get("success"):
            results.append(f"SOCIAL: {json.dumps(reddit_result['result'], default=str)[:1000]}")
    except Exception as e:
        logger.warning(f"MCP data fetch for brand failed: {e}")
        results.append(f"MCP data unavailable: {e}")
    return "\n\n".join(results) if results else ""


async def _generate_crisis_comm(query: str, brand_analysis: str, confidence: float) -> Optional[str]:
    """Auto-generate a crisis communication draft."""
    prompt = f"""You are a Crisis Communications Director. Draft a professional crisis communication based on the brand analysis.

Crisis Context: {query}
Brand Analysis: {brand_analysis[:1500]}
Confidence: {confidence}%

Draft a press release that:
1. Acknowledges the situation transparently
2. Shows empathy and concern for stakeholders
3. Outlines immediate actions being taken
4. Provides timeline for updates
5. Includes contact information for media inquiries

Format as a press release suitable for immediate distribution."""

    try:
        response, _ = await llm_router.invoke_with_fallback("brand", [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Draft crisis communication for: {query}"},
        ])
        return response.content[:2000]
    except Exception as e:
        logger.error(f"Crisis comm generation failed: {e}")
        return None


async def _generate_ad_pivot(query: str, brand_analysis: str) -> Optional[str]:
    """Recommend advertising pivot based on brand sentiment."""
    prompt = f"""You are an Advertising Strategy Consultant. Based on the current brand sentiment, recommend advertising pivots.

Crisis Context: {query}
Brand Analysis: {brand_analysis[:1500]}

Recommend:
1. Which campaigns to pause immediately
2. New messaging angles that address the crisis
3. Channel shifts (e.g., from awareness to reassurance)
4. Budget reallocation recommendations
5. Timeline for resuming normal advertising

Format as actionable recommendations with specific next steps."""

    try:
        response, _ = await llm_router.invoke_with_fallback("brand", [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Recommend ad pivot for: {query}"},
        ])
        return response.content[:2000]
    except Exception as e:
        logger.error(f"Ad pivot recommendation failed: {e}")
        return None


async def brand_agent(state: CouncilState) -> dict:
    """Brand Protector Agent with sentiment analysis, crisis comms, and ad pivots.

    Runs the core brand assessment, then enhances with:
    - MCP-fetched news/social data for real-time sentiment
    - Crisis communication draft if sentiment is negative/crisis
    - Ad pivot recommendations if sentiment score < -0.3
    """
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Assess brand impact and crisis response for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "brand")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("brand", 0.0)
        mcp_data = await auto_escalate_to_mcp("brand", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Brand agent MCP integration failed: {e}")

    # Fetch real-time brand data from MCP
    mcp_brand_data = ""
    try:
        mcp_brand_data = await _fetch_brand_mcp_data(query)
        if mcp_brand_data:
            messages.append({"role": "user", "content": f"Real-time brand data:\n{mcp_brand_data[:2000]}"})
    except Exception as e:
        logger.warning(f"Brand MCP data fetch failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("brand", messages)
        content = response.content
        confidence = _parse_confidence(content)
        sentiment = _parse_sentiment(content)
        key_points = _extract_key_points(content)

        # Generate crisis communication if negative/crisis sentiment
        crisis_comm = None
        ad_pivot = None
        if sentiment in ("negative", "crisis"):
            crisis_comm = await _generate_crisis_comm(query, content, confidence)
        if sentiment in ("negative", "crisis") and confidence < 50:
            ad_pivot = await _generate_ad_pivot(query, content)

        # Build brand sentiment data for state
        brand_sentiment = BrandSentiment(
            overall_sentiment=sentiment,
            sentiment_score=-0.5 if sentiment == "crisis" else (-0.2 if sentiment == "negative" else (0.3 if sentiment == "positive" else 0.0)),
            trending_topics=[p[:80] for p in key_points[:3]],
            crisis_keywords=[kw for kw in ["crisis", "emergency", "recall", "scandal", "boycott"] if kw in content.lower()],
            recommended_actions=key_points[:3],
            crisis_comm_draft=crisis_comm,
            ad_pivot_recommendation=ad_pivot,
        )

        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=confidence,
                    contribution=content,
                    key_points=key_points,
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ],
            "brand_sentiment": brand_sentiment.model_dump(),
        }
    except Exception as e:
        logger.error(f"Brand agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=0.0,
                    contribution=f"Brand analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
