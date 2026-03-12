"""
Pytest fixtures: in-memory SQLite DB, client, and sample data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.telemetry import TelemetryEvent  # noqa: F401 - register with Base
from app.models.employee import Employee  # noqa: F401 - register with Base
from app.main import create_app


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory SQLite engine per test. StaticPool so all connections share one DB."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a DB session that rolls back after the test."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """FastAPI test client with overridden get_db to use in-memory DB."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
