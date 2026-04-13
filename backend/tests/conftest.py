import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def api_headers():
    return {"X-API-Key": "dev-key"}
