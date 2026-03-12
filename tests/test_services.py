"""
Service tests: DataLoader and AnalyticsService with in-memory DB.
"""
from datetime import datetime, timedelta
import json
import csv
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee
from app.models.sessions_summary import SessionSummary
from app.models.daily_metrics import DailyMetric
from app.services.data_loader import DataLoader
from app.services.analytics_service import AnalyticsService
from app.services.ingestion import run_ingestion
from app.services import analytics as analytics_module


@pytest.fixture
def session():
    """In-memory DB session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_data_loader_telemetry_jsonl(session):
    """DataLoader loads valid JSONL and skips duplicates."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({
            "event_id": "e1",
            "timestamp": "2024-01-15T10:00:00Z",
            "user_id": "1",
            "event_type": "session_start",
        }) + "\n")
        f.write(json.dumps({
            "event_id": "e2",
            "timestamp": "2024-01-15T10:01:00Z",
            "user_id": "1",
            "event_type": "completion_request",
            "duration_ms": 200,
        }) + "\n")
        path = f.name
    try:
        loader = DataLoader(session)
        count = loader.load_telemetry_jsonl(path)
        assert count == 2
        assert session.query(TelemetryEvent).count() == 2
        # Duplicate run should not add
        count2 = loader.load_telemetry_jsonl(path)
        assert count2 == 0
        assert session.query(TelemetryEvent).count() == 2
    finally:
        Path(path).unlink(missing_ok=True)


def test_data_loader_employees_csv(session):
    """DataLoader loads CSV and skips duplicates."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", newline="", delete=False) as f:
        w = csv.DictWriter(f, fieldnames=["employee_id", "name", "email", "department", "role"])
        w.writeheader()
        w.writerow({
            "employee_id": "1",
            "name": "Alice",
            "email": "alice@co.com",
            "department": "Eng",
            "role": "Intern",
        })
        path = f.name
    try:
        loader = DataLoader(session)
        count = loader.load_employees_csv(path)
        assert count == 1
        assert session.query(Employee).count() == 1
        count2 = loader.load_employees_csv(path)
        assert count2 == 0
    finally:
        Path(path).unlink(missing_ok=True)


def test_analytics_summary(session):
    """AnalyticsService.get_summary_stats returns correct counts."""
    session.add(
        TelemetryEvent(event_id="e1", timestamp=datetime.utcnow(), user_id="1", event_type="session_start")
    )
    session.add(
        TelemetryEvent(event_id="e2", timestamp=datetime.utcnow(), user_id="2", event_type="session_start")
    )
    session.add(Employee(employee_id="1", name="A", email="a@a.com", department="D1", role="R1"))
    session.commit()

    svc = AnalyticsService(session)
    summary = svc.get_summary_stats()
    assert summary["total_events"] == 2
    assert summary["total_employees"] == 1
    assert summary["unique_users_with_events"] == 2
    assert "session_start" in summary["event_types"]


def test_analytics_events_by_type(session):
    """AnalyticsService.get_events_by_type returns dict of type -> count."""
    session.add(
        TelemetryEvent(event_id="e1", timestamp=datetime.utcnow(), user_id="1", event_type="session_start")
    )
    session.add(
        TelemetryEvent(event_id="e2", timestamp=datetime.utcnow(), user_id="1", event_type="session_start")
    )
    session.add(
        TelemetryEvent(event_id="e3", timestamp=datetime.utcnow(), user_id="1", event_type="error")
    )
    session.commit()

    svc = AnalyticsService(session)
    by_type = svc.get_events_by_type()
    assert by_type["session_start"] == 2
    assert by_type["error"] == 1


def test_ingestion_run(session):
    """run_ingestion returns dict with expected keys and does not raise."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({
            "event_id": "ing1",
            "timestamp": "2024-01-15T10:00:00Z",
            "user_id": "1",
            "event_type": "session_start",
        }) + "\n")
        jsonl_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", newline="", delete=False) as f:
        w = csv.DictWriter(f, fieldnames=["employee_id", "name", "email", "department", "role"])
        w.writeheader()
        w.writerow({"employee_id": "1", "name": "A", "email": "a@a.com", "department": "D", "role": "R"})
        csv_path = f.name
    try:
        result = run_ingestion(
            session,
            telemetry_path=jsonl_path,
            employees_path=csv_path,
            rebuild_sessions=True,
            rebuild_daily_metrics=True,
        )
        assert isinstance(result, dict)
        assert "employees_loaded" in result
        assert "telemetry_loaded" in result
        assert "telemetry_skipped" in result
        assert "telemetry_errors" in result
        assert "sessions_inserted" in result
        assert "daily_metrics_inserted" in result
        assert result["telemetry_loaded"] >= 0
    finally:
        Path(jsonl_path).unlink(missing_ok=True)
        Path(csv_path).unlink(missing_ok=True)


def test_dashboard_kpis_keys(session):
    """dashboard_kpis returns expected KPI keys."""
    session.add(
        TelemetryEvent(event_id="k1", timestamp=datetime.utcnow(), user_id="1", event_type="session_start")
    )
    session.commit()
    kpis = analytics_module.dashboard_kpis(session, days=30)
    assert "total_events" in kpis
    assert "estimated_cost_usd" in kpis
    assert "total_tokens" in kpis
    assert "active_users" in kpis


def test_narrative_insights_structure(session):
    """narrative_insights returns bullets list and generated_at."""
    session.add(
        TelemetryEvent(event_id="n1", timestamp=datetime.utcnow(), user_id="1", event_type="session_start")
    )
    session.commit()
    ni = analytics_module.narrative_insights(session, days=30)
    assert hasattr(ni, "bullets")
    assert isinstance(ni.bullets, list)
    assert len(ni.bullets) <= 8
    assert hasattr(ni, "generated_at")
    assert isinstance(ni.generated_at, str)
