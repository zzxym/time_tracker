"""Tests for Activity API workflow: full lifecycle and cross-user scenarios.

These tests verify end-to-end workflows through the service layer,
mirroring the API endpoint behavior.
"""

import pytest
import uuid
from datetime import datetime, timezone

from conftest import Activity as TestActivity, TimeSegment as TestTimeSegment, MAX_PARALLEL


class TestFullActivityWorkflow:
    """End-to-end workflow tests for activity lifecycle."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_create_start_pause_resume_stop(self, activity_service, test_user):
        """Full activity lifecycle: create -> start -> pause -> resume -> stop."""
        # Create
        created = await activity_service.create_activity(test_user.id, "Lifecycle Test", "#FF9800")
        assert created.status == "PAUSED"

        # Start
        started = await activity_service.start_activity(created.id, test_user.id, parallel=False)
        assert started["activity"].status == "RUNNING"

        # Pause
        paused = await activity_service.pause_activity(created.id, test_user.id)
        assert paused.status == "PAUSED"

        # Resume
        resumed = await activity_service.resume_activity(created.id, test_user.id)
        assert resumed.status == "RUNNING"

        # Stop
        stopped = await activity_service.stop_activity(created.id, test_user.id)
        assert stopped.status == "ENDED"
        assert stopped.ended_at is not None

    @pytest.mark.asyncio
    async def test_two_users_independent_workflows(self, activity_service, test_user, second_user, db):
        """Two users should be able to run activities independently."""
        # User 1 creates and starts
        act1 = await activity_service.create_activity(test_user.id, "User1 Activity", "#E91E63")
        started1 = await activity_service.start_activity(act1.id, test_user.id, parallel=False)
        assert started1["activity"].status == "RUNNING"

        # User 2 creates and starts (should not affect user 1)
        act2 = await activity_service.create_activity(second_user.id, "User2 Activity", "#9C27B0")
        started2 = await activity_service.start_activity(act2.id, second_user.id, parallel=False)
        assert started2["activity"].status == "RUNNING"
        assert started2["auto_paused"] == []

        # User 1's activity should still be RUNNING
        check1 = await activity_service.get_activity(act1.id, test_user.id)
        assert check1.status == "RUNNING"

    @pytest.mark.asyncio
    async def test_auto_pause_then_restart_original(self, activity_service, test_user):
        """Start A -> Start B (auto-pauses A) -> Resume A (auto-pauses B)."""
        act_a = await activity_service.create_activity(test_user.id, "Activity A", "#F44336")
        act_b = await activity_service.create_activity(test_user.id, "Activity B", "#2196F3")

        # Start A
        result_a = await activity_service.start_activity(act_a.id, test_user.id, parallel=False)
        assert result_a["activity"].status == "RUNNING"

        # Start B (should auto-pause A)
        result_b = await activity_service.start_activity(act_b.id, test_user.id, parallel=False)
        assert result_b["activity"].status == "RUNNING"
        assert len(result_b["auto_paused"]) == 1
        assert result_b["auto_paused"][0].id == act_a.id

        # Resume A (should auto-pause B)
        result_a2 = await activity_service.resume_activity(act_a.id, test_user.id)
        assert result_a2.status == "RUNNING"

        # B should now be PAUSED
        check_b = await activity_service.get_activity(act_b.id, test_user.id)
        assert check_b.status == "PAUSED"

    @pytest.mark.asyncio
    async def test_start_two_parallel_then_non_parallel_auto_pauses_both(self, activity_service, test_user):
        """Start 2 parallel, then start non-parallel -> should auto-pause both."""
        act1 = await activity_service.create_activity(test_user.id, "P1", is_parallel=True)
        act2 = await activity_service.create_activity(test_user.id, "P2", is_parallel=True)
        act3 = await activity_service.create_activity(test_user.id, "NP", is_parallel=False)

        await activity_service.start_activity(act1.id, test_user.id, parallel=True)
        await activity_service.start_activity(act2.id, test_user.id, parallel=True)

        # Start non-parallel act3 -> should auto-pause both act1 and act2
        result = await activity_service.start_activity(act3.id, test_user.id, parallel=False)
        assert result["activity"].status == "RUNNING"
        assert len(result["auto_paused"]) == 2

        # Both parallel activities should be PAUSED
        check1 = await activity_service.get_activity(act1.id, test_user.id)
        check2 = await activity_service.get_activity(act2.id, test_user.id)
        assert check1.status == "PAUSED"
        assert check2.status == "PAUSED"

    @pytest.mark.asyncio
    async def test_stop_one_of_two_parallel_allows_third(self, activity_service, test_user):
        """After stopping one of 2 parallel activities, a third can start."""
        act1 = await activity_service.create_activity(test_user.id, "P1", is_parallel=True)
        act2 = await activity_service.create_activity(test_user.id, "P2", is_parallel=True)
        act3 = await activity_service.create_activity(test_user.id, "P3", is_parallel=True)

        await activity_service.start_activity(act1.id, test_user.id, parallel=True)
        await activity_service.start_activity(act2.id, test_user.id, parallel=True)

        # Stop one
        await activity_service.stop_activity(act1.id, test_user.id)

        # Third should now be allowed
        result = await activity_service.start_activity(act3.id, test_user.id, parallel=True)
        assert result["activity"].status == "RUNNING"
