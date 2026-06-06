"""Dependency injection functions for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and verify the current user from the JWT access token.

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.

    Returns:
        dict: User information including user_id, email, and role.

    Raises:
        HTTPException: 401 if token is invalid or expired.
    """
    auth_service = AuthService(db)
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[dict]:
    """Optionally extract user from JWT token.

    Args:
        credentials: Bearer token from Authorization header (optional).
        db: Database session.

    Returns:
        Optional[dict]: User information if token is valid, None otherwise.
    """
    if credentials is None:
        return None
    auth_service = AuthService(db)
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except ValueError:
        return None


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require the current user to have admin role.

    Args:
        current_user: Current authenticated user.

    Returns:
        dict: User information if admin.

    Raises:
        HTTPException: 403 if user is not admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
