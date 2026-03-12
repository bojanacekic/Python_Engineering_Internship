"""
API tests: analytics endpoints, dashboard, load-data.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee


def _add_sample_data(session: Session) -> None:
    """Insert minimal sample telemetry and employees."""
    base = datetime.utcnow() - timedelta(days=5)
    session.add(
        TelemetryEvent(
            event_id="evt_001",
            timestamp=base,
            user_id="1",
            event_type="session_start",
        )
    )
    session.add(
        TelemetryEvent(
            event_id="evt_002",
            timestamp=base,
            user_id="1",
            event_type="completion_request",
            duration_ms=100,
        )
    )
    session.add(Employee(employee_id="1", name="Test User", email="test@co.com", department="Eng", role="Intern"))
    session.commit()


def test_dashboard_returns_html(client):
    """Dashboard page returns HTML."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert b"Claude Code Telemetry" in r.content or b"Telemetry" in r.content


def test_summary_empty(client):
    """Summary with no data returns zeros."""
    r = client.get("/api/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 0
    assert data["total_employees"] == 0


def test_summary_with_data(client, db_engine):
    """Summary reflects inserted data."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    session = Session()
    _add_sample_data(session)
    session.close()

    r = client.get("/api/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 2
    assert data["total_employees"] == 1
    assert data["unique_users_with_events"] == 1


def test_events_by_type(client, db_engine):
    """Events by type returns counts per type."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    session = Session()
    _add_sample_data(session)
    session.close()

    r = client.get("/api/analytics/events-by-type")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert "session_start" in data["by_type"]
    assert "completion_request" in data["by_type"]


def test_events_over_time_invalid_days(client):
    """Events over time rejects invalid days."""
    r = client.get("/api/analytics/events-over-time?days=0")
    assert r.status_code == 400
    r = client.get("/api/analytics/events-over-time?days=400")
    assert r.status_code == 400


def test_load_data_no_files(client):
    """Load data with no files returns zero counts (no error)."""
    r = client.post("/api/analytics/load-data")
    assert r.status_code == 200
    data = r.json()
    assert "telemetry_loaded" in data
    assert "employees_loaded" in data
