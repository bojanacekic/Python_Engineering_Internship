"""Pydantic schemas for telemetry events."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryEventCreate(BaseModel):
    """Payload for creating/ingesting a telemetry event."""

    event_id: str
    timestamp: datetime
    user_id: str
    event_type: str
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None


class TelemetryEventResponse(BaseModel):
    """Telemetry event as returned by the API."""

    id: int
    event_id: str
    timestamp: datetime
    user_id: str
    event_type: str
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None

    class Config:
        from_attributes = True
