"""Brand Agent Enhancement for SupplyChainGPT Council.

Extends the Brand Protector Agent with:
  - Real-time sentiment analysis (using RAG + MCP news/social tools)
  - Auto-generated crisis communication drafts
  - Advertising pivot recommendations
  - Competitor counter-messaging strategies

Integrates with:
  - Day 3 RAG for historical brand/sentiment data
  - Day 4 MCP tools (reddit_search, social_sentiment, news_search, firecrawl)
  - Day 5 Debate Engine for brand impact assessment
"""

import json
import logging
from typing import Optional

from backend.state import CouncilState, BrandSentiment
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SENTIMENT_ANALYSIS_PROMPT = """You are a Brand Sentiment Analyst. Analyze the following data and provide a structured assessment.

News & Social Data:
{news_data}

Historical Context (from RAG):
{rag_context}

Query: {query}

Provide your analysis as JSON:
{{
    "overall_sentiment": "positive|neutral|negative|crisis",
    "sentiment_score": <float -1.0 to 1.0>,
    "trending_topics": [<list of strings>],
    "crisis_keywords": [<list of detected crisis keywords>],
    "recommended_actions": [<list of actionable recommendations>]
}}
"""

CRISIS_COMM_PROMPT = """You are a Crisis Communications Director. Draft a crisis communication based on the sentiment analysis.

Crisis Context: {query}
Sentiment Analysis: {sentiment_data}
Company Position: {company_position}

Draft a professional crisis communication that:
1. Acknowledges the situation transparently
2. Shows empathy and concern for stakeholders
3. Outlines immediate actions being taken
4. Provides timeline for updates
5. Includes contact information for media inquiries

Format as a press release suitable for immediate distribution.
"""

AD_PIVOT_PROMPT = """You are an Advertising Strategy Consultant. Based on the current brand sentiment, recommend advertising pivots.

Current Sentiment: {sentiment_data}
Crisis Context: {query}
Current Ad Strategy: {current_strategy}

Recommend:
1. Which campaigns to pause immediately
2. New messaging angles that address the crisis
3. Channel shifts (e.g., from awareness to reassurance)
4. Budget reallocation recommendations
5. Timeline for resuming normal advertising

Format as actionable recommendations with specific next steps.
"""

COMPETITOR_COUNTER_PROMPT = """You are a Competitive Intelligence Analyst. Analyze competitor activity and recommend counter-messaging.

Competitor Data: {competitor_data}
Crisis Context: {query}
Our Sentiment: {sentiment_data}

Recommend:
1. Competitor messaging vulnerabilities
2. Counter-messaging strategies
3. Market share opportunities during the crisis
4. Defensive brand positioning
5. Proactive communication angles

Format as strategic recommendations with specific talking points.
"""


