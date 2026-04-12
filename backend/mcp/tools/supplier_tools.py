from backend.mcp.registry import register_tool
import logging

logger = logging.getLogger(__name__)


async def _neo4j_query(params: dict):
    cypher = params.get("cypher_query", params.get("query", ""))
    try:
        from backend.db.neo4j_client import run_cypher
        result = await run_cypher(cypher)
        return {"results": result, "query": cypher}
    except Exception as e:
        return {"results": [], "error": str(e), "query": cypher}


async def _supplier_search(params: dict):
    product = params.get("product", "")
    region = params.get("region", "")
    try:
        from backend.db.neo4j_client import run_cypher
        query = """
            MATCH (s:Supplier)-[:SUPPLIES]->(c:Component)
            WHERE ($product = '' OR toLower(c.name) CONTAINS toLower($product))
              AND ($region = '' OR toLower(s.location) CONTAINS toLower($region))
            RETURN s.id, s.name, s.capability_match, s.lead_time_days, s.location, s.tier
            ORDER BY s.capability_match DESC LIMIT 10
        """
        result = await run_cypher(query, {"product": product, "region": region})
        return {"suppliers": result, "product": product, "region": region}
    except Exception as e:
        return _mock_supplier_search(product, region)


def _mock_supplier_search(product: str, region: str) -> dict:
    return {
        "suppliers": [
            {"id": "S1", "name": "Taiwan Semi Corp", "capability_match": 95, "lead_time_days": 14, "location": "Taiwan", "tier": 1},
            {"id": "S2", "name": "India Electronics Ltd", "capability_match": 82, "lead_time_days": 12, "location": "India", "tier": 1},
            {"id": "S3", "name": "Vietnam Components", "capability_match": 75, "lead_time_days": 18, "location": "Vietnam", "tier": 2},
        ],
        "product": product,
        "region": region,
        "mock": True,
    }


async def _contract_lookup(params: dict):
    supplier_id = params.get("supplier_id", "")
    try:
        from backend.db.neon import execute_query
        rows = await execute_query(
            "SELECT * FROM supplier_contracts WHERE supplier_id = $1 LIMIT 5",
            supplier_id,
        )
        if rows:
            return {"contracts": [dict(r) for r in rows]}
    except Exception:
        pass
    return {
        "contracts": [
            {"supplier_id": supplier_id, "contract_type": "annual", "value": 500000, "status": "active", "renewal_date": "2026-03-01"},
        ],
        "mock": True,
    }


def register():
    register_tool(
        name="neo4j_query",
        description="Execute a read-only Cypher query against the supplier graph (sandboxed)",
        input_schema={
            "type": "object",
            "properties": {
                "cypher_query": {"type": "string", "description": "Cypher query (read-only)"},
            },
            "required": ["cypher_query"],
        },
        handler=_neo4j_query,
        category="supplier",
        cache_ttl=600,
    )
    register_tool(
        name="supplier_search",
        description="Search suppliers by product and region from Neo4j graph",
        input_schema={
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product/component name"},
                "region": {"type": "string", "description": "Geographic region filter", "default": ""},
            },
            "required": ["product"],
        },
        handler=_supplier_search,
        category="supplier",
        cache_ttl=600,
    )
    register_tool(
        name="contract_lookup",
        description="Look up contract details for a supplier from Neon PG",
        input_schema={
            "type": "object",
            "properties": {
                "supplier_id": {"type": "string", "description": "Supplier ID"},
            },
            "required": ["supplier_id"],
        },
        handler=_contract_lookup,
        category="supplier",
        cache_ttl=3600,
    )
