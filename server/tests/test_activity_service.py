"""Tests for ActivityService: auto-pause, parallel limits, time segments, user isolation."""

import pytest
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from conftest import Activity as TestActivity
from conftest import TimeSegment as TestTimeSegment
from conftest import MAX_PARALLEL


class TestCreateActivity:
    """Test activity creation."""

    @pytest.mark.asyncio
    async def test_create_activity_success(self, activity_service, test_user):
        """Creating an activity should return a PAUSED activity."""
        result = await activity_service.create_activity(test_user.id, "My Activity", "#FF5722", False)

        assert result.name == "My Activity"
        assert result.color == "#FF5722"
        assert result.status == "PAUSED"
        assert result.is_parallel is False
        assert result.total_duration_seconds == 0
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_activity_default_color(self, activity_service, test_user):
        """Activity should get default color if not specified."""
        result = await activity_service.create_activity(test_user.id, "Default Color Activity")

        assert result.color == "#4CAF50"

    @pytest.mark.asyncio
    async def test_create_activity_parallel_flag(self, activity_service, test_user):
        """Activity should store the is_parallel flag."""
        result = await activity_service.create_activity(test_user.id, "Parallel Activity", is_parallel=True)

        assert result.is_parallel is True


class TestStartActivity:
    """Test activity start with auto-pause and parallel mode."""

    @pytest.mark.asyncio
    async def test_start_paused_activity(self, activity_service, test_activity):
        """Starting a PAUSED activity should change status to RUNNING."""
        result = await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)

        assert result["activity"].status == "RUNNING"
        assert result["activity"].started_at is not None
        assert result["auto_paused"] == []

    @pytest.mark.asyncio
    async def test_start_creates_time_segment(self, activity_service, test_activity, db):
        """Starting an activity should create a new TimeSegment with end_time=None."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == test_activity.id)
        )
        segments = result.scalars().all()
        assert len(segments) == 1
        assert segments[0].start_time is not None
        assert segments[0].end_time is None

    @pytest.mark.asyncio
    async def test_start_already_running_activity_fails(self, activity_service, running_activity):
        """Starting an already RUNNING activity should raise ValueError."""
        with pytest.raises(ValueError, match="already running"):
            await activity_service.start_activity(running_activity.id, running_activity.user_id, parallel=False)

    @pytest.mark.asyncio
    async def test_start_ended_activity_fails(self, activity_service, db, test_user):
        """Starting an ENDED activity should raise ValueError."""
        ended_activity = TestActivity(
            id=str(uuid.uuid4()), user_id=test_user.id, name="Ended Activity",
            color="#000000", status="ENDED", is_parallel=False, total_duration_seconds=100,
        )
        db.add(ended_activity)
        await db.flush()

        with pytest.raises(ValueError, match="Cannot restart an ended activity"):
            await activity_service.start_activity(ended_activity.id, test_user.id, parallel=False)


class TestAutoPause:
    """Test auto-pause logic: non-parallel mode should auto-pause other running activities."""

    @pytest.mark.asyncio
    async def test_auto_pause_on_non_parallel_start(self, activity_service, running_activity, test_activity):
        """When starting activity B in non-parallel mode, running activity A should auto-pause."""
        result = await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)

        assert result["activity"].status == "RUNNING"
        assert len(result["auto_paused"]) == 1
        assert result["auto_paused"][0].id == running_activity.id
        assert result["auto_paused"][0].status == "PAUSED"

    @pytest.mark.asyncio
    async def test_auto_pause_closes_time_segment(self, activity_service, running_activity, test_activity, db):
        """Auto-pausing should close the open TimeSegment of the paused activity."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == running_activity.id)
        )
        segments = result.scalars().all()
        for seg in segments:
            assert seg.end_time is not None, "Time segment should be closed after auto-pause"

    @pytest.mark.asyncio
    async def test_no_auto_pause_in_parallel_mode(self, activity_service, running_activity, test_activity):
        """Starting in parallel mode should NOT auto-pause other running activities."""
        result = await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=True)

        assert result["activity"].status == "RUNNING"
        assert result["auto_paused"] == []

    @pytest.mark.asyncio
    async def test_auto_pause_updates_total_duration(self, activity_service, running_activity, test_activity):
        """Auto-pausing should update total_duration_seconds on the paused activity."""
        result = await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)

        assert result["auto_paused"][0].total_duration_seconds >= 0


