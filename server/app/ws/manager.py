"""WebSocket connection manager with Redis Pub/Sub for multi-process broadcasting."""

import json
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.config import settings
from app.services.auth_service import AuthService
from app.database import AsyncSessionLocal


class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages via Redis Pub/Sub.

    This manager maintains a mapping of user_id -> set of WebSocket connections,
    allowing multiple devices/terminals per user. Redis Pub/Sub is used to
    broadcast messages across multiple worker processes.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis = None

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            user_id: Authenticated user ID.
            websocket: The WebSocket connection instance.
        """
        await websocket.accept()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            user_id: User ID.
            websocket: The WebSocket connection to remove.
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a message to all WebSocket connections of a user.

        Args:
            user_id: Target user ID.
            message: Message dict to send as JSON.
        """
        connections = self.active_connections.get(user_id, set())
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)

        # Clean up disconnected WebSockets
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)
        if user_id in self.active_connections and not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def subscribe_redis(self) -> None:
        """Subscribe to Redis Pub/Sub channels for cross-process message delivery.

        Listens to channels named 'user:{user_id}' and forwards messages
        to local WebSocket connections.
        """
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = self._redis.pubsub()

        # Subscribe to all user channels using pattern
        await pubsub.psubscribe("user:*")

        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    data = json.loads(message["data"])
                    # Extract user_id from channel name: user:{user_id}
                    channel = message["channel"]
                    if isinstance(channel, str) and channel.startswith("user:"):
                        user_id = channel.split(":", 1)[1]
                        # Only send to local connections; don't re-publish to Redis
                        connections = self.active_connections.get(user_id, set())
                        for ws in list(connections):
                            try:
                                await ws.send_json(data)
                            except Exception:
                                self.disconnect(user_id, ws)
                except Exception:
                    continue

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global WebSocket manager instance
ws_manager = WebSocketManager()

# WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/api/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for real-time activity updates.

    Accepts connections with JWT token authentication via query parameter.
    Handles heartbeat (ping/pong) and message broadcasting.

    Args:
        websocket: The WebSocket connection.
        token: JWT access token from query parameter.
    """
    # Authenticate via token query parameter
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        async with AsyncSessionLocal() as db:
            auth_service = AuthService(db)
            user_info = await auth_service.verify_token(token)
            user_id = user_info["user_id"]
    except (ValueError, JWTError):
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # Accept connection
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle ping/pong heartbeat
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            # Other message types can be handled here

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception:
        ws_manager.disconnect(user_id, websocket)
