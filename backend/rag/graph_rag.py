"""Graph RAG module for SupplyChainGPT Council.

Provides HybridCypherRetriever that combines:
  - Neo4j Cypher queries for supplier graph traversal (Tier-1/2/3)
  - Vector similarity search for semantic matching
  - Structured output with relationship context

Cypher queries cover:
  - Direct supplier lookup (Tier-1)
  - Multi-tier supplier traversal (Tier-2, Tier-3)
  - Component dependency chains
  - Supplier risk propagation
"""

import logging
from typing import Optional

from backend.rag.rag_config import NEO4J_URI, NEO4J_PASSWORD

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entity extraction (upgraded with LLM fallback)
# ---------------------------------------------------------------------------
SUPPLY_CHAIN_KEYWORDS = [
    "supplier", "company", "corp", "ltd", "inc", "components", "electronics",
    "semi", "taiwan", "vietnam", "india", "china", "chip", "pcb", "assembly",
    "manufacturing", "logistics", "shipping", "port", "route",
]


async def _extract_entities(query: str) -> list[str]:
    """Extract named entities and supply-chain keywords from query."""
    words = query.split()
    entities = []

    for word in words:
        lower = word.lower().rstrip(".,;:!?")
        if lower in SUPPLY_CHAIN_KEYWORDS:
            entities.append(lower)
        if word[0].isupper() and len(word) > 2:
            entities.append(word)

    return list(set(entities))[:8]


async def _extract_entities_with_llm(query: str) -> list[str]:
    """Use LLM to extract supplier/component entities from query."""
    try:
        from backend.llm.router import llm_router
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract supply chain entity names from the query. "
                    "Return ONLY a comma-separated list of entity names. "
                    "Include company names, component names, locations, and industry terms."
                ),
            },
            {"role": "user", "content": query},
        ]
        response, _ = await llm_router.invoke_with_fallback("supply", messages)
        entities = [e.strip() for e in response.content.split(",") if e.strip()]
        return entities[:8]
    except Exception as e:
        logger.warning(f"LLM entity extraction failed: {e}")
        return await _extract_entities(query)


# ---------------------------------------------------------------------------
# Cypher query templates for multi-tier supplier traversal
# ---------------------------------------------------------------------------
CYPHER_TIER1_SUPPLIERS = """
MATCH (s:Supplier {tier: 1})
WHERE toLower(s.name) CONTAINS toLower($name) OR toLower(s.location) CONTAINS toLower($name)
MATCH (s)-[r:SUPPLIES]->(c:Component)
RETURN s.id as supplier_id, s.name as supplier_name, s.location as location,
       s.capability_match as capability_match, s.lead_time_days as lead_time,
       type(r) as rel_type, c.id as component_id, c.name as component_name,
       r.cost_per_unit as cost_per_unit, r.moq as moq, r.lead_time_days as supply_lead_time
LIMIT 10
"""

CYPHER_TIER2_SUPPLIERS = """
MATCH (s1:Supplier {tier: 1})-[:DEPENDS_ON]->(s2:Supplier {tier: 2})
WHERE toLower(s1.name) CONTAINS toLower($name) OR toLower(s2.name) CONTAINS toLower($name)
   OR toLower(s2.location) CONTAINS toLower($name)
MATCH (s2)-[r:SUPPLIES]->(c:Component)
RETURN s1.name as tier1_supplier, s2.id as supplier_id, s2.name as supplier_name,
       s2.location as location, s2.capability_match as capability_match,
       s2.lead_time_days as lead_time, c.name as component_name,
       r.cost_per_unit as cost_per_unit
LIMIT 10
"""

CYPHER_TIER3_SUPPLIERS = """
MATCH (s1:Supplier {tier: 1})-[:DEPENDS_ON]->(s2:Supplier {tier: 2})-[:DEPENDS_ON]->(s3:Supplier {tier: 3})
WHERE toLower(s1.name) CONTAINS toLower($name) OR toLower(s3.name) CONTAINS toLower($name)
   OR toLower(s3.location) CONTAINS toLower($name)
MATCH (s3)-[r:SUPPLIES]->(c:Component)
RETURN s1.name as tier1_supplier, s2.name as tier2_supplier, s3.id as supplier_id,
       s3.name as supplier_name, s3.location as location,
       s3.capability_match as capability_match, s3.lead_time_days as lead_time,
       c.name as component_name, r.cost_per_unit as cost_per_unit
LIMIT 10
"""

