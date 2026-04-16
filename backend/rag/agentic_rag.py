"""Agentic (Corrective) RAG pipeline for SupplyChainGPT Council.

Implements a full Corrective RAG loop:
  1. retrieve() → top_k chunks via hybrid search
  2. critique_step() → LLM grades each chunk's relevance (1-10)
  3. self_reflection() → if avg confidence < threshold, re-retrieve with
     expanded query or escalate to MCP tools
  4. recency_weighting → boost documents < N days old
  5. vector_drift_detection → stub for detecting embedding drift

Returns: context string + sources + confidence_score
"""

import logging
import time
from typing import Optional

from backend.rag.base_rag import BaseRAG
from backend.rag.rag_config import (
    CRITIQUE_TOP_K,
    CRITIQUE_LLM_AGENT,
    SELF_REFLECTION_THRESHOLD,
    MAX_RETRIEVAL_LOOPS,
    VECTOR_DRIFT_THRESHOLD,
    get_agent_profile,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Critique prompt template
# ---------------------------------------------------------------------------
CRITIQUE_PROMPT = """You are a relevance judge for supply chain document retrieval.
Given the following query and a retrieved document chunk, rate the relevance on a scale of 1-10.

Query: {query}

Document Chunk:
{chunk_content}

Respond with ONLY a single integer from 1 to 10 representing the relevance score.
Do not include any other text."""

SELF_REFLECTION_PROMPT = """You are a self-reflection agent for a RAG pipeline.
Given the original query and the average relevance score of retrieved documents,
decide if the retrieval was sufficient.

Query: {query}
Average relevance score: {avg_score}/10
Number of relevant chunks (score >= 6): {relevant_count}/{total_count}

If the average score is below 7, suggest an expanded search query that might retrieve
better results. If the retrieval is sufficient, respond with "SUFFICIENT".

Expanded query (or SUFFICIENT):"""


class AgenticRAG(BaseRAG):
    """Corrective RAG with critique, self-reflection, and MCP escalation.

    Inherits from BaseRAG and adds:
    - LLM-based relevance grading (critique_step)
    - Self-reflection loop: re-retrieve if confidence < threshold
    - MCP tool escalation when RAG fails
    - Vector drift detection stub
    """

    def __init__(self, agent_name: str, collection: Optional[str] = None):
        super().__init__(agent_name, collection)
        self._drift_baseline = None  # stub for vector drift detection

    # ------------------------------------------------------------------
    # Step 1: Retrieve (inherited from BaseRAG, overridden for logging)
    # ------------------------------------------------------------------
    async def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """Retrieve top_k chunks via hybrid search with recency weighting."""
        top_k = top_k or CRITIQUE_TOP_K
        logger.info(f"[AgenticRAG:{self.agent_name}] Retrieving top {top_k} for: {query[:80]}...")
        results = await super().retrieve(query, top_k=top_k)
        logger.info(f"[AgenticRAG:{self.agent_name}] Retrieved {len(results)} chunks")
        return results

    # ------------------------------------------------------------------
    # Step 2: Critique – LLM grades each chunk's relevance
    # ------------------------------------------------------------------
    async def critique_step(self, query: str, results: list[dict]) -> list[dict]:
        """Grade each retrieved chunk's relevance using LLM (1-10 scale).

        Adds 'critique_score' and 'is_relevant' (score >= 6) to each result dict.
        """
        if not results:
            return results

        graded = []
        for r in results:
            score = await self._grade_chunk(query, r.get("content", ""))
            r["critique_score"] = score
            r["is_relevant"] = score >= 6
            graded.append(r)

        relevant_count = sum(1 for r in graded if r.get("is_relevant"))
        avg_score = sum(r.get("critique_score", 0) for r in graded) / max(len(graded), 1)
        logger.info(
            f"[AgenticRAG:{self.agent_name}] Critique: avg={avg_score:.1f}, "
            f"relevant={relevant_count}/{len(graded)}"
        )
        return graded

    async def _grade_chunk(self, query: str, chunk_content: str) -> int:
        """Use LLM to grade a single chunk's relevance to the query."""
        try:
            from backend.llm.router import llm_router
            prompt = CRITIQUE_PROMPT.format(query=query, chunk_content=chunk_content[:2000])
            messages = [
                {"role": "system", "content": "You are a precise relevance judge. Output ONLY a single integer 1-10."},
                {"role": "user", "content": prompt},
            ]
            response, _ = await llm_router.invoke_with_fallback(CRITIQUE_LLM_AGENT, messages)
            # Parse integer from response
            text = response.content.strip()
            # Extract first integer found
            for word in text.split():
                try:
                    score = int(word)
                    return max(1, min(10, score))
                except ValueError:
                    continue
            # Fallback: try to extract any digit
            import re
            match = re.search(r'\d+', text)
            if match:
                return max(1, min(10, int(match.group())))
            return 5  # default middle score if parsing fails
        except Exception as e:
            logger.warning(f"[AgenticRAG:{self.agent_name}] Critique LLM failed: {e}")
            return 5  # neutral score on failure

    # ------------------------------------------------------------------
    # Step 3: Self-reflection – re-retrieve or escalate if confidence low
    # ------------------------------------------------------------------
    async def self_reflection(self, query: str, graded_results: list[dict]) -> dict:
        """Evaluate retrieval quality. If confidence < threshold, re-retrieve
        with expanded query or escalate to MCP tools.

        Returns dict with:
          - action: "accept" | "re_retrieve" | "escalate_mcp"
          - expanded_query: str (if re_retrieve)
          - confidence: float (0-1)
          - mcp_tool: str (if escalate)
        """
        if not graded_results:
            return {
                "action": "escalate_mcp",
                "expanded_query": query,
                "confidence": 0.0,
                "mcp_tool": self.profile.get("mcp_escalation_tools", ["rag_query"])[0],
            }

        avg_score = sum(r.get("critique_score", 0) for r in graded_results) / len(graded_results)
        confidence = avg_score / 10.0
        relevant_count = sum(1 for r in graded_results if r.get("is_relevant"))

        # Sufficient confidence
        if confidence >= SELF_REFLECTION_THRESHOLD:
            logger.info(f"[AgenticRAG:{self.agent_name}] Self-reflection: ACCEPT (confidence={confidence:.2f})")
            return {
                "action": "accept",
                "expanded_query": None,
                "confidence": confidence,
                "mcp_tool": None,
            }

        # Low confidence – try to expand query
        expanded_query = await self._generate_expanded_query(query, avg_score, relevant_count, len(graded_results))

        if expanded_query and expanded_query != "SUFFICIENT":
            logger.info(
                f"[AgenticRAG:{self.agent_name}] Self-reflection: RE-RETRIEVE "
                f"(confidence={confidence:.2f}, expanded_query={expanded_query[:80]})"
            )
            return {
                "action": "re_retrieve",
                "expanded_query": expanded_query,
                "confidence": confidence,
                "mcp_tool": None,
            }

        # Still insufficient – escalate to MCP
        mcp_tool = self.profile.get("mcp_escalation_tools", ["rag_query"])[0]
        logger.info(
            f"[AgenticRAG:{self.agent_name}] Self-reflection: ESCALATE to MCP "
            f"(confidence={confidence:.2f}, tool={mcp_tool})"
        )
        return {
            "action": "escalate_mcp",
            "expanded_query": query,
            "confidence": confidence,
            "mcp_tool": mcp_tool,
        }

    async def _generate_expanded_query(self, query: str, avg_score: float, relevant_count: int, total_count: int) -> Optional[str]:
        """Ask LLM to generate an expanded search query."""
        try:
            from backend.llm.router import llm_router
            prompt = SELF_REFLECTION_PROMPT.format(
                query=query,
                avg_score=f"{avg_score:.1f}",
                relevant_count=relevant_count,
                total_count=total_count,
            )
            messages = [
                {"role": "system", "content": "You generate expanded search queries for document retrieval."},
                {"role": "user", "content": prompt},
            ]
            response, _ = await llm_router.invoke_with_fallback(CRITIQUE_LLM_AGENT, messages)
            return response.content.strip()
        except Exception as e:
            logger.warning(f"[AgenticRAG:{self.agent_name}] Expanded query generation failed: {e}")
            return None

    # ------------------------------------------------------------------
    # MCP escalation
    # ------------------------------------------------------------------
    async def _escalate_to_mcp(self, query: str, tool_name: str) -> list[dict]:
        """Call an MCP tool as fallback when RAG confidence is too low."""
        try:
            from backend.mcp.registry import invoke_tool
            result = await invoke_tool(tool_name, {"query": query})
            # Normalize MCP result to RAG result format
            if isinstance(result, dict):
                content = result.get("content") or result.get("answer") or str(result)
                return [{"content": content, "metadata": {"source": f"mcp:{tool_name}"}, "score": 0.5, "from_mcp": True}]
            elif isinstance(result, list):
                return [
                    {"content": r.get("content", str(r)), "metadata": {"source": f"mcp:{tool_name}"}, "score": 0.5, "from_mcp": True}
                    for r in result[:5]
                ]
            return [{"content": str(result), "metadata": {"source": f"mcp:{tool_name}"}, "score": 0.5, "from_mcp": True}]
        except Exception as e:
            logger.error(f"[AgenticRAG:{self.agent_name}] MCP escalation to {tool_name} failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Full pipeline: retrieve → critique → reflect → (re-retrieve | escalate)
    # ------------------------------------------------------------------
    async def run(self, query: str, top_k: Optional[int] = None) -> dict:
        """Execute the full Agentic RAG pipeline.

        Returns:
            context: str – formatted context for LLM
            sources: list[dict] – citation info
            confidence: float – 0-1 confidence score
            loops_used: int – number of retrieval loops
            escalated: bool – whether MCP was used
            chunks_retrieved: int
        """
        start = time.time()
        top_k = top_k or self.top_k
        all_results = []
        loops_used = 0
        escalated = False
        current_query = query
        graded = []

        for loop in range(MAX_RETRIEVAL_LOOPS + 1):
            loops_used = loop + 1

            # Step 1: Retrieve
            results = await self.retrieve(current_query, top_k=top_k)
            if not results and loop == 0:
                # No results at all – escalate immediately
                mcp_tool = self.profile.get("mcp_escalation_tools", ["rag_query"])[0]
                mcp_results = await self._escalate_to_mcp(query, mcp_tool)
                all_results = mcp_results
                escalated = True
                break

            # Step 2: Critique
            graded = await self.critique_step(current_query, results)

            # Step 3: Self-reflection
            reflection = await self.self_reflection(current_query, graded)

            if reflection["action"] == "accept":
                all_results = graded
                break
            elif reflection["action"] == "re_retrieve":
                current_query = reflection["expanded_query"]
                # Keep relevant results from previous loop
                all_results = [r for r in graded if r.get("is_relevant")]
                logger.info(f"[AgenticRAG:{self.agent_name}] Loop {loop+1}: re-retrieving with expanded query")
                continue
            elif reflection["action"] == "escalate_mcp":
                # Keep relevant results + add MCP data
                all_results = [r for r in graded if r.get("is_relevant")]
                mcp_results = await self._escalate_to_mcp(query, reflection["mcp_tool"])
                all_results.extend(mcp_results)
                escalated = True
                break

        # If we exhausted loops without accept, use what we have
        if not all_results:
            all_results = graded if graded else []

        # Filter to relevant only for final context
        relevant = [r for r in all_results if r.get("is_relevant", True)]
        if not relevant:
            relevant = all_results  # use everything if nothing scored relevant

        # Build context
        ctx = self.build_prompt_context(relevant)

        # Compute final confidence
        scores = [r.get("critique_score", 5) for r in relevant if "critique_score" in r]
        confidence = (sum(scores) / max(len(scores), 1)) / 10.0 if scores else 0.5

        latency = int((time.time() - start) * 1000)
        logger.info(
            f"[AgenticRAG:{self.agent_name}] Pipeline complete: "
            f"confidence={confidence:.2f}, loops={loops_used}, "
            f"chunks={len(relevant)}, escalated={escalated}, latency={latency}ms"
        )

        return {
            "context": ctx["context"],
            "sources": ctx["citations"],
            "confidence": round(confidence, 3),
            "loops_used": loops_used,
            "escalated": escalated,
            "chunks_retrieved": len(relevant),
            "latency_ms": latency,
        }

    # ------------------------------------------------------------------
    # Vector drift detection (stub)
    # ------------------------------------------------------------------
    async def detect_vector_drift(self, query: str) -> dict:
        """Stub: Detect if query embeddings have drifted from the indexed baseline.

        In production, this would:
        1. Compute the centroid of the top-K retrieved embeddings
        2. Compare against a stored baseline centroid
        3. Alert if cosine distance > VECTOR_DRIFT_THRESHOLD

        Returns a diagnostic dict.
        """
        try:
            query_embedding = await embed_query(query)
            # Placeholder: compare against a stored baseline
            if self._drift_baseline is None:
                self._drift_baseline = query_embedding
                return {"drift_detected": False, "distance": 0.0, "status": "baseline_set"}

            # Cosine distance between current query embedding and baseline
            import numpy as np
            a = np.array(query_embedding)
            b = np.array(self._drift_baseline)
            cosine_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
            distance = 1.0 - cosine_sim

            drift_detected = distance > VECTOR_DRIFT_THRESHOLD
            if drift_detected:
                logger.warning(
                    f"[AgenticRAG:{self.agent_name}] Vector drift detected: "
                    f"distance={distance:.4f} > threshold={VECTOR_DRIFT_THRESHOLD}"
                )

            return {
                "drift_detected": drift_detected,
                "distance": round(float(distance), 4),
                "threshold": VECTOR_DRIFT_THRESHOLD,
                "status": "drift_alert" if drift_detected else "stable",
            }
        except Exception as e:
            logger.warning(f"[AgenticRAG:{self.agent_name}] Drift detection failed: {e}")
            return {"drift_detected": False, "distance": 0.0, "status": "error", "error": str(e)}
