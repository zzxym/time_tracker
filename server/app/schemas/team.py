"""Pydantic schemas for Team and TeamMember."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Team schemas ─────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class TeamMemberAdd(BaseModel):
    user_id: str
    role: str = Field(default="member", pattern="^(member|admin)$")


class TeamMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(member|admin)$")


# ── Response schemas ─────────────────────────────────────────

class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    username: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: str
    owner_id: str
    owner_username: str
    created_at: datetime
    updated_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True


# ── Team Activity / Stats schemas ───────────────────────────

class TeamMemberStatus(BaseModel):
    user_id: str
    username: str
    current_activity: Optional[str] = None
    current_activity_status: Optional[str] = None
    current_activity_started_at: Optional[datetime] = None
    today_duration_seconds: int = 0


class TeamActivityResponse(BaseModel):
    user_id: str
    username: str
    activity_id: str
    activity_name: str
    activity_status: str
    started_at: Optional[datetime] = None
    today_duration_seconds: int = 0

    class Config:
        from_attributes = True
