import logging

logger = logging.getLogger(__name__)


async def graph_rag_query(query: str) -> dict:
    try:
        from backend.db.neo4j_client import run_cypher
        entities = await _extract_entities(query)

        results = {}
        for entity in entities:
            supplier_data = await run_cypher(
                """MATCH (s:Supplier)
                   WHERE toLower(s.name) CONTAINS toLower($name) OR toLower(s.location) CONTAINS toLower($name)
                   MATCH (s)-[r]->(c:Component)
                   RETURN s, type(r) as rel_type, c
                   LIMIT 10""",
                {"name": entity},
            )
            if supplier_data:
                results[entity] = supplier_data

        if not results:
            all_suppliers = await run_cypher(
                "MATCH (s:Supplier)-[r]->(c:Component) RETURN s, type(r) as rel_type, c LIMIT 20"
            )
            results["all"] = all_suppliers

        return {
            "graph_results": results,
            "entities_found": list(results.keys()),
            "query": query,
        }
    except Exception as e:
        logger.warning(f"Graph RAG query failed: {e}")
        return {
            "graph_results": {},
            "entities_found": [],
            "query": query,
            "error": str(e),
        }


async def _extract_entities(query: str) -> list[str]:
    keywords = ["supplier", "company", "corp", "ltd", "inc", "components", "electronics", "semi"]
    words = query.lower().split()
    entities = []
    for i, word in enumerate(words):
        if word in keywords or len(word) > 4:
            entities.append(word)
        if word[0].isupper() and len(word) > 2:
            entities.append(word)
    return list(set(entities))[:5]
