"""Pydantic schemas for analytics API responses."""
from typing import Any, Dict, List, Optional
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


# ---- Stakeholder analytics ----

class UsageByRoleItem(BaseModel):
    role: str
    event_count: int
    total_duration_ms: int
    user_count: int


class UsageByDepartmentItem(BaseModel):
    department: str
    event_count: int
    total_duration_ms: int
    user_count: int


class CostTrendResponse(BaseModel):
    """Usage/cost trend over time for charts."""
    labels: List[str]
    event_counts: List[int]
    total_duration_ms: List[int]
    buckets: List[Dict[str, Any]]


class PeakHoursResponse(BaseModel):
    labels: List[str]
    values: List[int]
    buckets: List[Dict[str, Any]]


class DistributionResponse(BaseModel):
    """Pie/bar chart: labels + values."""
    labels: List[str]
    values: List[int]
    total: int


class ToolSuccessRateItem(BaseModel):
    tool: str
    success_count: int
    failure_count: int
    success_rate_pct: float


class TopUserItem(BaseModel):
    user_id: str
    event_count: int
    name: Optional[str] = None
    department: Optional[str] = None


class TopDepartmentItem(BaseModel):
    department: str
    event_count: int
    user_count: int


class NarrativeInsightsResponse(BaseModel):
    bullets: List[str]
    generated_at: str
