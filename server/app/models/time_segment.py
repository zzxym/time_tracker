"""TimeSegment database model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TimeSegment(Base):
    """TimeSegment model representing a continuous time recording period.

    Each segment records the start and end of a continuous timing period.
    An activity can have multiple segments (start-pause-resume-stop cycles).

    Attributes:
        id: UUID primary key.
        activity_id: Foreign key to the parent activity.
        start_time: When this segment started (UTC).
        end_time: When this segment ended (UTC), None if currently running.
    """

    __tablename__ = "time_segments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    activity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    activity = relationship("Activity", back_populates="time_segments")

    def get_duration_seconds(self) -> int:
        """Calculate the duration of this time segment in seconds.

        Returns:
            Duration in seconds. If end_time is None, calculates from start_time
            to the current time (segment is still running).
        """
        end = self.end_time if self.end_time else datetime.now(timezone.utc)
        duration = (end - self.start_time).total_seconds()
        return int(max(0, duration))

    def __repr__(self) -> str:
        return f"<TimeSegment(id={self.id}, activity_id={self.activity_id}, start={self.start_time})>"
