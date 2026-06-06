"""Activity database model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Activity(Base):
    """Activity model representing a tracked time activity.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        name: Display name of the activity.
        color: Hex color code for visual display.
        status: Current status (RUNNING, PAUSED, ENDED).
        is_parallel: Whether this activity allows parallel execution.
        started_at: When the activity was first started (UTC).
        ended_at: When the activity was ended (UTC), None if still active.
        total_duration_seconds: Cumulative duration excluding current running segment.
        created_at: Record creation timestamp (UTC).
        updated_at: Last update timestamp (UTC).
    """

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#4CAF50")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PAUSED", index=True)
    is_parallel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="activities")
    time_segments = relationship(
        "TimeSegment", back_populates="activity", lazy="selectin",
        order_by="TimeSegment.start_time"
    )
    tags = relationship(
        "Tag", secondary="activity_tags", back_populates="activities", lazy="selectin"
    )

    def get_elapsed_seconds(self) -> int:
        """Calculate total elapsed seconds including the current running segment.

        Returns:
            Total elapsed seconds. For RUNNING activities, includes time
            since the last TimeSegment started.
        """
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

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, name={self.name}, status={self.status})>"
