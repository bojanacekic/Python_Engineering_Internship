"""
FastAPI application factory. Registers routes, static files, and startup logic.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from app.database import init_db
from app.routes import api_router, page_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_title,
        description="Analytics platform for Claude Code telemetry",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
    )

    # Ensure DB tables exist
    init_db()

    # Static assets
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Routes
    app.include_router(page_router)
    app.include_router(api_router)

    return app
