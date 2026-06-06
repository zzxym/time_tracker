"""User and authentication Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserSettings(BaseModel):
    """User preference settings."""
    auto_pause_enabled: bool = True
    theme: str = "system"
    default_activity_color: str = "#4CAF50"


class UserCreate(BaseModel):
    """Request schema for user registration."""
    username: str = Field(..., min_length=3, max_length=100, description="Display name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password")


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str
    username: str
    email: str
    role: str = "user"
    settings: UserSettings = UserSettings()
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class TokenPair(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response with user data and tokens."""
    user: UserResponse
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token."""
    refresh_token: str = Field(..., description="Refresh token")
