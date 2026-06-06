"""Activity and TimeSegment Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TimeSegmentResponse(BaseModel):
    """Response schema for a time segment."""
    id: str
    activity_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    """Request schema for creating an activity."""
    name: str = Field(..., min_length=1, max_length=200, description="Activity name")
    color: str = Field(default="#4CAF50", max_length=7, description="Hex color code")
    is_parallel: bool = Field(default=False, description="Allow parallel execution")
    tag_ids: list[str] = Field(default_factory=list, description="Tag IDs to associate")


class ActivityUpdate(BaseModel):
    """Request schema for updating an activity."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Activity name")
    color: Optional[str] = Field(None, max_length=7, description="Hex color code")
    is_parallel: Optional[bool] = Field(None, description="Allow parallel execution")
    tag_ids: Optional[list[str]] = Field(None, description="Tag IDs to associate")


class ActivityStartRequest(BaseModel):
    """Request schema for starting an activity."""
    parallel: bool = Field(default=False, description="Start in parallel mode")


class ActivityResponse(BaseModel):
    """Response schema for an activity."""
    id: str
    user_id: str
    name: str
    color: str
    status: str
    is_parallel: bool
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    total_duration_seconds: int
    created_at: datetime
    updated_at: datetime
    tags: list["TagBriefResponse"] = Field(default_factory=list)
    time_segments: list[TimeSegmentResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TagBriefResponse(BaseModel):
    """Brief tag info embedded in activity response."""
    id: str
    name: str
    color: str

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    """Paginated list of activities."""
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StartActivityResponse(BaseModel):
    """Response schema for starting an activity, includes auto-paused activities."""
    activity: ActivityResponse
    auto_paused: list[ActivityResponse] = Field(default_factory=list)


# Update forward references
ActivityResponse.model_rebuild()