class BrandAgentEnhancer:
    """Enhances the Brand Protector Agent with real-time sentiment,
    crisis communications, ad pivots, and competitor counter-messaging.
    """

    async def analyze_sentiment(self, state: CouncilState) -> BrandSentiment:
        """Run real-time sentiment analysis using RAG + MCP data.

        Fetches news and social data via MCP tools, combines with
        RAG historical context, and produces a structured sentiment assessment.
        """
        query = state.get("query", "")
        context = state.get("context") or {}

        # Gather MCP data for brand agent
        news_data = await self._fetch_brand_mcp_data(query, context)
        rag_context = self._get_brand_rag_context(context)

        prompt = SENTIMENT_ANALYSIS_PROMPT.format(
            news_data=news_data[:3000],
            rag_context=rag_context[:2000],
            query=query,
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Analyze brand sentiment for: {query}"},
        ]

        try:
            response, model_used = await llm_router.invoke_with_fallback("brand", messages)
            parsed = self._parse_sentiment_json(response.content)
            return BrandSentiment(**parsed)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return BrandSentiment(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                trending_topics=[],
                crisis_keywords=[],
                recommended_actions=["Manual sentiment review recommended"],
            )

    async def generate_crisis_comm(self, state: CouncilState, sentiment: BrandSentiment) -> str:
        """Auto-generate a crisis communication draft based on sentiment analysis."""
        query = state.get("query", "")
        agent_outputs = state.get("agent_outputs", [])

        # Get brand agent's position from debate
        brand_position = ""
        for o in agent_outputs:
            if o.agent == "brand":
                brand_position = o.contribution
                break

        prompt = CRISIS_COMM_PROMPT.format(
            query=query,
            sentiment_data=sentiment.model_dump_json(),
            company_position=brand_position[:1000] or "Standard supply chain company position",
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Draft crisis communication for: {query}"},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("brand", messages)
            return response.content
        except Exception as e:
            logger.error(f"Crisis comm generation failed: {e}")
            return f"Crisis communication draft generation failed: {e}"

    async def recommend_ad_pivot(self, state: CouncilState, sentiment: BrandSentiment) -> str:
        """Recommend advertising pivot based on current sentiment."""
        query = state.get("query", "")

        prompt = AD_PIVOT_PROMPT.format(
            sentiment_data=sentiment.model_dump_json(),
            query=query,
            current_strategy="Standard brand awareness campaigns across digital channels",
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Recommend ad pivot for: {query}"},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("brand", messages)
            return response.content
        except Exception as e:
            logger.error(f"Ad pivot recommendation failed: {e}")
            return f"Ad pivot recommendation failed: {e}"

    async def competitor_counter_messaging(self, state: CouncilState, sentiment: BrandSentiment) -> str:
        """Generate competitor counter-messaging strategy."""
        query = state.get("query", "")

        # Fetch competitor data via MCP
        competitor_data = await self._fetch_competitor_data(query)

        prompt = COMPETITOR_COUNTER_PROMPT.format(
            competitor_data=competitor_data[:2000],
            query=query,
            sentiment_data=sentiment.model_dump_json(),
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Analyze competitor activity for: {query}"},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("brand", messages)
            return response.content
        except Exception as e:
            logger.error(f"Competitor counter-messaging failed: {e}")
            return f"Competitor analysis failed: {e}"

    async def run_full_enhancement(self, state: CouncilState) -> dict:
        """Run the full brand enhancement pipeline.

        Returns state update with brand_sentiment and enhanced brand data.
        """
        # 1. Sentiment analysis
        sentiment = await self.analyze_sentiment(state)

        # 2. Crisis communication (only if negative/crisis sentiment)
        crisis_comm = None
        if sentiment.overall_sentiment in ("negative", "crisis"):
            crisis_comm = await self.generate_crisis_comm(state, sentiment)
            sentiment.crisis_comm_draft = crisis_comm[:2000]

        # 3. Ad pivot recommendations
        ad_pivot = None
        if sentiment.sentiment_score < -0.3:
            ad_pivot = await self.recommend_ad_pivot(state, sentiment)
            sentiment.ad_pivot_recommendation = ad_pivot[:2000]

        # 4. Competitor counter-messaging
        competitor_msg = None
        if sentiment.overall_sentiment in ("negative", "crisis"):
            competitor_msg = await self.competitor_counter_messaging(state, sentiment)
            sentiment.competitor_activity = competitor_msg[:2000]

        return {
            "brand_sentiment": sentiment.model_dump(),
        }

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------
    async def _fetch_brand_mcp_data(self, query: str, context: dict) -> str:
        """Fetch news and social data from MCP tools for brand analysis."""
        results = []

        try:
            from backend.mcp.secure_mcp import secure_invoke

            # News search
            news_result = await secure_invoke("brand", "news_search", {"query": query})
            if news_result.get("success"):
                results.append(f"NEWS: {json.dumps(news_result['result'], default=str)[:1000]}")

            # Reddit/social sentiment
            reddit_result = await secure_invoke("brand", "reddit_search", {"query": query})
            if reddit_result.get("success"):
                results.append(f"SOCIAL: {json.dumps(reddit_result['result'], default=str)[:1000]}")

        except Exception as e:
            logger.warning(f"MCP data fetch for brand failed: {e}")
            results.append(f"MCP data unavailable: {e}")

        return "\n\n".join(results) if results else "No real-time data available."

    def _get_brand_rag_context(self, context: dict) -> str:
        """Extract brand-specific RAG context from state."""
        rag_contexts = context.get("rag_contexts") or {}
        return rag_contexts.get("brand", "")

    async def _fetch_competitor_data(self, query: str) -> str:
        """Fetch competitor intelligence via MCP Firecrawl."""
        try:
            from backend.mcp.secure_mcp import secure_invoke
            result = await secure_invoke("brand", "firecrawl_search", {
                "query": f"competitor response to {query}",
                "num_results": 5,
            })
            if result.get("success"):
                return json.dumps(result["result"], default=str)[:2000]
        except Exception as e:
            logger.warning(f"Competitor data fetch failed: {e}")

        return "No competitor data available."

    def _parse_sentiment_json(self, text: str) -> dict:
        """Parse sentiment analysis JSON from LLM response."""
        try:
            # Try to extract JSON from response
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            elif "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
            else:
                raise ValueError("No JSON found in response")

            parsed = json.loads(json_str)

            # Validate required fields
            return {
                "overall_sentiment": parsed.get("overall_sentiment", "neutral"),
                "sentiment_score": float(parsed.get("sentiment_score", 0.0)),
                "trending_topics": parsed.get("trending_topics", []),
                "crisis_keywords": parsed.get("crisis_keywords", []),
                "recommended_actions": parsed.get("recommended_actions", []),
            }
        except Exception as e:
            logger.warning(f"Sentiment JSON parse failed: {e}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "trending_topics": [],
                "crisis_keywords": [],
                "recommended_actions": ["Manual review recommended"],
            }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
brand_enhancer = BrandAgentEnhancer()
