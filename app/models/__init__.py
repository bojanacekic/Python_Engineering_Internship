"""SQLAlchemy models for telemetry and employees."""
from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee

__all__ = ["TelemetryEvent", "Employee"]