CYPHER_COMPONENT_DEPENDENCY = """
MATCH (c1:Component)-[:USED_IN]->(c2:Component)
WHERE toLower(c1.name) CONTAINS toLower($name) OR toLower(c2.name) CONTAINS toLower($name)
OPTIONAL MATCH (s:Supplier)-[r:SUPPLIES]->(c1)
RETURN c1.name as component, c2.name as used_in, s.name as supplier,
       r.cost_per_unit as cost, r.lead_time_days as lead_time
LIMIT 10
"""

CYPHER_SUPPLIER_RISK_PROPAGATION = """
MATCH path = (s1:Supplier)-[:DEPENDS_ON*1..3]->(s2:Supplier)
WHERE toLower(s1.name) CONTAINS toLower($name)
RETURN s1.name as source_supplier, s2.name as dependent_supplier,
       s2.tier as tier, s2.location as location, s2.capability_match as capability,
       length(path) as dependency_depth
ORDER BY dependency_depth
LIMIT 15
"""

CYPHER_ALL_SUPPLIERS = """
MATCH (s:Supplier)-[r:SUPPLIES]->(c:Component)
RETURN s.id as supplier_id, s.name as supplier_name, s.tier as tier,
       s.location as location, s.capability_match as capability_match,
       s.lead_time_days as lead_time, c.name as component_name,
       r.cost_per_unit as cost_per_unit, r.moq as moq
LIMIT 20
"""


# ---------------------------------------------------------------------------
# HybridCypherRetriever
# ---------------------------------------------------------------------------
class HybridCypherRetriever:
    """Combines Neo4j Cypher graph traversal with vector similarity search.

    Workflow:
      1. Extract entities from query (keyword + LLM)
      2. Run tiered Cypher queries (Tier-1 → Tier-2 → Tier-3)
      3. Run component dependency and risk propagation queries
      4. Optionally combine with vector search results
      5. Return structured graph context
    """

    def __init__(self, use_llm_extraction: bool = True, combine_with_vector: bool = True):
        self.use_llm_extraction = use_llm_extraction
        self.combine_with_vector = combine_with_vector

    async def retrieve(self, query: str, top_k: int = 10) -> dict:
        """Execute hybrid Cypher + vector retrieval for a supply chain query.

        Returns:
            graph_results: dict[str, list] – results keyed by entity
            tier1/tier2/tier3: list[dict] – per-tier supplier data
            component_deps: list[dict] – component dependency chains
            risk_propagation: list[dict] – supplier risk paths
            vector_context: list[dict] – optional vector search results
            entities_found: list[str]
            query: str
        """
        # Step 1: Extract entities
        if self.use_llm_extraction:
            entities = await _extract_entities_with_llm(query)
        else:
            entities = await _extract_entities(query)

        if not entities:
            # Fallback: use full words from query
            entities = [w for w in query.split() if len(w) > 3][:5]

        # Step 2: Run tiered Cypher queries
        tier1_results = []
        tier2_results = []
        tier3_results = []
        component_deps = []
        risk_propagation = []

        try:
            from backend.db.neo4j_client import run_cypher

            for entity in entities:
                # Tier-1 suppliers
                t1 = await run_cypher(CYPHER_TIER1_SUPPLIERS, {"name": entity})
                tier1_results.extend(t1 or [])

                # Tier-2 suppliers (sub-tier dependencies)
                t2 = await run_cypher(CYPHER_TIER2_SUPPLIERS, {"name": entity})
                tier2_results.extend(t2 or [])

                # Tier-3 suppliers (deep sub-tier)
                t3 = await run_cypher(CYPHER_TIER3_SUPPLIERS, {"name": entity})
                tier3_results.extend(t3 or [])

                # Component dependencies
                cd = await run_cypher(CYPHER_COMPONENT_DEPENDENCY, {"name": entity})
                component_deps.extend(cd or [])

                # Risk propagation paths
                rp = await run_cypher(CYPHER_SUPPLIER_RISK_PROPAGATION, {"name": entity})
                risk_propagation.extend(rp or [])

            # If no results found for any entity, get all suppliers
            if not (tier1_results or tier2_results or tier3_results):
                all_data = await run_cypher(CYPHER_ALL_SUPPLIERS)
                tier1_results = all_data or []

        except Exception as e:
            logger.warning(f"Neo4j Cypher queries failed: {e}")

        # Step 3: Optional vector search combination
        vector_context = []
        if self.combine_with_vector:
            try:
                from backend.rag.retriever import vector_retrieve
                docs = await vector_retrieve(query, top_k=top_k)
                vector_context = [
                    {"content": d.page_content, "metadata": d.metadata, "score": d.metadata.get("relevance_score", 0)}
                    for d in docs
                ]
            except Exception as e:
                logger.warning(f"Vector search in HybridCypherRetriever failed: {e}")

        return {
            "graph_results": {
                "tier1": tier1_results,
                "tier2": tier2_results,
                "tier3": tier3_results,
            },
            "component_deps": component_deps,
            "risk_propagation": risk_propagation,
            "vector_context": vector_context,
            "entities_found": entities,
            "query": query,
        }

    def format_graph_context(self, result: dict) -> str:
        """Format graph retrieval results into a readable context string."""
        parts = []

        # Tier-1 suppliers
        tier1 = result.get("graph_results", {}).get("tier1", [])
        if tier1:
            parts.append("--- Tier-1 Suppliers (Direct) ---")
            for r in tier1[:8]:
                parts.append(
                    f"  {r.get('supplier_name', '?')} | Location: {r.get('location', '?')} | "
                    f"Capability: {r.get('capability_match', '?')}% | Lead: {r.get('lead_time', '?')}d | "
                    f"Component: {r.get('component_name', '?')} | Cost: ${r.get('cost_per_unit', '?')}"
                )

        # Tier-2 suppliers
        tier2 = result.get("graph_results", {}).get("tier2", [])
        if tier2:
            parts.append("--- Tier-2 Suppliers (Sub-tier) ---")
            for r in tier2[:8]:
                parts.append(
                    f"  {r.get('supplier_name', '?')} (via {r.get('tier1_supplier', '?')}) | "
                    f"Location: {r.get('location', '?')} | Capability: {r.get('capability_match', '?')}% | "
                    f"Component: {r.get('component_name', '?')}"
                )

        # Tier-3 suppliers
        tier3 = result.get("graph_results", {}).get("tier3", [])
        if tier3:
            parts.append("--- Tier-3 Suppliers (Deep Sub-tier) ---")
            for r in tier3[:8]:
                parts.append(
                    f"  {r.get('supplier_name', '?')} (via {r.get('tier2_supplier', '?')} → {r.get('tier1_supplier', '?')}) | "
                    f"Location: {r.get('location', '?')} | Capability: {r.get('capability_match', '?')}%"
                )

        # Component dependencies
        deps = result.get("component_deps", [])
        if deps:
            parts.append("--- Component Dependencies ---")
            for r in deps[:8]:
                parts.append(
                    f"  {r.get('component', '?')} → used in → {r.get('used_in', '?')} | "
                    f"Supplier: {r.get('supplier', '?')} | Cost: ${r.get('cost', '?')}"
                )

        # Risk propagation
        risk = result.get("risk_propagation", [])
        if risk:
            parts.append("--- Risk Propagation Paths ---")
            for r in risk[:8]:
                parts.append(
                    f"  {r.get('source_supplier', '?')} → {r.get('dependent_supplier', '?')} | "
                    f"Tier: {r.get('tier', '?')} | Depth: {r.get('dependency_depth', '?')} | "
                    f"Location: {r.get('location', '?')}"
                )

        # Vector context
        vc = result.get("vector_context", [])
        if vc:
            parts.append("--- Vector Search Results ---")
            for i, r in enumerate(vc[:5]):
                parts.append(f"  [{i+1}] {r.get('content', '')[:200]}...")

        return "\n".join(parts) if parts else "No graph data available for this query."


