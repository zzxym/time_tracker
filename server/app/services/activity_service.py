"""Activity service with auto-pause, parallel mode, and time tracking logic."""

from datetime import datetime, timezone
from typing import Optional
import uuid
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.activity import Activity
from app.models.time_segment import TimeSegment
from app.models.tag import Tag
from app.schemas.activity import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    ActivityStartRequest, StartActivityResponse, ActivityListResponse,
    TimeSegmentResponse,
)
from app.ws.manager import WebSocketManager

# Maximum number of parallel running activities
MAX_PARALLEL = 2


class ActivityService:
    """Service for managing activities, including start/pause/resume/stop
    with auto-pause and parallel mode enforcement.
    """

    def __init__(self, db: AsyncSession, ws_manager: Optional[WebSocketManager] = None):
        """Initialize with database session and optional WebSocket manager.

        Args:
            db: AsyncSession for database operations.
            ws_manager: WebSocketManager for broadcasting updates.
        """
        self.db = db
        self.ws_manager = ws_manager

    async def list_activities(
        self,
        user_id: str,
        status: Optional[str] = None,
        tag_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ActivityListResponse:
        """List activities for a user with optional filtering and pagination.

        Args:
            user_id: Owner's user ID.
            status: Filter by activity status.
            tag_id: Filter by tag ID.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            ActivityListResponse with paginated results.
        """
        query = select(Activity).where(Activity.user_id == user_id)

        if status:
            query = query.where(Activity.status == status)

        if tag_id:
            query = query.join(Activity.tags).where(Tag.id == tag_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(Activity.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        activities = result.scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return ActivityListResponse(
            items=[self._to_response(a) for a in activities],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_activity(self, activity_id: str, user_id: str) -> ActivityResponse:
        """Get a single activity by ID.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID (for data isolation).

        Returns:
            ActivityResponse.

        Raises:
            ValueError: If activity not found or doesn't belong to user.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)
        return self._to_response(activity)

    async def create_activity(self, user_id: str, data: ActivityCreate) -> ActivityResponse:
        """Create a new activity.

        Args:
            user_id: Owner's user ID.
            data: Activity creation data.

        Returns:
            ActivityResponse for the created activity.
        """
        activity = Activity(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            color=data.color,
            status="PAUSED",
            is_parallel=data.is_parallel,
            total_duration_seconds=0,
        )
        self.db.add(activity)

        # Associate tags
        if data.tag_ids:
            result = await self.db.execute(
                select(Tag).where(Tag.id.in_(data.tag_ids), Tag.user_id == user_id)
            )
            tags = result.scalars().all()
            activity.tags = list(tags)

        await self.db.flush()
        return self._to_response(activity)

    async def start_activity(
        self,
        activity_id: str,
        user_id: str,
        parallel: bool = False,
    ) -> StartActivityResponse:
        """Start an activity, with auto-pause logic for non-parallel mode.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.
            parallel: Whether to start in parallel mode.

        Returns:
            StartActivityResponse with the started activity and any auto-paused activities.

        Raises:
            ValueError: If activity not found, already running, or parallel limit exceeded.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)

        if activity.status == "RUNNING":
            raise ValueError("Activity is already running")

        if activity.status == "ENDED":
            raise ValueError("Cannot restart an ended activity")

        auto_paused = []

        if not parallel:
            # Auto-pause any running activities
            auto_paused = await self._auto_pause_running(user_id, exclude_id=activity_id)
        else:
            # Check parallel limit
            running_count = await self._count_running(user_id)
            if running_count >= MAX_PARALLEL:
                raise ValueError(f"Maximum {MAX_PARALLEL} parallel activities allowed")

        # Start the activity
        activity.status = "RUNNING"
        activity.is_parallel = parallel
        if activity.started_at is None:
            activity.started_at = datetime.now(timezone.utc)

        # Create a new time segment
        segment = TimeSegment(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        self.db.add(segment)

        await self.db.flush()

        # Broadcast activity started
        await self._broadcast_update(user_id, "activity_started", activity)

        # Broadcast auto-paused activities
        for paused_activity in auto_paused:
            await self._broadcast_update(user_id, "activity_paused", paused_activity)

        return StartActivityResponse(
            activity=self._to_response(activity),
            auto_paused=[self._to_response(a) for a in auto_paused],
        )

    async def pause_activity(self, activity_id: str, user_id: str) -> ActivityResponse:
        """Pause a running activity.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.

        Returns:
            ActivityResponse for the paused activity.

        Raises:
            ValueError: If activity not found or not running.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)

        if activity.status != "RUNNING":
            raise ValueError("Activity is not running")

        # Close the current open time segment
        now = datetime.now(timezone.utc)
        await self._close_open_segment(activity.id, now)

        # Update activity
        activity.status = "PAUSED"
        activity.total_duration_seconds = activity.get_elapsed_seconds()

        await self.db.flush()

        await self._broadcast_update(user_id, "activity_paused", activity)

        return self._to_response(activity)

    async def resume_activity(self, activity_id: str, user_id: str) -> ActivityResponse:
        """Resume a paused activity.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.

        Returns:
            ActivityResponse for the resumed activity.

        Raises:
            ValueError: If activity not found or not paused.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)

        if activity.status != "PAUSED":
            raise ValueError("Activity is not paused")

        # Auto-pause running activities if not parallel
        if not activity.is_parallel:
            await self._auto_pause_running(user_id, exclude_id=activity_id)
        else:
            running_count = await self._count_running(user_id)
            if running_count >= MAX_PARALLEL:
                raise ValueError(f"Maximum {MAX_PARALLEL} parallel activities allowed")

        # Create a new time segment
        segment = TimeSegment(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        self.db.add(segment)

        activity.status = "RUNNING"

        await self.db.flush()

        await self._broadcast_update(user_id, "activity_resumed", activity)

        return self._to_response(activity)

    async def stop_activity(self, activity_id: str, user_id: str) -> ActivityResponse:
        """Stop (end) an activity.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.

        Returns:
            ActivityResponse for the stopped activity.

        Raises:
            ValueError: If activity not found or already ended.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)

        if activity.status == "ENDED":
            raise ValueError("Activity is already ended")

        # Close the current open time segment if running
        now = datetime.now(timezone.utc)
        if activity.status == "RUNNING":
            await self._close_open_segment(activity.id, now)
            activity.total_duration_seconds = activity.get_elapsed_seconds()

        activity.status = "ENDED"
        activity.ended_at = now

        await self.db.flush()

        await self._broadcast_update(user_id, "activity_stopped", activity)

        return self._to_response(activity)

    async def update_activity(
        self, activity_id: str, user_id: str, data: ActivityUpdate
    ) -> ActivityResponse:
        """Update activity properties.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.
            data: Update data.

        Returns:
            ActivityResponse for the updated activity.

        Raises:
            ValueError: If activity not found.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)

        if data.name is not None:
            activity.name = data.name
        if data.color is not None:
            activity.color = data.color
        if data.is_parallel is not None:
            activity.is_parallel = data.is_parallel
        if data.tag_ids is not None:
            result = await self.db.execute(
                select(Tag).where(Tag.id.in_(data.tag_ids), Tag.user_id == user_id)
            )
            activity.tags = list(result.scalars().all())

        await self.db.flush()

        await self._broadcast_update(user_id, "activity_updated", activity)

        return self._to_response(activity)

    async def delete_activity(self, activity_id: str, user_id: str) -> None:
        """Delete an activity.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.

        Raises:
            ValueError: If activity not found.
        """
        activity = await self._get_activity_or_raise(activity_id, user_id)
        await self.db.delete(activity)
        await self.db.flush()

    async def _auto_pause_running(
        self, user_id: str, exclude_id: Optional[str] = None
    ) -> list[Activity]:
        """Auto-pause all running activities for a user, excluding one.

        This is the core auto-pause logic that runs on the server side
        to ensure consistency across all clients.

        Args:
            user_id: User ID whose activities to pause.
            exclude_id: Activity ID to exclude from pausing.

        Returns:
            List of activities that were auto-paused.
        """
        query = select(Activity).where(
            Activity.user_id == user_id,
            Activity.status == "RUNNING",
        )
        if exclude_id:
            query = query.where(Activity.id != exclude_id)

        result = await self.db.execute(query)
        running_activities = result.scalars().all()

        paused = []
        now = datetime.now(timezone.utc)
        for activity in running_activities:
            # Close the open time segment
            await self._close_open_segment(activity.id, now)
            activity.status = "PAUSED"
            activity.total_duration_seconds = activity.get_elapsed_seconds()
            paused.append(activity)

        return paused

    async def _count_running(self, user_id: str) -> int:
        """Count the number of currently running activities for a user.

        Args:
            user_id: User ID.

        Returns:
            Count of running activities.
        """
        result = await self.db.execute(
            select(func.count()).select_from(Activity).where(
                Activity.user_id == user_id,
                Activity.status == "RUNNING",
            )
        )
        return result.scalar() or 0

    async def _close_open_segment(self, activity_id: str, end_time: datetime) -> None:
        """Close the currently open time segment for an activity.

        Args:
            activity_id: Activity UUID.
            end_time: The end time to set.
        """
        result = await self.db.execute(
            select(TimeSegment).where(
                TimeSegment.activity_id == activity_id,
                TimeSegment.end_time.is_(None),
            )
        )
        open_segment = result.scalars().first()
        if open_segment:
            open_segment.end_time = end_time

    async def _get_activity_or_raise(
        self, activity_id: str, user_id: str
    ) -> Activity:
        """Get an activity by ID, ensuring it belongs to the user.

        Args:
            activity_id: Activity UUID.
            user_id: Owner's user ID.

        Returns:
            Activity instance.

        Raises:
            ValueError: If activity not found or doesn't belong to user.
        """
        result = await self.db.execute(
            select(Activity).where(Activity.id == activity_id, Activity.user_id == user_id)
        )
        activity = result.scalars().first()
        if not activity:
            raise ValueError("Activity not found")
        return activity

    async def _broadcast_update(
        self, user_id: str, event_type: str, activity: Activity
    ) -> None:
        """Broadcast an activity update via WebSocket.

        Args:
            user_id: User ID to broadcast to.
            event_type: WebSocket event type.
            activity: Updated activity.
        """
        if self.ws_manager:
            await self.ws_manager.send_to_user(user_id, {
                "type": event_type,
                "payload": {
                    "activity_id": activity.id,
                    "activity_name": activity.name,
                    "activity_status": activity.status,
                    "activity_color": activity.color,
                    "total_duration_seconds": activity.total_duration_seconds,
                },
            })

    def _to_response(self, activity: Activity) -> ActivityResponse:
        """Convert an Activity model to an ActivityResponse schema.

        Args:
            activity: Activity model instance.

        Returns:
            ActivityResponse schema.
        """
        from app.schemas.activity import TagBriefResponse

        return ActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            name=activity.name,
            color=activity.color,
            status=activity.status,
            is_parallel=activity.is_parallel,
            started_at=activity.started_at,
            ended_at=activity.ended_at,
            total_duration_seconds=activity.total_duration_seconds,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
            tags=[
                TagBriefResponse(id=t.id, name=t.name, color=t.color)
                for t in (activity.tags or [])
            ],
            time_segments=[
                TimeSegmentResponse(
                    id=s.id,
                    activity_id=s.activity_id,
                    start_time=s.start_time,
                    end_time=s.end_time,
                )
                for s in (activity.time_segments or [])
            ],
        )
