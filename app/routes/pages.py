"""
Page routes: dashboard and index. Serves Jinja2-rendered HTML.
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from fastapi import Depends
from sqlalchemy.orm import Session

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Render the main analytics dashboard with summary and charts."""
    svc = AnalyticsService(db)
    summary = svc.get_summary_stats()
    by_type = svc.get_events_by_type()
    over_time = svc.get_events_over_time(days=30)
    by_dept = svc.get_events_by_department()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "summary": summary,
            "by_type": by_type,
            "over_time": over_time,
            "by_department": by_dept,
        },
    )
