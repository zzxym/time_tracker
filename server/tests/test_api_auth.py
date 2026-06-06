"""Tests for Auth API workflow: register, login, refresh token flow.

These tests verify end-to-end authentication workflows through the service layer,
mirroring the API endpoint behavior.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from jose import jwt
from app.config import settings


class TestAuthWorkflow:
    """End-to-end authentication workflow tests."""

    @pytest.mark.asyncio
    async def test_register_then_login_flow(self, auth_service):
        """Register a new user, then login with the same credentials."""
        # Register
        reg_result = await auth_service.register("flowuser", "flow@example.com", "mypassword")
        assert reg_result["user"].username == "flowuser"
        access_token = reg_result["access_token"]
        refresh_token = reg_result["refresh_token"]

        # Verify access token works
        user_info = await auth_service.verify_token(access_token)
        assert user_info["email"] == "flow@example.com"

        # Login
        login_result = await auth_service.login("flow@example.com", "mypassword")
        assert login_result["user"].username == "flowuser"

    @pytest.mark.asyncio
    async def test_register_then_refresh_flow(self, auth_service):
        """Register a new user, then use refresh token to get new tokens."""
        reg_result = await auth_service.register("refreshuser", "refresh@example.com", "mypassword")
        refresh_token = reg_result["refresh_token"]

        # Refresh
        new_tokens = await auth_service.refresh_token(refresh_token)
        assert new_tokens["access_token"] is not None
        assert new_tokens["refresh_token"] is not None

        # New access token should work
        user_info = await auth_service.verify_token(new_tokens["access_token"])
        assert user_info["email"] == "refresh@example.com"

    @pytest.mark.asyncio
    async def test_login_fails_then_succeeds_after_register(self, auth_service):
        """Login should fail before registration, then succeed after."""
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login("new@example.com", "password123")

        await auth_service.register("newuser", "new@example.com", "password123")

        result = await auth_service.login("new@example.com", "password123")
        assert result["user"].username == "newuser"

    @pytest.mark.asyncio
    async def test_token_type_isolation(self, auth_service, test_user):
        """Access token cannot be used as refresh token and vice versa."""
        access = auth_service._create_access_token(test_user.id)
        refresh = auth_service._create_refresh_token(test_user.id)

        # Access token should not work as refresh
        with pytest.raises(ValueError, match="Invalid refresh token"):
            await auth_service.refresh_token(access)

        # Refresh token should not work as access
        with pytest.raises(ValueError, match="Invalid access token"):
            await auth_service.verify_token(refresh)
