"""Sync service for broadcasting updates via WebSocket and Redis Pub/Sub."""

from typing import Optional
import json
import redis.asyncio as redis

from app.config import settings
from app.ws.manager import WebSocketManager


class SyncService:
    """Service for synchronizing activity data across clients via WebSocket and Redis."""

    def __init__(self, ws_manager: Optional[WebSocketManager] = None):
        """Initialize with optional WebSocket manager.

        Args:
            ws_manager: WebSocketManager for broadcasting messages.
        """
        self.ws_manager = ws_manager
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection.

        Returns:
            Redis connection instance.
        """
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def broadcast_to_user(self, user_id: str, message: dict) -> None:
        """Broadcast a message to all connections of a user via WebSocket and Redis.

        If there are multiple worker processes, Redis Pub/Sub ensures
        the message reaches all processes that might have WebSocket connections
        for this user.

        Args:
            user_id: Target user ID.
            message: Message dict with 'type' and 'payload'.
        """
        # Send directly via WebSocket if available
        if self.ws_manager:
            await self.ws_manager.send_to_user(user_id, message)

        # Also publish to Redis for cross-process delivery
        try:
            r = await self._get_redis()
            channel = f"user:{user_id}"
            await r.publish(channel, json.dumps(message))
        except Exception:
            # Redis failure should not block the operation
            pass

    async def broadcast_activity_update(
        self, user_id: str, activity_id: str, activity_name: str,
        activity_status: str, activity_color: str, total_duration_seconds: int = 0,
        auto_paused_ids: Optional[list[str]] = None,
    ) -> None:
        """Broadcast an activity status update to a user.

        Args:
            user_id: Target user ID.
            activity_id: Updated activity ID.
            activity_name: Activity display name.
            activity_status: New activity status.
            activity_color: Activity color code.
            total_duration_seconds: Current duration.
            auto_paused_ids: IDs of activities auto-paused.
        """
        event_type = f"activity_{activity_status.lower()}"
        message = {
            "type": event_type,
            "payload": {
                "activity_id": activity_id,
                "activity_name": activity_name,
                "activity_status": activity_status,
                "activity_color": activity_color,
                "total_duration_seconds": total_duration_seconds,
                "auto_paused_ids": auto_paused_ids or [],
            },
        }
        await self.broadcast_to_user(user_id, message)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
