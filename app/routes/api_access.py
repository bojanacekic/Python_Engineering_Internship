"""
Programmatic API access to processed analytics data.

These endpoints expose clean JSON for integrations and evaluators.
All responses use native Python types (no custom objects).
Swagger/ReDoc remain disabled; use this module and README for API reference.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics as analytics_module

router = APIRouter(tags=["api-access"])


def _days(days: Optional[int]) -> int:
    """Validate days query param; default 30."""
    if days is not None and (days < 1 or days > 365):
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    return days if days is not None else 30


# ---- GET /api/summary: high-level KPIs ----
@router.get("/summary")
def get_summary(days: int = 30, db: Session = Depends(get_db)):
    """
    High-level summary: total events, estimated cost, total tokens, active users.
    Powers programmatic dashboards and health checks.
    """
    _days(days)
    data = analytics_module.dashboard_kpis(db, days=days)
    return {"days": days, **data}


# ---- GET /api/trends: daily usage/cost trend ----
@router.get("/trends")
def get_trends(days: int = 30, db: Session = Depends(get_db)):
    """
    Daily trend: labels (dates), event_counts, total_duration_ms.
    For time-series charts and usage-over-time analysis.
    """
    _days(days)
    return analytics_module.cost_trend_for_api(db, days=days)


# ---- GET /api/top-users: top users by estimated cost ----
@router.get("/top-users")
def get_top_users(limit: int = 10, days: int = 30, db: Session = Depends(get_db)):
    """
    Top users by estimated cost (duration-based proxy).
    Returns user_id, name, department, event_count, estimated_cost_usd.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    _days(days)
    return analytics_module.top_users_by_cost(db, limit=limit, days=days)


# ---- GET /api/tool-stats: tool usage + success/failure rates ----
@router.get("/tool-stats")
def get_tool_stats(days: int = 30, db: Session = Depends(get_db)):
    """
    Tool/feature stats: usage distribution (labels, values) and per-tool
    success/failure rates. For reliability and adoption analysis.
    """
    _days(days)
    usage = analytics_module.tool_usage_for_api(db, days=days)
    success_rates = analytics_module.tool_success_rates_for_api(db, days=days)
    return {"usage": usage, "success_rates": success_rates}


# ---- GET /api/insights: narrative insights ----
@router.get("/insights")
def get_insights(days: int = 30, db: Session = Depends(get_db)):
    """
    Automated narrative insights (5–10 bullets): peak usage, dominant model,
    top department, cost anomalies, most active user, etc.
    """
    _days(days)
    ni = analytics_module.get_insights(db, days=days)
    return {"bullets": ni.bullets, "generated_at": ni.generated_at}


# ---- GET /api/advanced-stats: advanced statistical analysis ----
@router.get("/advanced-stats")
def get_advanced_stats(days: int = 30, db: Session = Depends(get_db)):
    """
    Advanced stats: usage by weekday, avg session duration by department,
    cost by department, failure rate by tool, most volatile day, avg events per active user.
    """
    _days(days)
    return analytics_module.advanced_stats(db, days=days)
