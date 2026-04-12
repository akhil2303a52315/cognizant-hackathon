import logging
import asyncio
import os
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from backend.ws.events import EventType, Topic, build_event, subscribe_topic, unsubscribe_topic

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30  # seconds


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._topics: dict[str, set[WebSocket]] = {}  # topic -> set of websockets
        self._heartbeat_tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, api_key: Optional[str] = None):
        # Validate API key on connect
        valid_keys = os.getenv("API_KEYS", "dev-key").split(",")
        if api_key and api_key not in valid_keys:
            await websocket.close(code=4001, reason="Invalid API key")
            logger.warning("WebSocket connection rejected: invalid API key")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

        # Start heartbeat
        self._heartbeat_tasks[websocket] = asyncio.create_task(self._heartbeat_loop(websocket))
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Cancel heartbeat
        task = self._heartbeat_tasks.pop(websocket, None)
        if task:
            task.cancel()

        # Remove from all topics
        for topic_conns in self._topics.values():
            topic_conns.discard(websocket)

        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, topic: str):
        if topic not in self._topics:
            self._topics[topic] = set()
        self._topics[topic].add(websocket)
        logger.info(f"WebSocket subscribed to '{topic}'. Subscribers: {len(self._topics[topic])}")

    def unsubscribe(self, websocket: WebSocket, topic: str):
        if topic in self._topics:
            self._topics[topic].discard(websocket)
            logger.info(f"WebSocket unsubscribed from '{topic}'")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Broadcast failed: {e}")
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_topic(self, topic: str, message: dict):
        subscribers = self._topics.get(topic, set())
        disconnected = []
        for connection in subscribers:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Topic broadcast failed: {e}")
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Send failed: {e}")
            self.disconnect(websocket)

    async def _heartbeat_loop(self, websocket: WebSocket):
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                try:
                    await websocket.send_json(build_event(EventType.HEARTBEAT, {"status": "alive"}))
                except Exception:
                    break
        except asyncio.CancelledError:
            pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    # Extract API key from query params or headers
    api_key = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key")

    connected = await manager.connect(websocket, api_key=api_key)
    if not connected:
        return

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "unknown")

            if event_type == "ping":
                await manager.send_to(websocket, {"type": "pong", "timestamp": __import__("time").time()})

            elif event_type == "subscribe":
                topic_name = data.get("topic", data.get("channel", "council"))
                try:
                    topic = Topic(topic_name)
                    await subscribe_topic(websocket, topic)
                except ValueError:
                    await manager.send_to(websocket, build_event(
                        EventType.ERROR, {"message": f"Unknown topic: {topic_name}"}
                    ))

            elif event_type == "unsubscribe":
                topic_name = data.get("topic", data.get("channel", "council"))
                try:
                    topic = Topic(topic_name)
                    await unsubscribe_topic(websocket, topic)
                except ValueError:
                    pass

            elif event_type == "query":
                await manager.send_to(websocket, {"type": "ack", "message": "Processing query..."})

            else:
                await manager.send_to(websocket, build_event(
                    EventType.ERROR, {"message": f"Unknown event type: {event_type}"}
                ))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
