"""Pydantic schemas for analytics API responses."""
from typing import Any, Dict, List
from pydantic import BaseModel


class EventsByTypeResponse(BaseModel):
    """Count of events grouped by event_type."""

    by_type: Dict[str, int]
    total: int


class EventsOverTimeResponse(BaseModel):
    """Events aggregated by time bucket (e.g. day)."""

    buckets: List[Dict[str, Any]]
    total: int


class SummaryStatsResponse(BaseModel):
    """High-level summary statistics."""

    total_events: int
    total_employees: int
    unique_users_with_events: int
    event_types: List[str]
    date_range: Dict[str, str]
