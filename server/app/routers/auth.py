"""Authentication API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserCreate, LoginRequest, AuthResponse, TokenPair,
    RefreshTokenRequest, UserResponse,
)
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account.

    Args:
        data: Registration data (username, email, password).
        db: Database session.

    Returns:
        AuthResponse with user data and JWT tokens.
    """
    auth_service = AuthService(db)
    try:
        result = await auth_service.register(data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": 40900, "message": str(e)},
        )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return tokens.

    Args:
        data: Login data (email, password).
        db: Database session.

    Returns:
        AuthResponse with user data and JWT tokens.
    """
    auth_service = AuthService(db)
    try:
        result = await auth_service.login(data.email, data.password)
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 40101, "message": "Invalid email or password"},
        )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token.

    Args:
        data: Refresh token data.
        db: Database session.

    Returns:
        New TokenPair with fresh access and refresh tokens.
    """
    auth_service = AuthService(db)
    try:
        result = await auth_service.refresh_token(data.refresh_token)
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 40102, "message": "Invalid or expired refresh token"},
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user profile.

    Args:
        current_user: Current authenticated user info.
        db: Database session.

    Returns:
        UserResponse with current user data.
    """
    from sqlalchemy import select
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": "User not found"},
        )
    return UserResponse.model_validate(user)
