"""SQLAlchemy model for telemetry events."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.database import Base


class TelemetryEvent(Base):
    """Stored Claude Code telemetry event."""

    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)
    error_code = Column(String(64), nullable=True)
    raw_payload = Column(Text, nullable=True)  # Optional full JSON for flexibility

    def __repr__(self) -> str:
        return f"<TelemetryEvent {self.event_id} {self.event_type}>"
