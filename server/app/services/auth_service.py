"""Authentication service with JWT token management."""

from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, TokenPair, AuthResponse, UserResponse

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service handling user authentication, registration, and JWT token management."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session.

        Args:
            db: AsyncSession for database operations.
        """
        self.db = db

    async def register(self, data: UserCreate) -> AuthResponse:
        """Register a new user account.

        Args:
            data: User registration data.

        Returns:
            AuthResponse with user data and JWT tokens.

        Raises:
            ValueError: If email or username is already registered.
        """
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalars().first():
            raise ValueError("Email already registered")

        # Check if username already exists
        result = await self.db.execute(select(User).where(User.username == data.username))
        if result.scalars().first():
            raise ValueError("Username already taken")

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            username=data.username,
            email=data.email,
            password_hash=self.hash_password(data.password),
            role="user",
            settings={"auto_pause_enabled": True, "theme": "system", "default_activity_color": "#4CAF50"},
        )
        self.db.add(user)
        await self.db.flush()

        # Generate tokens
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, email: str, password: str) -> AuthResponse:
        """Authenticate a user and return tokens.

        Args:
            email: User email address.
            password: Plain text password.

        Returns:
            AuthResponse with user data and JWT tokens.

        Raises:
            ValueError: If credentials are invalid.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenPair:
        """Generate new token pair from a valid refresh token.

        Args:
            refresh_token_str: The refresh token string.

        Returns:
            New TokenPair with fresh access and refresh tokens.

        Raises:
            ValueError: If refresh token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id: Optional[str] = payload.get("sub")
            token_type: Optional[str] = payload.get("type")

            if user_id is None or token_type != "refresh":
                raise ValueError("Invalid refresh token")

        except JWTError:
            raise ValueError("Invalid or expired refresh token")

        # Verify user still exists
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("User not found")

        new_access = self._create_access_token(user.id)
        new_refresh = self._create_refresh_token(user.id)

        return TokenPair(
            access_token=new_access,
            refresh_token=new_refresh,
        )

    async def verify_token(self, access_token: str) -> dict:
        """Verify an access token and return user info.

        Args:
            access_token: The JWT access token string.

        Returns:
            Dict with user_id, email, and role.

        Raises:
            ValueError: If token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id: Optional[str] = payload.get("sub")
            token_type: Optional[str] = payload.get("type")

            if user_id is None or token_type != "access":
                raise ValueError("Invalid access token")

        except JWTError:
            raise ValueError("Invalid or expired access token")

        # Fetch user from DB
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("User not found")

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        }

    def hash_password(self, plain: str) -> str:
        """Hash a plain text password.

        Args:
            plain: Plain text password.

        Returns:
            Bcrypt hash string.
        """
        return pwd_context.hash(plain)

    def verify_password(self, plain: str, hash: str) -> bool:
        """Verify a plain text password against a hash.

        Args:
            plain: Plain text password.
            hash: Bcrypt hash string.

        Returns:
            True if the password matches the hash.
        """
        return pwd_context.verify(plain, hash)

    def _create_access_token(self, user_id: str) -> str:
        """Create a short-lived access token.

        Args:
            user_id: User ID to encode in the token.

        Returns:
            Encoded JWT access token.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_refresh_token(self, user_id: str) -> str:
        """Create a long-lived refresh token.

        Args:
            user_id: User ID to encode in the token.

        Returns:
            Encoded JWT refresh token.
        """
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
