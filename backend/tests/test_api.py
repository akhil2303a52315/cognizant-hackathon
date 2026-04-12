import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ready(client):
    r = await client.get("/ready")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_required(client):
    r = await client.post("/council/analyze", json={"query": "test"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_valid(client, api_headers):
    r = await client.get("/models/status", headers=api_headers)
    assert r.status_code == 200
