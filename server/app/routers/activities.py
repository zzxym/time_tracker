"""Activities API router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.activity_service import ActivityService
from app.schemas.activity import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    ActivityStartRequest, StartActivityResponse, ActivityListResponse,
)
from app.ws.manager import ws_manager

router = APIRouter()


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    tag_id: Optional[str] = Query(None, description="Filter by tag ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities for the current user with optional filtering.

    Args:
        status_filter: Optional status filter (RUNNING, PAUSED, ENDED).
        tag_id: Optional tag ID filter.
        page: Page number (1-based).
        page_size: Items per page.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Paginated list of activities.
    """
    service = ActivityService(db, ws_manager)
    return await service.list_activities(
        user_id=current_user["user_id"],
        status=status_filter,
        tag_id=tag_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single activity by ID.

    Args:
        activity_id: Activity UUID.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Activity data.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.get_activity(activity_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": str(e)},
        )


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new activity.

    Args:
        data: Activity creation data.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Created activity data.
    """
    service = ActivityService(db, ws_manager)
    return await service.create_activity(current_user["user_id"], data)


@router.post("/{activity_id}/start", response_model=StartActivityResponse)
async def start_activity(
    activity_id: str,
    data: ActivityStartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an activity with auto-pause and parallel mode support.

    Args:
        activity_id: Activity UUID.
        data: Start request with parallel flag.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Started activity and any auto-paused activities.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.start_activity(
            activity_id, current_user["user_id"], data.parallel
        )
    except ValueError as e:
        error_msg = str(e)
        if "parallel" in error_msg.lower() or "maximum" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": 40901, "message": error_msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40001, "message": error_msg},
        )


@router.post("/{activity_id}/pause", response_model=ActivityResponse)
async def pause_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a running activity.

    Args:
        activity_id: Activity UUID.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Paused activity data.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.pause_activity(activity_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40001, "message": str(e)},
        )


@router.post("/{activity_id}/resume", response_model=ActivityResponse)
async def resume_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused activity.

    Args:
        activity_id: Activity UUID.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Resumed activity data.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.resume_activity(activity_id, current_user["user_id"])
    except ValueError as e:
        error_msg = str(e)
        if "parallel" in error_msg.lower() or "maximum" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": 40901, "message": error_msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40001, "message": error_msg},
        )


@router.post("/{activity_id}/stop", response_model=ActivityResponse)
async def stop_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop (end) an activity.

    Args:
        activity_id: Activity UUID.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Stopped activity data.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.stop_activity(activity_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40001, "message": str(e)},
        )


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    data: ActivityUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update activity properties.

    Args:
        activity_id: Activity UUID.
        data: Update data.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Updated activity data.
    """
    service = ActivityService(db, ws_manager)
    try:
        return await service.update_activity(activity_id, current_user["user_id"], data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": str(e)},
        )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an activity.

    Args:
        activity_id: Activity UUID.
        current_user: Authenticated user info.
        db: Database session.
    """
    service = ActivityService(db, ws_manager)
    try:
        await service.delete_activity(activity_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": str(e)},
        )
