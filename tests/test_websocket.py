import pytest
import httpx
import os
import json
import asyncio

os.environ["API_KEYS"] = "test-key"
os.environ["MCP_API_KEY"] = "test-mcp-key"

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"


@pytest.mark.asyncio
async def test_ws_connect_disconnect():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    async with ws_connect(f"{WS_URL}?api_key=test-key") as ws:
        # Should receive heartbeat within 35s
        msg = await asyncio.wait_for(ws.recv(), timeout=35)
        data = json.loads(msg)
        assert data["type"] in ("heartbeat", "pong")

    # Disconnect should be clean


@pytest.mark.asyncio
async def test_ws_subscribe_topic():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    async with ws_connect(f"{WS_URL}?api_key=test-key") as ws:
        await ws.send(json.dumps({"type": "subscribe", "topic": "council"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        assert data["type"] == "heartbeat"
        assert data["payload"]["status"] == "subscribed"
        assert data["payload"]["topic"] == "council"


@pytest.mark.asyncio
async def test_ws_heartbeat():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    async with ws_connect(f"{WS_URL}?api_key=test-key") as ws:
        # Wait for heartbeat (server sends every 30s)
        msg = await asyncio.wait_for(ws.recv(), timeout=35)
        data = json.loads(msg)
        assert data["type"] == "heartbeat"


@pytest.mark.asyncio
async def test_ws_ping_pong():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    async with ws_connect(f"{WS_URL}?api_key=test-key") as ws:
        await ws.send(json.dumps({"type": "ping"}))
        # May need to skip heartbeats
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(msg)
            if data["type"] == "pong":
                assert "timestamp" in data
                return
        pytest.fail("Did not receive pong")


@pytest.mark.asyncio
async def test_ws_auth_rejection():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    try:
        async with ws_connect(f"{WS_URL}?api_key=invalid-key") as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            pytest.fail("Should have been rejected")
    except Exception:
        pass  # Expected: connection closed with 4001


@pytest.mark.asyncio
async def test_ws_unsubscribe():
    try:
        from websockets import connect as ws_connect
    except ImportError:
        pytest.skip("websockets not installed")

    async with ws_connect(f"{WS_URL}?api_key=test-key") as ws:
        await ws.send(json.dumps({"type": "subscribe", "topic": "risk"}))
        await asyncio.wait_for(ws.recv(), timeout=10)

        await ws.send(json.dumps({"type": "unsubscribe", "topic": "risk"}))
        # No error should occur
