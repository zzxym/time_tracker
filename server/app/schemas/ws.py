"""WebSocket message Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Any


WSMessageType = Literal[
    "activity_started",
    "activity_paused",
    "activity_resumed",
    "activity_stopped",
    "activity_updated",
    "tag_created",
    "tag_updated",
    "tag_deleted",
    "ping",
    "pong",
]


class WSMessage(BaseModel):
    """WebSocket message envelope."""
    type: WSMessageType
    payload: dict[str, Any] = Field(default_factory=dict)


class WSActivityPayload(BaseModel):
    """Payload for activity-related WebSocket messages."""
    activity_id: str
    activity_name: str
    activity_status: str
    activity_color: str
    total_duration_seconds: int = 0
    auto_paused_ids: list[str] = Field(default_factory=list)


class WSTagPayload(BaseModel):
    """Payload for tag-related WebSocket messages."""
    tag_id: str
    tag_name: str
    tag_color: str