class TestParallelLimit:
    """Test parallel activity limit (MAX_PARALLEL = 2)."""

    @pytest.mark.asyncio
    async def test_parallel_limit_enforcement(self, activity_service, test_user, db):
        """Starting a 3rd parallel activity should raise ValueError (MAX_PARALLEL=2)."""
        # Create and start 2 parallel activities
        act1 = await activity_service.create_activity(test_user.id, "Act1", "#111111", is_parallel=True)
        act2 = await activity_service.create_activity(test_user.id, "Act2", "#222222", is_parallel=True)
        act3 = await activity_service.create_activity(test_user.id, "Act3", "#333333", is_parallel=True)

        await activity_service.start_activity(act1.id, test_user.id, parallel=True)
        await activity_service.start_activity(act2.id, test_user.id, parallel=True)

        with pytest.raises(ValueError, match="Maximum 2 parallel activities"):
            await activity_service.start_activity(act3.id, test_user.id, parallel=True)

    @pytest.mark.asyncio
    async def test_max_parallel_constant_is_2(self):
        """MAX_PARALLEL should be set to 2 per PRD."""
        assert MAX_PARALLEL == 2

    @pytest.mark.asyncio
    async def test_two_parallel_activities_allowed(self, activity_service, test_user):
        """Starting 2 parallel activities should succeed."""
        act1 = await activity_service.create_activity(test_user.id, "P1", is_parallel=True)
        act2 = await activity_service.create_activity(test_user.id, "P2", is_parallel=True)

        r1 = await activity_service.start_activity(act1.id, test_user.id, parallel=True)
        r2 = await activity_service.start_activity(act2.id, test_user.id, parallel=True)

        assert r1["activity"].status == "RUNNING"
        assert r2["activity"].status == "RUNNING"


class TestPauseActivity:
    """Test pausing a running activity."""

    @pytest.mark.asyncio
    async def test_pause_running_activity(self, activity_service, running_activity):
        """Pausing a RUNNING activity should change status to PAUSED."""
        result = await activity_service.pause_activity(running_activity.id, running_activity.user_id)
        assert result.status == "PAUSED"

    @pytest.mark.asyncio
    async def test_pause_closes_time_segment(self, activity_service, running_activity, db):
        """Pausing should close the open TimeSegment."""
        await activity_service.pause_activity(running_activity.id, running_activity.user_id)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == running_activity.id)
        )
        segments = result.scalars().all()
        for seg in segments:
            assert seg.end_time is not None

    @pytest.mark.asyncio
    async def test_pause_updates_duration(self, activity_service, running_activity):
        """Pausing should update total_duration_seconds."""
        result = await activity_service.pause_activity(running_activity.id, running_activity.user_id)
        assert result.total_duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_pause_non_running_activity_fails(self, activity_service, test_activity):
        """Pausing a non-RUNNING activity should raise ValueError."""
        with pytest.raises(ValueError, match="not running"):
            await activity_service.pause_activity(test_activity.id, test_activity.user_id)


