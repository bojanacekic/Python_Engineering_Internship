"""
Page routes: dashboard and index. Serves Jinja2-rendered HTML.
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics as analytics_module

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ALLOWED_DAYS = (7, 30, 90)


def _coerce_days(days: Optional[int]) -> int:
    """Return 30 if days is None or not in ALLOWED_DAYS; otherwise return days."""
    if days is not None and days in ALLOWED_DAYS:
        return days
    return 30


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    days: Optional[int] = Query(None, description="Time window: 7, 30, or 90 days"),
):
    """Render the main analytics dashboard: KPIs, charts, tables, insights. Supports ?days=7|30|90."""
    days = _coerce_days(days)
    metrics_kpis = analytics_module.dashboard_kpis(db, days=days)
    cost_trend = analytics_module.cost_trend_for_api(db, days=days)
    peak_hours = analytics_module.peak_usage_hours_for_api(db, days=days)
    tool_usage = analytics_module.tool_usage_for_api(db, days=days)
    model_usage = analytics_module.model_usage_for_api(db, days=days)
    usage_by_role = analytics_module.usage_by_role_for_api(db, days=days)
    usage_by_department = analytics_module.usage_by_department_for_api(db, days=days)
    top_users_by_cost = analytics_module.top_users_by_cost(db, limit=10, days=days)
    top_tools_by_failures = analytics_module.top_tools_by_failures(db, limit=10, days=days)
    insights = analytics_module.get_insights(db, days=days)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "days": days,
            "allowed_days": ALLOWED_DAYS,
            "metrics": metrics_kpis,
            "cost_trend": cost_trend,
            "peak_hours": peak_hours,
            "tool_usage": tool_usage,
            "model_usage": model_usage,
            "usage_by_role": usage_by_role,
            "usage_by_department": usage_by_department,
            "top_users_by_cost": top_users_by_cost,
            "top_tools_by_failures": top_tools_by_failures,
            "insights": insights,
        },
    )
