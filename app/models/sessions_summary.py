"""SQLAlchemy model for session-level aggregates."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.database import Base


class SessionSummary(Base):
    """One row per session: same user, bounded by session_start or 30-min gap."""

    __tablename__ = "sessions_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    session_start_ts = Column(DateTime, nullable=False, index=True)
    session_end_ts = Column(DateTime, nullable=False, index=True)
    event_count = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<SessionSummary user_id={self.user_id} start={self.session_start_ts}>"