# ---------------------------------------------------------------------------
# Convenience function (backwards-compatible with existing API)
# ---------------------------------------------------------------------------
async def graph_rag_query(query: str) -> dict:
    """Legacy entry point for graph RAG queries. Returns the raw result dict."""
    retriever = HybridCypherRetriever(use_llm_extraction=False, combine_with_vector=False)
    result = await retriever.retrieve(query)
    # Transform to legacy format for backwards compatibility
    legacy_results = {}
    for tier_name, tier_data in result.get("graph_results", {}).items():
        if tier_data:
            legacy_results[tier_name] = tier_data
    for dep in result.get("component_deps", []):
        legacy_results.setdefault("components", []).append(dep)
    for rp in result.get("risk_propagation", []):
        legacy_results.setdefault("risk_paths", []).append(rp)

    return {
        "graph_results": legacy_results,
        "entities_found": result.get("entities_found", []),
        "query": query,
    }


# ---------------------------------------------------------------------------
# Singleton retriever instance for reuse
# ---------------------------------------------------------------------------
_default_retriever: Optional[HybridCypherRetriever] = None


def get_graph_retriever(use_llm: bool = True, combine_vector: bool = True) -> HybridCypherRetriever:
    """Get or create the default HybridCypherRetriever instance."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = HybridCypherRetriever(
            use_llm_extraction=use_llm,
            combine_with_vector=combine_vector,
        )
    return _default_retriever
