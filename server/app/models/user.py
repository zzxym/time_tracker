"""User database model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """User model for authentication and profile management.

    Attributes:
        id: UUID primary key.
        username: Unique display name.
        email: Unique email address.
        password_hash: Bcrypt hashed password.
        role: User role ('user' or 'admin').
        settings: JSONB field for user preferences.
        created_at: Account creation timestamp (UTC).
        updated_at: Last update timestamp (UTC).
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    activities = relationship("Activity", back_populates="user", lazy="selectin")
    tags = relationship("Tag", back_populates="user", lazy="selectin")
    owned_teams = relationship("Team", back_populates="owner", lazy="selectin")
    team_memberships = relationship("TeamMember", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
