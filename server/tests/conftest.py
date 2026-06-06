"""Test configuration and fixtures for the time_tracker test suite.

Uses SQLite in-memory database with standalone test models to avoid
PostgreSQL dependency and app.database module-level engine creation.
"""

import os
import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

# Set environment BEFORE any app imports to prevent PostgreSQL engine creation
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, Boolean, JSON, ForeignKey, Table, Column, select, func, and_
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings


# ---- Test Database Setup ----

class TestBase(DeclarativeBase):
    """Test SQLAlchemy declarative base."""
    pass


# Association table
ActivityTagTest = Table(
    "activity_tags",
    TestBase.metadata,
    Column("activity_id", String, ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(TestBase):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    activities = relationship("Activity", back_populates="user", lazy="selectin")
    tags = relationship("Tag", back_populates="user", lazy="selectin")


class TimeSegment(TestBase):
    __tablename__ = "time_segments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id: Mapped[str] = mapped_column(String, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    activity = relationship("Activity", back_populates="time_segments")

    def get_duration_seconds(self) -> int:
        end = self.end_time if self.end_time else datetime.now(timezone.utc)
        duration = (end - self.start_time).total_seconds()
        return int(max(0, duration))


class Activity(TestBase):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#4CAF50")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PAUSED", index=True)
    is_parallel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="activities")
    time_segments = relationship("TimeSegment", back_populates="activity", lazy="selectin", order_by="TimeSegment.start_time")
    tags = relationship("Tag", secondary="activity_tags", back_populates="activities", lazy="selectin")

    def get_elapsed_seconds(self) -> int:
        total = self.total_duration_seconds
        if self.status == "RUNNING" and self.time_segments:
            open_segment = None
            for seg in self.time_segments:
                if seg.end_time is None:
                    open_segment = seg
                    break
            if open_segment:
                elapsed = (datetime.now(timezone.utc) - open_segment.start_time).total_seconds()
                total += int(elapsed)
        return total


class Tag(TestBase):
    __tablename__ = "tags"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#2196F3")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="tags")
    activities = relationship("Activity", secondary="activity_tags", back_populates="tags", lazy="selectin")


# ---- Re-implement services for testing (same logic as production, using test models) ----

MAX_PARALLEL = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestAuthService:
    """AuthService with same logic, using test models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, email: str, password: str):
        # Check existing email
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalars().first():
            raise ValueError("Email already registered")
        # Check existing username
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalars().first():
            raise ValueError("Username already taken")
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            role="user",
            settings={"auto_pause_enabled": True, "theme": "system"},
        )
        self.db.add(user)
        await self.db.flush()
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        return {"user": user, "access_token": access_token, "refresh_token": refresh_token}

    async def login(self, email: str, password: str):
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        return {"user": user, "access_token": access_token, "refresh_token": refresh_token}

    async def refresh_token(self, refresh_token_str: str):
        try:
            payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            token_type = payload.get("type")
            if user_id is None or token_type != "refresh":
                raise ValueError("Invalid refresh token")
        except JWTError:
            raise ValueError("Invalid or expired refresh token")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("User not found")
        return {
            "access_token": self._create_access_token(user.id),
            "refresh_token": self._create_refresh_token(user.id),
        }

    async def verify_token(self, access_token: str) -> dict:
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            token_type = payload.get("type")
            if user_id is None or token_type != "access":
                raise ValueError("Invalid access token")
        except JWTError:
            raise ValueError("Invalid or expired access token")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("User not found")
        return {"user_id": user.id, "email": user.email, "role": user.role}

    def hash_password(self, plain: str) -> str:
        return pwd_context.hash(plain)

    def verify_password(self, plain: str, hash: str) -> bool:
        return pwd_context.verify(plain, hash)

    def _create_access_token(self, user_id: str) -> str:
        from datetime import timedelta
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": user_id, "type": "access", "exp": expire, "iat": datetime.now(timezone.utc)}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_refresh_token(self, user_id: str) -> str:
        from datetime import timedelta
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": user_id, "type": "refresh", "exp": expire, "iat": datetime.now(timezone.utc)}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class TestActivityService:
    """ActivityService with same logic, using test models."""

    def __init__(self, db: AsyncSession, ws_manager=None):
        self.db = db
        self.ws_manager = ws_manager

    async def create_activity(self, user_id: str, name: str, color: str = "#4CAF50", is_parallel: bool = False, tag_ids: list = None):
        activity = Activity(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            color=color,
            status="PAUSED",
            is_parallel=is_parallel,
            total_duration_seconds=0,
        )
        self.db.add(activity)
        if tag_ids:
            result = await self.db.execute(select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id))
            activity.tags = list(result.scalars().all())
        await self.db.flush()
        return activity

    async def start_activity(self, activity_id: str, user_id: str, parallel: bool = False):
        activity = await self._get_activity_or_raise(activity_id, user_id)
        if activity.status == "RUNNING":
            raise ValueError("Activity is already running")
        if activity.status == "ENDED":
            raise ValueError("Cannot restart an ended activity")

        auto_paused = []
        if not parallel:
            auto_paused = await self._auto_pause_running(user_id, exclude_id=activity_id)
        else:
            running_count = await self._count_running(user_id)
            if running_count >= MAX_PARALLEL:
                raise ValueError(f"Maximum {MAX_PARALLEL} parallel activities allowed")

        activity.status = "RUNNING"
        activity.is_parallel = parallel
        if activity.started_at is None:
            activity.started_at = datetime.now(timezone.utc)

        segment = TimeSegment(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        self.db.add(segment)
        await self.db.flush()
        return {"activity": activity, "auto_paused": auto_paused}

    async def pause_activity(self, activity_id: str, user_id: str):
        activity = await self._get_activity_or_raise(activity_id, user_id)
        if activity.status != "RUNNING":
            raise ValueError("Activity is not running")

        now = datetime.now(timezone.utc)
        await self._close_open_segment(activity.id, now)
        activity.status = "PAUSED"
        activity.total_duration_seconds = activity.get_elapsed_seconds()
        await self.db.flush()
        return activity

    async def resume_activity(self, activity_id: str, user_id: str):
        activity = await self._get_activity_or_raise(activity_id, user_id)
        if activity.status != "PAUSED":
            raise ValueError("Activity is not paused")

        if not activity.is_parallel:
            await self._auto_pause_running(user_id, exclude_id=activity_id)
        else:
            running_count = await self._count_running(user_id)
            if running_count >= MAX_PARALLEL:
                raise ValueError(f"Maximum {MAX_PARALLEL} parallel activities allowed")

        segment = TimeSegment(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        self.db.add(segment)
        activity.status = "RUNNING"
        await self.db.flush()
        return activity

    async def stop_activity(self, activity_id: str, user_id: str):
        activity = await self._get_activity_or_raise(activity_id, user_id)
        if activity.status == "ENDED":
            raise ValueError("Activity is already ended")

        now = datetime.now(timezone.utc)
        if activity.status == "RUNNING":
            await self._close_open_segment(activity.id, now)
            activity.total_duration_seconds = activity.get_elapsed_seconds()

        activity.status = "ENDED"
        activity.ended_at = now
        await self.db.flush()
        return activity

    async def delete_activity(self, activity_id: str, user_id: str):
        activity = await self._get_activity_or_raise(activity_id, user_id)
        await self.db.delete(activity)
        await self.db.flush()

    async def get_activity(self, activity_id: str, user_id: str):
        return await self._get_activity_or_raise(activity_id, user_id)

    async def list_activities(self, user_id: str, status: str = None, page: int = 1, page_size: int = 20):
        import math
        query = select(Activity).where(Activity.user_id == user_id)
        if status:
            query = query.where(Activity.status == status)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = query.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        activities = result.scalars().all()
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return {"items": activities, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def _auto_pause_running(self, user_id: str, exclude_id: str = None) -> list:
        query = select(Activity).where(Activity.user_id == user_id, Activity.status == "RUNNING")
        if exclude_id:
            query = query.where(Activity.id != exclude_id)
        result = await self.db.execute(query)
        running_activities = result.scalars().all()
        paused = []
        now = datetime.now(timezone.utc)
        for activity in running_activities:
            await self._close_open_segment(activity.id, now)
            activity.status = "PAUSED"
            activity.total_duration_seconds = activity.get_elapsed_seconds()
            paused.append(activity)
        return paused

    async def _count_running(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Activity).where(
                Activity.user_id == user_id, Activity.status == "RUNNING"
            )
        )
        return result.scalar() or 0

    async def _close_open_segment(self, activity_id: str, end_time: datetime):
        result = await self.db.execute(
            select(TimeSegment).where(TimeSegment.activity_id == activity_id, TimeSegment.end_time.is_(None))
        )
        open_segment = result.scalars().first()
        if open_segment:
            open_segment.end_time = end_time

    async def _broadcast_update(self, user_id: str, event_type: str, activity):
        """Broadcast an activity update via WebSocket."""
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

    async def _get_activity_or_raise(self, activity_id: str, user_id: str) -> Activity:
        result = await self.db.execute(
            select(Activity).where(Activity.id == activity_id, Activity.user_id == user_id)
        )
        activity = result.scalars().first()
        if not activity:
            raise ValueError("Activity not found")
        return activity


# ---- SQLite Test Engine ----

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False,
)


# ---- Pytest Fixtures ----

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def auth_service(db: AsyncSession) -> TestAuthService:
    return TestAuthService(db)


@pytest_asyncio.fixture
async def activity_service(db: AsyncSession) -> TestActivityService:
    return TestActivityService(db, ws_manager=None)


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    svc = TestAuthService(db)
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        password_hash=svc.hash_password("password123"),
        role="user",
        settings={"auto_pause_enabled": True, "theme": "system"},
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def second_user(db: AsyncSession) -> User:
    svc = TestAuthService(db)
    user = User(
        id=str(uuid.uuid4()),
        username="testuser2",
        email="test2@example.com",
        password_hash=svc.hash_password("password123"),
        role="user",
        settings={"auto_pause_enabled": True, "theme": "system"},
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def test_activity(db: AsyncSession, test_user: User) -> Activity:
    activity = Activity(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        name="Test Activity",
        color="#4CAF50",
        status="PAUSED",
        is_parallel=False,
        total_duration_seconds=0,
    )
    db.add(activity)
    await db.flush()
    return activity


@pytest_asyncio.fixture
async def running_activity(db: AsyncSession, test_user: User) -> Activity:
    now = datetime.now(timezone.utc)
    activity = Activity(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        name="Running Activity",
        color="#2196F3",
        status="RUNNING",
        is_parallel=False,
        total_duration_seconds=0,
        started_at=now,
    )
    db.add(activity)
    await db.flush()
    segment = TimeSegment(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        start_time=now,
        end_time=None,
    )
    db.add(segment)
    await db.flush()
    return activity
