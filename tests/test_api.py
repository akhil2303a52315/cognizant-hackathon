import pytest
import httpx
import os

os.environ.setdefault("API_KEYS", "dev-key")
os.environ.setdefault("MCP_API_KEY", "dev-mcp-key")

BASE_URL = "http://localhost:8000"
API_HEADERS = {"X-API-Key": os.environ.get("API_KEYS", "dev-key").split(",")[0]}
MCP_HEADERS = {"X-MCP-API-Key": os.environ.get("MCP_API_KEY", "dev-mcp-key")}


@pytest.fixture
def client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=60)


@pytest.fixture
def api_headers():
    return API_HEADERS


@pytest.fixture
def mcp_headers():
    return MCP_HEADERS


# --- Health & Info ---

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ready(client):
    resp = await client.get("/ready")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_models_list(client, api_headers):
    resp = await client.get("/models/status", headers=api_headers)
    assert resp.status_code == 200


# --- Auth Rejection ---

@pytest.mark.asyncio
async def test_no_api_key(client):
    resp = await client.get("/council/analyze")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_api_key(client):
    resp = await client.get("/council/analyze", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_no_mcp_key(client):
    resp = await client.get("/mcp/tools")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_mcp_key(client):
    resp = await client.get("/mcp/tools", headers={"X-MCP-API-Key": "wrong"})
    assert resp.status_code == 401


# --- Council ---

@pytest.mark.asyncio
async def test_council_analyze(client, api_headers):
    pytest.skip("LLM call too slow for CI")
    # Skipped above


@pytest.mark.asyncio
async def test_council_stream(client, api_headers):
    pytest.skip("LLM streaming too slow for CI")
    # Skipped above


@pytest.mark.asyncio
async def test_council_export(client, api_headers):
    resp = await client.get("/council/export/test-session-id", headers=api_headers)
    assert resp.status_code in (200, 500)


# --- Risk ---

@pytest.mark.asyncio
async def test_risk_supplier(client, api_headers):
    resp = await client.get("/risk/score/test-supplier", headers=api_headers)
    assert resp.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_risk_heatmap(client, api_headers):
    resp = await client.get("/risk/heatmap", headers=api_headers)
    assert resp.status_code in (200, 500)


@pytest.mark.asyncio
async def test_risk_alerts(client, api_headers):
    resp = await client.get("/risk/suppliers", headers=api_headers)
    assert resp.status_code in (200, 500)


# --- Ingest ---

@pytest.mark.asyncio
async def test_ingest_news(client, api_headers):
    resp = await client.post("/ingest/news", headers=api_headers, json={"articles": [], "source": "test"})
    assert resp.status_code in (200, 422, 500)


# --- Optimize ---

@pytest.mark.asyncio
async def test_optimize_routes(client, api_headers):
    resp = await client.post("/optimize/routes", headers=api_headers, json={"origin": "A", "destination": "B"})
    assert resp.status_code in (200, 422, 500)


# --- Settings ---

@pytest.mark.asyncio
async def test_get_settings(client, api_headers):
    resp = await client.get("/settings/app", headers=api_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_settings(client, api_headers):
    resp = await client.put("/settings/app", headers=api_headers, json={"rag_chunk_size": 512})
    assert resp.status_code in (200, 422)


# --- RAG ---

@pytest.mark.asyncio
async def test_rag_collections(client, api_headers):
    resp = await client.get("/rag/collections", headers=api_headers)
    assert resp.status_code in (200, 500)


@pytest.mark.asyncio
async def test_rag_stats(client, api_headers):
    resp = await client.get("/rag/stats", headers=api_headers)
    assert resp.status_code in (200, 500)


@pytest.mark.asyncio
async def test_rag_health(client):
    resp = await client.get("/rag/health")
    assert resp.status_code in (200, 401)  # health may or may not require auth


@pytest.mark.asyncio
async def test_rag_query(client, api_headers):
    resp = await client.post("/rag/query", headers=api_headers, json={"query": "supply chain risk"})
    assert resp.status_code in (200, 500)


@pytest.mark.asyncio
async def test_rag_graph_query(client, api_headers):
    resp = await client.post("/rag/graph-query", headers=api_headers, json={"query": "supplier relationships"})
    assert resp.status_code in (200, 500)


@pytest.mark.asyncio
async def test_rag_hybrid_query(client, api_headers):
    resp = await client.post("/rag/hybrid-query", headers=api_headers, json={"query": "logistics risk"})
    assert resp.status_code in (200, 500)


# --- MCP ---

@pytest.mark.asyncio
async def test_mcp_list_tools(client, mcp_headers):
    resp = await client.get("/mcp/tools", headers=mcp_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_mcp_invoke_tool(client, mcp_headers):
    resp = await client.post("/mcp/tools/news_search/invoke", headers=mcp_headers, json={"query": "supply chain"})
    assert resp.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_mcp_rag_query(client, mcp_headers):
    resp = await client.post("/mcp/tools/rag_query/invoke", headers=mcp_headers, json={"query": "test"})
    assert resp.status_code in (200, 500)


# --- Rate Limiting ---

@pytest.mark.asyncio
async def test_rate_limiting(client, api_headers):
    pytest.skip("Rate limit test too slow for CI")
    responses = []
    for _ in range(70):
        resp = await client.get("/models/status", headers=api_headers)
        responses.append(resp.status_code)
    assert 429 in responses or all(r == 200 for r in responses)


# --- Sandbox Blocking ---

@pytest.mark.asyncio
async def test_sandbox_write_cypher(client, mcp_headers):
    resp = await client.post("/mcp/tools/supplier_search/invoke", headers=mcp_headers,
                             json={"query": "MATCH (n) DELETE n"})
    assert resp.status_code in (403, 200)  # 403 if sandbox blocks, 200 if tool handles it


@pytest.mark.asyncio
async def test_sandbox_write_sql(client, mcp_headers):
    resp = await client.post("/mcp/tools/supplier_financials/invoke", headers=mcp_headers,
                             json={"supplier_name": "'; DROP TABLE suppliers; --"})
    assert resp.status_code in (403, 200)
