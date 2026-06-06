"""Tag Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TagCreate(BaseModel):
    """Request schema for creating a tag."""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    color: str = Field(default="#2196F3", max_length=7, description="Hex color code")


class TagUpdate(BaseModel):
    """Request schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tag name")
    color: Optional[str] = Field(None, max_length=7, description="Hex color code")


class TagResponse(BaseModel):
    """Response schema for a tag."""
    id: str
    user_id: str
    name: str
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}
