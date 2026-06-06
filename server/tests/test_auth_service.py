"""Tests for AuthService: registration, login, token management, password hashing."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from jose import jwt

from app.config import settings


class TestPasswordHashing:
    """Test password hashing and verification."""

    @pytest.mark.asyncio
    async def test_hash_password_returns_bcrypt_hash(self, auth_service):
        """Hash password should return a bcrypt hash string."""
        hashed = auth_service.hash_password("mypassword")
        assert hashed != "mypassword"
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    @pytest.mark.asyncio
    async def test_verify_password_correct(self, auth_service):
        """Correct password should verify successfully."""
        hashed = auth_service.hash_password("mypassword")
        assert auth_service.verify_password("mypassword", hashed) is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self, auth_service):
        """Wrong password should fail verification."""
        hashed = auth_service.hash_password("mypassword")
        assert auth_service.verify_password("wrongpassword", hashed) is False


class TestRegister:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service):
        """Successful registration should return user data and tokens."""
        result = await auth_service.register("newuser", "new@example.com", "password123")

        assert result["user"].username == "newuser"
        assert result["user"].email == "new@example.com"
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None
        assert result["user"].role == "user"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, test_user):
        """Registration with duplicate email should raise ValueError."""
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register("user2", "test@example.com", "password456")

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, test_user):
        """Registration with duplicate username should raise ValueError."""
        with pytest.raises(ValueError, match="Username already taken"):
            await auth_service.register("testuser", "other@example.com", "password456")

    @pytest.mark.asyncio
    async def test_register_password_is_hashed(self, auth_service, db):
        """Stored password should be hashed, not plaintext."""
        await auth_service.register("hashtest", "hash@example.com", "plaintext123")

        from sqlalchemy import select
        from conftest import User
        result = await db.execute(select(User).where(User.email == "hash@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.password_hash != "plaintext123"
        assert auth_service.verify_password("plaintext123", user.password_hash) is True


class TestLogin:
    """Test user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, test_user):
        """Login with correct credentials should return tokens."""
        result = await auth_service.login("test@example.com", "password123")

        assert result["user"].email == "test@example.com"
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, test_user):
        """Login with wrong password should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login("test@example.com", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, auth_service):
        """Login with non-existent email should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login("nobody@example.com", "password123")


class TestJWTTokenManagement:
    """Test JWT token creation, verification, and refresh."""

    @pytest.mark.asyncio
    async def test_access_token_contains_correct_claims(self, auth_service, test_user):
        """Access token should contain 'sub' (user_id) and 'type: access'."""
        token = auth_service._create_access_token(test_user.id)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == test_user.id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_refresh_token_contains_correct_claims(self, auth_service, test_user):
        """Refresh token should contain 'sub' (user_id) and 'type: refresh'."""
        token = auth_service._create_refresh_token(test_user.id)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == test_user.id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_access_token_expiry(self, auth_service, test_user):
        """Access token expiry should match ACCESS_TOKEN_EXPIRE_MINUTES setting."""
        token = auth_service._create_access_token(test_user.id)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # iat and exp are Unix timestamps (ints), so calculate directly
        expected_duration_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        actual_duration = payload["exp"] - payload["iat"]
        assert abs(actual_duration - expected_duration_seconds) < 5

    @pytest.mark.asyncio
    async def test_verify_valid_access_token(self, auth_service, test_user):
        """Valid access token should be verified and return user info."""
        token = auth_service._create_access_token(test_user.id)
        user_info = await auth_service.verify_token(token)

        assert user_info["user_id"] == test_user.id
        assert user_info["email"] == test_user.email
        assert user_info["role"] == test_user.role

    @pytest.mark.asyncio
    async def test_verify_access_token_rejects_refresh_token(self, auth_service, test_user):
        """verify_token should reject a refresh token (wrong type)."""
        refresh_token = auth_service._create_refresh_token(test_user.id)
        with pytest.raises(ValueError, match="Invalid access token"):
            await auth_service.verify_token(refresh_token)

    @pytest.mark.asyncio
    async def test_verify_expired_access_token(self, auth_service, test_user):
        """Expired access token should be rejected."""
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "sub": test_user.id,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc) - timedelta(minutes=30),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        with pytest.raises(ValueError, match="Invalid or expired access token"):
            await auth_service.verify_token(expired_token)

    @pytest.mark.asyncio
    async def test_verify_token_with_wrong_secret(self, auth_service, test_user):
        """Token signed with a different secret should be rejected."""
        payload = {
            "sub": test_user.id,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        bad_token = jwt.encode(payload, "wrong-secret-key", algorithm=settings.ALGORITHM)

        with pytest.raises(ValueError, match="Invalid or expired access token"):
            await auth_service.verify_token(bad_token)

    @pytest.mark.asyncio
    async def test_verify_token_user_deleted(self, auth_service, db):
        """Token for a deleted/non-existent user should be rejected."""
        fake_user_id = str(uuid.uuid4())
        token = auth_service._create_access_token(fake_user_id)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.verify_token(token)


class TestRefreshToken:
    """Test refresh token flow."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, test_user):
        """Valid refresh token should produce new token pair."""
        refresh_token = auth_service._create_refresh_token(test_user.id)
        result = await auth_service.refresh_token(refresh_token)

        assert result["access_token"] is not None
        assert result["refresh_token"] is not None

    @pytest.mark.asyncio
    async def test_refresh_token_produces_new_tokens(self, auth_service, test_user):
        """Refresh should produce valid new tokens."""
        refresh_token = auth_service._create_refresh_token(test_user.id)
        result = await auth_service.refresh_token(refresh_token)

        # New tokens should be valid (can be decoded)
        new_access_payload = jwt.decode(
            result["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        new_refresh_payload = jwt.decode(
            result["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert new_access_payload["type"] == "access"
        assert new_refresh_payload["type"] == "refresh"
        assert new_access_payload["sub"] == test_user.id
        assert new_refresh_payload["sub"] == test_user.id

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, auth_service, test_user):
        """Using an access token as refresh token should fail."""
        access_token = auth_service._create_access_token(test_user.id)
        with pytest.raises(ValueError, match="Invalid refresh token"):
            await auth_service.refresh_token(access_token)

    @pytest.mark.asyncio
    async def test_refresh_expired_token_fails(self, auth_service, test_user):
        """Expired refresh token should be rejected."""
        expire = datetime.now(timezone.utc) - timedelta(days=1)
        payload = {
            "sub": test_user.id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc) - timedelta(days=8),
        }
        expired_refresh = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await auth_service.refresh_token(expired_refresh)

    @pytest.mark.asyncio
    async def test_refresh_deleted_user_fails(self, auth_service):
        """Refresh token for a deleted user should fail."""
        fake_user_id = str(uuid.uuid4())
        refresh_token = auth_service._create_refresh_token(fake_user_id)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.refresh_token(refresh_token)
