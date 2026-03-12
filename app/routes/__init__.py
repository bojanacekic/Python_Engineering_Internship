"""API and page routes."""
from fastapi import APIRouter
from app.routes import analytics, pages

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

page_router = APIRouter(tags=["pages"])
page_router.include_router(pages.router)
