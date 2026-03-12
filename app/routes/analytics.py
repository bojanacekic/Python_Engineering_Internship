"""
Analytics API endpoints: summary, events by type, trends, and stakeholder metrics.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_loader import DataLoader
from app.services.analytics_service import AnalyticsService
from app.services import analytics as analytics_module
from app.schemas.analytics import (
    EventsByTypeResponse,
    EventsOverTimeResponse,
    SummaryStatsResponse,
    CostTrendResponse,
    PeakHoursResponse,
    DistributionResponse,
    ToolSuccessRateItem,
    NarrativeInsightsResponse,
)

router = APIRouter()


@router.get("/summary", response_model=SummaryStatsResponse)
def get_summary(db: Session = Depends(get_db)) -> SummaryStatsResponse:
    """Return high-level summary statistics."""
    svc = AnalyticsService(db)
    data = svc.get_summary_stats()
    return SummaryStatsResponse(**data)


@router.get("/events-by-type", response_model=EventsByTypeResponse)
def get_events_by_type(db: Session = Depends(get_db)) -> EventsByTypeResponse:
    """Return event counts grouped by event_type."""
    svc = AnalyticsService(db)
    by_type = svc.get_events_by_type()
    return EventsByTypeResponse(by_type=by_type, total=sum(by_type.values()))


@router.get("/events-over-time", response_model=EventsOverTimeResponse)
def get_events_over_time(
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
) -> EventsOverTimeResponse:
    """Return daily event counts, optionally limited to last N days."""
    if days is not None and (days < 1 or days > 365):
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    svc = AnalyticsService(db)
    buckets = svc.get_events_over_time(days=days)
    return EventsOverTimeResponse(buckets=buckets, total=sum(b["count"] for b in buckets))


@router.get("/events-by-department")
def get_events_by_department(db: Session = Depends(get_db)):
    """Return event counts per department."""
    svc = AnalyticsService(db)
    return svc.get_events_by_department()


@router.get("/top-users")
def get_top_users(limit: int = 10, db: Session = Depends(get_db)):
    """Return top users by event count."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    svc = AnalyticsService(db)
    return svc.get_top_users(limit=limit)


@router.post("/load-data")
def load_data(db: Session = Depends(get_db)):
    """Load telemetry_logs.jsonl and employees.csv into the database."""
    loader = DataLoader(db)
    result = loader.load_all()
    return result


# ---- Stakeholder analytics (charts + tables) ----

def _days_param(days: Optional[int] = 30) -> Optional[int]:
    if days is not None and (days < 1 or days > 365):
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    return days


@router.get("/usage-by-role")
def get_usage_by_role(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Usage (event count + duration) by employee role. API-friendly for charts/tables."""
    _days_param(days)
    return analytics_module.usage_by_role_for_api(db, days=days)


@router.get("/usage-by-department")
def get_usage_by_department(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Usage by department (practice). API-friendly for charts/tables."""
    _days_param(days)
    return analytics_module.usage_by_department_for_api(db, days=days)


@router.get("/cost-trend", response_model=CostTrendResponse)
def get_cost_trend(days: int = 30, db: Session = Depends(get_db)):
    """Usage/cost trend over time. Labels + series for line/area charts."""
    _days_param(days)
    return analytics_module.cost_trend_for_api(db, days=days)


@router.get("/peak-usage-hours", response_model=PeakHoursResponse)
def get_peak_usage_hours(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Event count by hour of day (0-23 UTC). For bar chart."""
    _days_param(days)
    return analytics_module.peak_usage_hours_for_api(db, days=days)


@router.get("/tool-usage", response_model=DistributionResponse)
def get_tool_usage(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Most common tool/event type distribution. For pie/bar chart."""
    _days_param(days)
    return analytics_module.tool_usage_for_api(db, days=days)


@router.get("/model-usage", response_model=DistributionResponse)
def get_model_usage(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Model usage distribution (from payload or default). For pie chart."""
    _days_param(days)
    return analytics_module.model_usage_for_api(db, days=days)


@router.get("/tool-success-rates")
def get_tool_success_rates(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Success vs failure rate per tool/event type. Table-friendly."""
    _days_param(days)
    return analytics_module.tool_success_rates_for_api(db, days=days)


@router.get("/average-session-duration")
def get_average_session_duration(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Average session duration in seconds."""
    _days_param(days)
    avg = analytics_module.average_session_duration(db, days=days)
    return {"average_seconds": avg, "unit": "seconds"}


@router.get("/top-users-activity")
def get_top_users_activity(limit: int = 10, days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Top users by event count with optional name/department."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    _days_param(days)
    return analytics_module.top_users_activity(db, limit=limit, days=days)


@router.get("/top-departments")
def get_top_departments(limit: int = 10, days: Optional[int] = 30, db: Session = Depends(get_db)):
    """Top departments by usage (event count)."""
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 50")
    _days_param(days)
    return analytics_module.top_departments_by_usage(db, limit=limit, days=days)


@router.get("/insights", response_model=NarrativeInsightsResponse)
def get_narrative_insights(days: int = 30, db: Session = Depends(get_db)):
    """5-8 auto-generated bullet insights in plain English."""
    _days_param(days)
    ni = analytics_module.get_insights(db, days=days)
    return NarrativeInsightsResponse(bullets=ni.bullets, generated_at=ni.generated_at)
