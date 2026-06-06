"""Team management service layer."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Base
from app.models.user import User
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.activity import Activity
from app.models.time_segment import TimeSegment
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamMemberAdd, TeamMemberUpdate,
    TeamResponse, TeamDetailResponse, TeamMemberResponse,
    TeamMemberStatus, TeamActivityResponse,
)
from app.dependencies import require_admin


# ── Team CRUD ──────────────────────────────────────────────

async def create_team(db: AsyncSession, owner_id: str, data: TeamCreate) -> TeamResponse:
    """Create a new team owned by the current admin user."""
    team = Team(
        name=data.name,
        description=data.description or "",
        owner_id=owner_id,
    )
    db.add(team)
    await db.flush()
    await db.refresh(team)

    # Add owner as team admin member
    owner_member = TeamMember(
        team_id=team.id,
        user_id=owner_id,
        role="admin",
    )
    db.add(owner_member)
    await db.commit()

    return await get_team_detail(db, team.id, owner_id)


async def get_teams(db: AsyncSession, user_id: str) -> List[TeamResponse]:
    """List teams owned by the user (admin only)."""
    result = await db.execute(
        select(Team)
        .where(Team.owner_id == user_id)
        .order_by(Team.created_at.desc())
    )
    teams = result.scalars().all()

    responses = []
    for team in teams:
        member_count = await db.scalar(
            select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
        )
        owner = await db.get(User, team.owner_id)
        responses.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            owner_username=owner.username if owner else "",
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=member_count or 0,
        ))
    return responses


async def get_team_detail(db: AsyncSession, team_id: str, user_id: str) -> Optional[TeamDetailResponse]:
    """Get team detail with members list."""
    team = await db.get(Team, team_id)
    if not team:
        return None
    # Check permission: only owner or admin can view
    if team.owner_id != user_id:
        user = await db.get(User, user_id)
        if not user or user.role != "admin":
            return None

    # Get owner info
    owner = await db.get(User, team.owner_id)

    # Get members
    members_result = await db.execute(
        select(TeamMember, User.username, User.email)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    members_rows = members_result.all()

    member_responses = []
    for tm, username, email in members_rows:
        member_responses.append(TeamMemberResponse(
            id=tm.id,
            user_id=tm.user_id,
            username=username,
            email=email,
            role=tm.role,
            joined_at=tm.joined_at,
        ))

    member_count = await db.scalar(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team_id)
    )

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        owner_username=owner.username if owner else "",
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=member_count or 0,
        members=member_responses,
    )


async def update_team(db: AsyncSession, team_id: str, user_id: str, data: TeamUpdate) -> Optional[TeamResponse]:
    """Update team info (owner only)."""
    team = await db.get(Team, team_id)
    if not team or team.owner_id != user_id:
        return None

    if data.name is not None:
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    team.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(team)

    member_count = await db.scalar(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
    )
    owner = await db.get(User, team.owner_id)
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        owner_username=owner.username if owner else "",
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=member_count or 0,
    )


async def delete_team(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """Delete a team (owner only)."""
    team = await db.get(Team, team_id)
    if not team or team.owner_id != user_id:
        return False

    await db.delete(team)
    await db.commit()
    return True


# ── Team Member Management ────────────────────────────────

async def add_team_member(
    db: AsyncSession, team_id: str, owner_id: str, data: TeamMemberAdd
) -> Optional[TeamMemberResponse]:
    """Add a user to the team (owner only)."""
    # Verify team ownership
    team = await db.get(Team, team_id)
    if not team or team.owner_id != owner_id:
        return None

    # Check if user exists
    user = await db.get(User, data.user_id)
    if not user:
        return None

    # Check if already a member
    existing = await db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == data.user_id,
        )
    )
    if existing:
        return None  # Already a member

    member = TeamMember(
        team_id=team_id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return TeamMemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=user.username,
        email=user.email,
        role=member.role,
        joined_at=member.joined_at,
    )


async def update_team_member(
    db: AsyncSession, team_id: str, member_user_id: str, owner_id: str, data: TeamMemberUpdate
) -> bool:
    """Update a team member's role (owner only)."""
    team = await db.get(Team, team_id)
    if not team or team.owner_id != owner_id:
        return False

    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return False

    member.role = data.role
    await db.commit()
    return True


async def remove_team_member(
    db: AsyncSession, team_id: str, member_user_id: str, owner_id: str
) -> bool:
    """Remove a user from the team (owner only, cannot remove self)."""
    team = await db.get(Team, team_id)
    if not team or team.owner_id != owner_id:
        return False
    if member_user_id == owner_id:
        return False  # Cannot remove self

    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return False

    await db.delete(member)
    await db.commit()
    return True


# ── Team Activity & Status ────────────────────────────────