class TestResumeActivity:
    """Test resuming a paused activity."""

    @pytest.mark.asyncio
    async def test_resume_paused_activity(self, activity_service, test_activity):
        """Resuming a PAUSED activity should change status to RUNNING."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)
        result = await activity_service.resume_activity(test_activity.id, test_activity.user_id)
        assert result.status == "RUNNING"

    @pytest.mark.asyncio
    async def test_resume_creates_new_time_segment(self, activity_service, test_activity, db):
        """Resuming should create a new TimeSegment."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)
        await activity_service.resume_activity(test_activity.id, test_activity.user_id)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == test_activity.id)
            .order_by(TestTimeSegment.start_time)
        )
        segments = result.scalars().all()
        assert len(segments) == 2
        assert segments[0].end_time is not None  # First segment closed
        assert segments[1].end_time is None  # Second segment open

    @pytest.mark.asyncio
    async def test_resume_non_paused_activity_fails(self, activity_service, running_activity):
        """Resuming a non-PAUSED activity should raise ValueError."""
        with pytest.raises(ValueError, match="not paused"):
            await activity_service.resume_activity(running_activity.id, running_activity.user_id)

    @pytest.mark.asyncio
    async def test_resume_non_parallel_auto_pauses_others(
        self, activity_service, running_activity, test_activity
    ):
        """Resuming a non-parallel activity should auto-pause other running activities."""
        # Start test_activity (auto-pauses running_activity)
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)
        # Pause test_activity
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)
        # Resume running_activity (non-parallel) — should auto-pause test_activity
        result = await activity_service.resume_activity(running_activity.id, running_activity.user_id)
        assert result.status == "RUNNING"

        # test_activity should now be PAUSED
        check = await activity_service.get_activity(test_activity.id, test_activity.user_id)
        assert check.status == "PAUSED"


class TestStopActivity:
    """Test stopping (ending) an activity."""

    @pytest.mark.asyncio
    async def test_stop_running_activity(self, activity_service, running_activity):
        """Stopping a RUNNING activity should change status to ENDED."""
        result = await activity_service.stop_activity(running_activity.id, running_activity.user_id)
        assert result.status == "ENDED"
        assert result.ended_at is not None

    @pytest.mark.asyncio
    async def test_stop_closes_time_segment(self, activity_service, running_activity, db):
        """Stopping a running activity should close its open TimeSegment."""
        await activity_service.stop_activity(running_activity.id, running_activity.user_id)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == running_activity.id)
        )
        segments = result.scalars().all()
        for seg in segments:
            assert seg.end_time is not None

    @pytest.mark.asyncio
    async def test_stop_paused_activity(self, activity_service, test_activity):
        """Stopping a PAUSED activity should also work."""
        result = await activity_service.stop_activity(test_activity.id, test_activity.user_id)
        assert result.status == "ENDED"
        assert result.ended_at is not None

    @pytest.mark.asyncio
    async def test_stop_already_ended_fails(self, activity_service, db, test_user):
        """Stopping an already ENDED activity should raise ValueError."""
        ended = TestActivity(
            id=str(uuid.uuid4()), user_id=test_user.id, name="Ended",
            color="#000000", status="ENDED", is_parallel=False, total_duration_seconds=50,
        )
        db.add(ended)
        await db.flush()

        with pytest.raises(ValueError, match="already ended"):
            await activity_service.stop_activity(ended.id, test_user.id)

    @pytest.mark.asyncio
    async def test_stop_updates_duration(self, activity_service, running_activity):
        """Stopping should update total_duration_seconds."""
        result = await activity_service.stop_activity(running_activity.id, running_activity.user_id)
        assert result.total_duration_seconds >= 0


