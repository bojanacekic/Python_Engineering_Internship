"""
Analytics API endpoints: summary, events by type, events over time, load data.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_loader import DataLoader
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    EventsByTypeResponse,
    EventsOverTimeResponse,
    SummaryStatsResponse,
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
