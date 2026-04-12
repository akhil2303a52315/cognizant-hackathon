from neo4j import AsyncGraphDatabase
import os

_driver = None


async def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "testpassword")),
        )
    return _driver


async def close_neo4j():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def run_cypher(query: str, params: dict = None):
    driver = await get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(query, params or {})
        return await result.data()


async def init_neo4j_schema():
    constraints = [
        "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    ]
    for c in constraints:
        try:
            await run_cypher(c)
        except:
            pass

    await run_cypher("""
        MERGE (s1:Supplier {id: 'S1', name: 'Taiwan Semi Corp', capability_match: 95, lead_time_days: 14, location: 'Taiwan', tier: 1})
        MERGE (s2:Supplier {id: 'S2', name: 'India Electronics Ltd', capability_match: 82, lead_time_days: 12, location: 'India', tier: 1})
        MERGE (s3:Supplier {id: 'S3', name: 'Vietnam Components', capability_match: 75, lead_time_days: 18, location: 'Vietnam', tier: 2})
        MERGE (c1:Component {id: 'C1', name: 'Chip Module A'})
        MERGE (c2:Component {id: 'C2', name: 'PCB Assembly'})
        MERGE (s1)-[:SUPPLIES {lead_time_days: 14, moq: 10000, cost_per_unit: 12.50}]->(c1)
        MERGE (s2)-[:SUPPLIES {lead_time_days: 12, moq: 5000, cost_per_unit: 14.00}]->(c1)
        MERGE (s3)-[:SUPPLIES {lead_time_days: 18, moq: 3000, cost_per_unit: 11.00}]->(c2)
        MERGE (s1)-[:DEPENDS_ON]->(s3)
        MERGE (c1)-[:USED_IN]->(c2)
    """)
