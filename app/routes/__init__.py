"""API and page routes."""
from fastapi import APIRouter
from app.routes import analytics, metrics, pages

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

page_router = APIRouter(tags=["pages"])
page_router.include_router(pages.router)
