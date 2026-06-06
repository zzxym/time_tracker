"""Team management API routes."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamMemberAdd, TeamMemberUpdate,
    TeamResponse, TeamDetailResponse, TeamMemberResponse,
    TeamMemberStatus, TeamActivityResponse,
)
from app import services as all_services


router = APIRouter(prefix="/teams", tags=["teams"])


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


# ── Team CRUD ─────────────────────────────────────

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team (admin only)."""
    user = await db.get(User, current_user["user_id"])
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await all_services.team_service.create_team(db, current_user["user_id"], data)
    return result


@router.get("", response_model=List[TeamResponse])
async def list_teams(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List teams owned by current user. Global admins see all."""
    user = await db.get(User, current_user["user_id"])
    if user and user.role == "admin":
        return await all_services.team_service.get_all_teams_for_global_admin(db, current_user["user_id"])
    return await all_services.team_service.get_teams(db, current_user["user_id"])


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team detail with members list."""
    result = await all_services.team_service.get_team_detail(db, team_id, current_user["user_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return result


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    data: TeamUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update team info (owner only)."""
    result = await all_services.team_service.update_team(db, team_id, current_user["user_id"], data)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return result


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a team (owner only)."""
    ok = await all_services.team_service.delete_team(db, team_id, current_user["user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Team not found or access denied")


# ── Team Member Management ─────────────────────────

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: str,
    data: TeamMemberAdd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a user to the team (owner only)."""
    result = await all_services.team_service.add_team_member(db, team_id, current_user["user_id"], data)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot add member (team not found, user not found, or already a member)")
    return result


@router.put("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_team_member(
    team_id: str,
    user_id: str,
    data: TeamMemberUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a team member's role (owner only)."""
    ok = await all_services.team_service.update_team_member(db, team_id, user_id, current_user["user_id"], data)
    if not ok:
        raise HTTPException(status_code=404, detail="Team or member not found, or access denied")


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from the team (owner only, cannot remove self)."""
    ok = await all_services.team_service.remove_team_member(db, team_id, user_id, current_user["user_id"])
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot remove member (not found, access denied, or removing self)")


# ── Team Activity & Status ─────────────────────────

@router.get("/{team_id}/status", response_model=List[TeamMemberStatus])
async def get_team_member_status(
    team_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current status of all team members (what they are doing now)."""
    result = await all_services.team_service.get_team_member_statuses(db, team_id, current_user["user_id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return result


@router.get("/{team_id}/activities", response_model=List[TeamActivityResponse])
async def get_team_activities(
    team_id: str,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all team members' activities with optional date filter."""
    result = await all_services.team_service.get_team_activities(
        db, team_id, current_user["user_id"],
        start_date=start_date, end_date=end_date, user_id_filter=user_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return result


@router.get("/{team_id}/stats")
async def get_team_stats(
    team_id: str,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team statistics summary."""
    result = await all_services.team_service.get_team_stats(
        db, team_id, current_user["user_id"],
        start_date=start_date, end_date=end_date,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return result
