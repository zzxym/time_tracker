"""Tag database model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# Association table for many-to-many relationship between Activity and Tag
ActivityTag = Table(
    "activity_tags",
    Base.metadata,
    Column("activity_id", UUID(as_uuid=False), ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=False), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """Tag model for categorizing activities.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        name: Display name of the tag.
        color: Hex color code for visual display.
        created_at: Record creation timestamp (UTC).
    """

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#2196F3")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="tags")
    activities = relationship(
        "Activity", secondary="activity_tags", back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