async def get_team_member_statuses(
    db: AsyncSession, team_id: str, user_id: str
) -> Optional[List[TeamMemberStatus]]:
    """Get current status of all team members (what they are doing now)."""
    # Verify permission
    team = await db.get(Team, team_id)
    if not team:
        return None
    if team.owner_id != user_id:
        u = await db.get(User, user_id)
        if not u or u.role != "admin":
            return None

    # Get all team member user_ids
    members_result = await db.execute(
        select(TeamMember, User.username)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    members_rows = members_result.all()

    statuses = []
    now = datetime.now(timezone.utc)

    for tm, username in members_rows:
        # Get current running activity for this user
        activity_result = await db.execute(
            select(Activity)
            .where(
                Activity.user_id == tm.user_id,
                Activity.status == "RUNNING",
            )
            .order_by(Activity.updated_at.desc())
            .limit(1)
        )
        current_activity = activity_result.scalar_one_or_none()

        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        # Get today's total duration for this user
        today_activities = await db.execute(
            select(func.coalesce(func.sum(Activity.total_duration_seconds), 0))
            .where(
                Activity.user_id == tm.user_id,
                Activity.started_at >= today_start,
            )
        )
        today_duration = today_activities.scalar() or 0

        # Add current segment duration if activity is running
        current_activity_name = None
        current_activity_status = None
        current_activity_started_at = None
        if current_activity:
            current_activity_name = current_activity.name
            current_activity_status = current_activity.status
            current_activity_started_at = current_activity.started_at
            # Add current segment time
            seg_result = await db.execute(
                select(TimeSegment)
                .where(
                    TimeSegment.activity_id == current_activity.id,
                    TimeSegment.end_time.is_(None),
                )
                .limit(1)
            )
            open_seg = seg_result.scalar_one_or_none()
            if open_seg:
                elapsed = int((now - open_seg.start_time).total_seconds())
                today_duration += elapsed

        statuses.append(TeamMemberStatus(
            user_id=tm.user_id,
            username=username,
            current_activity=current_activity_name,
            current_activity_status=current_activity_status,
            current_activity_started_at=current_activity_started_at,
            today_duration_seconds=int(today_duration),
        ))

    return statuses


async def get_team_activities(
    db: AsyncSession, team_id: str, user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id_filter: Optional[str] = None,
) -> Optional[List[TeamActivityResponse]]:
    """Get all team members' activities with optional date filter."""
    # Verify permission
    team = await db.get(Team, team_id)
    if not team:
        return None
    if team.owner_id != user_id:
        u = await db.get(User, user_id)
        if not u or u.role != "admin":
            return None

    # Get member user_ids
    members_result = await db.execute(
        select(TeamMember.user_id, User.username)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    member_data = {row[0]: row[1] for row in members_result.all()}
    member_ids = list(member_data.keys())

    if user_id_filter:
        if user_id_filter in member_ids:
            member_ids = [user_id_filter]
        else:
            return []

    # Build query
    query = (
        select(Activity, User.username)
        .join(User, Activity.user_id == User.id)
        .where(Activity.user_id.in_(member_ids))
    )
    if start_date:
        query = query.where(Activity.started_at >= start_date)
    if end_date:
        query = query.where(Activity.started_at <= end_date)

    query = query.order_by(Activity.started_at.desc())
    result = await db.execute(query)
    rows = result.all()

    responses = []
    for activity, username in rows:
        responses.append(TeamActivityResponse(
            user_id=activity.user_id,
            username=username,
            activity_id=activity.id,
            activity_name=activity.name,
            activity_status=activity.status,
            started_at=activity.started_at,
            today_duration_seconds=activity.get_elapsed_seconds(),
        ))
    return responses


async def get_team_stats(
    db: AsyncSession, team_id: str, user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Get team statistics summary."""
    # Verify permission
    team = await db.get(Team, team_id)
    if not team:
        return None
    if team.owner_id != user_id:
        u = await db.get(User, user_id)
        if not u or u.role != "admin":
            return None

    members_result = await db.execute(
        select(TeamMember.user_id, User.username)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    member_data = {row[0]: row[1] for row in members_result.all()}
    member_ids = list(member_data.keys())

    # Total activities
    total_activities = await db.scalar(
        select(func.count(Activity.id)).where(Activity.user_id.in_(member_ids))
    )

    # Total duration
    total_duration = await db.scalar(
        select(func.coalesce(func.sum(Activity.total_duration_seconds), 0))
        .where(Activity.user_id.in_(member_ids))
    ) or 0

    # Per-member stats
    per_member = []
    for uid, uname in member_data.items():
        member_activities = await db.scalar(
            select(func.count(Activity.id)).where(Activity.user_id == uid)
        )
        member_duration = await db.scalar(
            select(func.coalesce(func.sum(Activity.total_duration_seconds), 0))
            .where(Activity.user_id == uid)
        ) or 0
        per_member.append({
            "user_id": uid,
            "username": uname,
            "activity_count": member_activities or 0,
            "total_duration_seconds": int(member_duration),
        })

    return {
        "team_id": team_id,
        "member_count": len(member_ids),
        "total_activities": total_activities or 0,
        "total_duration_seconds": int(total_duration),
        "per_member": per_member,
    }


async def get_all_teams_for_global_admin(
    db: AsyncSession, admin_id: str
) -> List[TeamResponse]:
    """Get all teams (global admin only)."""
    result = await db.execute(
        select(Team).order_by(Team.created_at.desc())
    )
    teams = result.scalars().all()

    responses = []
    for team in teams:
        member_count = await db.scalar(
            select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
        )
        owner = await db.get(User, team.owner_id)
        responses.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            owner_username=owner.username if owner else "",
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=member_count or 0,
        ))
    return responses