class TestTimeSegmentDuration:
    """Test that time segments correctly track duration."""

    @pytest.mark.asyncio
    async def test_start_pause_resume_stop_creates_two_segments(self, activity_service, test_activity, db):
        """Full cycle: start -> pause -> resume -> stop should create 2 time segments."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)
        await activity_service.resume_activity(test_activity.id, test_activity.user_id)
        await activity_service.stop_activity(test_activity.id, test_activity.user_id)

        result = await db.execute(
            select(TestTimeSegment).where(TestTimeSegment.activity_id == test_activity.id)
            .order_by(TestTimeSegment.start_time)
        )
        segments = result.scalars().all()

        assert len(segments) == 2
        assert segments[0].end_time is not None
        assert segments[1].end_time is not None
        assert segments[1].start_time >= segments[0].end_time

    @pytest.mark.asyncio
    async def test_cumulative_duration_after_multiple_cycles(self, activity_service, test_activity):
        """After start-pause-resume-pause cycles, total_duration_seconds should accumulate."""
        await activity_service.start_activity(test_activity.id, test_activity.user_id, parallel=False)
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)

        result1 = await activity_service.get_activity(test_activity.id, test_activity.user_id)
        duration_after_first = result1.total_duration_seconds

        await activity_service.resume_activity(test_activity.id, test_activity.user_id)
        await activity_service.pause_activity(test_activity.id, test_activity.user_id)

        result2 = await activity_service.get_activity(test_activity.id, test_activity.user_id)
        duration_after_second = result2.total_duration_seconds

        assert duration_after_second >= duration_after_first


class TestUserIsolation:
    """Test that activities are isolated between users."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_user_activity(self, activity_service, test_activity, second_user):
        """User should not be able to access another user's activity."""
        with pytest.raises(ValueError, match="Activity not found"):
            await activity_service.get_activity(test_activity.id, second_user.id)

    @pytest.mark.asyncio
    async def test_cannot_start_other_user_activity(self, activity_service, test_activity, second_user):
        """User should not be able to start another user's activity."""
        with pytest.raises(ValueError, match="Activity not found"):
            await activity_service.start_activity(test_activity.id, second_user.id, parallel=False)

    @pytest.mark.asyncio
    async def test_auto_pause_does_not_affect_other_user(self, activity_service, test_user, second_user, db):
        """Starting an activity should not auto-pause another user's running activity."""
        # Create running activity for user 2
        act_user2 = TestActivity(
            id=str(uuid.uuid4()), user_id=second_user.id, name="User2 Activity",
            color="#999999", status="RUNNING", is_parallel=False,
            total_duration_seconds=0, started_at=datetime.now(timezone.utc),
        )
        db.add(act_user2)
        seg_user2 = TestTimeSegment(
            id=str(uuid.uuid4()), activity_id=act_user2.id,
            start_time=datetime.now(timezone.utc), end_time=None,
        )
        db.add(seg_user2)

        # Create and start activity for user 1
        act_user1 = TestActivity(
            id=str(uuid.uuid4()), user_id=test_user.id, name="User1 Activity",
            color="#888888", status="PAUSED", is_parallel=False, total_duration_seconds=0,
        )
        db.add(act_user1)
        await db.flush()

        result = await activity_service.start_activity(act_user1.id, test_user.id, parallel=False)
        assert result["activity"].status == "RUNNING"

        # User 2's activity should still be RUNNING
        await db.refresh(act_user2)
        assert act_user2.status == "RUNNING"


class TestDeleteActivity:
    """Test activity deletion."""

    @pytest.mark.asyncio
    async def test_delete_activity_success(self, activity_service, test_activity):
        """Deleting an activity should succeed."""
        await activity_service.delete_activity(test_activity.id, test_activity.user_id)

        with pytest.raises(ValueError, match="Activity not found"):
            await activity_service.get_activity(test_activity.id, test_activity.user_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_activity(self, activity_service, test_user):
        """Deleting a non-existent activity should raise ValueError."""
        with pytest.raises(ValueError, match="Activity not found"):
            await activity_service.delete_activity("nonexistent-id", test_user.id)


class TestListActivities:
    """Test activity listing with filtering and pagination."""

    @pytest.mark.asyncio
    async def test_list_activities_returns_user_activities(self, activity_service, test_user, test_activity):
        """List should return activities for the specified user."""
        result = await activity_service.list_activities(test_user.id)

        assert result["total"] >= 1
        assert any(a.id == test_activity.id for a in result["items"])

    @pytest.mark.asyncio
    async def test_list_activities_status_filter(self, activity_service, test_user, test_activity, running_activity):
        """Status filter should only return matching activities."""
        result = await activity_service.list_activities(test_user.id, status="RUNNING")

        assert all(a.status == "RUNNING" for a in result["items"])
        assert any(a.id == running_activity.id for a in result["items"])

    @pytest.mark.asyncio
    async def test_list_activities_pagination(self, activity_service, test_user):
        """Pagination should work correctly."""
        for i in range(5):
            await activity_service.create_activity(test_user.id, f"Activity {i}", "#000000")

        result = await activity_service.list_activities(test_user.id, page=1, page_size=3)
        assert len(result["items"]) <= 3
        assert result["page"] == 1
        assert result["page_size"] == 3
