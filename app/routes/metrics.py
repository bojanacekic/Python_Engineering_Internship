"""API route for dashboard KPIs at GET /api/metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics as analytics_module

router = APIRouter(tags=["metrics"])


@router.get("")
def get_metrics(days: int = 30, db: Session = Depends(get_db)):
    """Return dashboard KPIs: total_events, estimated_cost_usd, total_tokens, active_users."""
    return analytics_module.dashboard_kpis(db, days=days)
