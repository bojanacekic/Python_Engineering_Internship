"""
Analytics aggregations using Pandas and SQLAlchemy.
Provides summary stats, events by type, events over time, and by department.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee


class AnalyticsService:
    """Compute analytics over telemetry and employees."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary_stats(self) -> Dict[str, Any]:
        """Return high-level summary: total events, employees, unique users, event types, date range."""
        total_events = self.db.query(func.count(TelemetryEvent.id)).scalar() or 0
        total_employees = self.db.query(func.count(Employee.id)).scalar() or 0
        unique_users = (
            self.db.query(func.count(func.distinct(TelemetryEvent.user_id))).scalar() or 0
        )
        event_types = [
            r[0]
            for r in self.db.query(TelemetryEvent.event_type)
            .distinct()
            .all()
        ]
        min_max = self.db.query(
            func.min(TelemetryEvent.timestamp),
            func.max(TelemetryEvent.timestamp),
        ).first()
        date_range = {"min": "", "max": ""}
        if min_max and min_max[0] and min_max[1]:
            date_range["min"] = min_max[0].isoformat()[:10]
            date_range["max"] = min_max[1].isoformat()[:10]
        return {
            "total_events": total_events,
            "total_employees": total_employees,
            "unique_users_with_events": unique_users,
            "event_types": sorted(event_types),
            "date_range": date_range,
        }

    def get_events_by_type(self) -> Dict[str, int]:
        """Return counts per event_type."""
        rows = (
            self.db.query(TelemetryEvent.event_type, func.count(TelemetryEvent.id))
            .group_by(TelemetryEvent.event_type)
            .all()
        )
        return {r[0]: r[1] for r in rows}

    def get_events_over_time(self, days: Optional[int] = 30) -> List[Dict[str, Any]]:
        """Return daily event counts. Limit to last `days` if set."""
        # SQLite date truncation
        if days:
            cutoff = self.db.query(func.max(TelemetryEvent.timestamp)).scalar()
            if cutoff:
                from datetime import timedelta
                cutoff = cutoff - timedelta(days=days)
                rows = (
                    self.db.query(
                        func.date(TelemetryEvent.timestamp).label("day"),
                        func.count(TelemetryEvent.id).label("count"),
                    )
                    .filter(TelemetryEvent.timestamp >= cutoff)
                    .group_by(func.date(TelemetryEvent.timestamp))
                    .order_by(func.date(TelemetryEvent.timestamp))
                    .all()
                )
            else:
                rows = []
        else:
            rows = (
                self.db.query(
                    func.date(TelemetryEvent.timestamp).label("day"),
                    func.count(TelemetryEvent.id).label("count"),
                )
                .group_by(func.date(TelemetryEvent.timestamp))
                .order_by(func.date(TelemetryEvent.timestamp))
                .all()
            )
        return [{"date": str(r.day), "count": r.count} for r in rows]

    def get_events_by_department(self) -> List[Dict[str, Any]]:
        """Return event counts per department (join employees)."""
        rows = (
            self.db.query(Employee.department, func.count(TelemetryEvent.id))
            .join(TelemetryEvent, Employee.employee_id == TelemetryEvent.user_id)
            .group_by(Employee.department)
            .all()
        )
        return [{"department": r[0], "count": r[1]} for r in rows]

    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return top users by event count."""
        rows = (
            self.db.query(TelemetryEvent.user_id, func.count(TelemetryEvent.id).label("count"))
            .group_by(TelemetryEvent.user_id)
            .order_by(func.count(TelemetryEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [{"user_id": r[0], "count": r[1]} for r in rows]
