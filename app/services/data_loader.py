"""
Load telemetry_logs.jsonl and employees.csv into the SQLite database.
Handles validation and duplicate-safe upserts by event_id / employee_id.
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from config.settings import settings
from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee


class DataLoader:
    """Loads JSONL and CSV data into the database."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _parse_timestamp(self, value: str) -> datetime:
        """Parse ISO timestamp; strip trailing Z and handle microseconds."""
        s = value.rstrip("Z").replace("Z", "")
        if "." in s:
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s)

    def load_telemetry_jsonl(self, path: Optional[str] = None) -> int:
        """
        Load telemetry events from a JSONL file. Skips duplicates by event_id.
        Returns the number of new rows inserted.
        """
        filepath = Path(path or settings.telemetry_logs_path)
        if not filepath.exists():
            return 0
        existing = {row[0] for row in self.db.query(TelemetryEvent.event_id).all()}
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_id = data.get("event_id")
                if not event_id or event_id in existing:
                    continue
                ts = data.get("timestamp")
                if not ts:
                    continue
                try:
                    timestamp = self._parse_timestamp(ts)
                except (ValueError, TypeError):
                    continue
                event = TelemetryEvent(
                    event_id=event_id,
                    timestamp=timestamp,
                    user_id=str(data.get("user_id", "")),
                    event_type=data.get("event_type", "unknown"),
                    duration_ms=data.get("duration_ms"),
                    error_code=data.get("error_code"),
                    raw_payload=line,
                )
                self.db.add(event)
                existing.add(event_id)
                count += 1
        self.db.commit()
        return count

    def load_employees_csv(self, path: Optional[str] = None) -> int:
        """
        Load employees from CSV. Skips duplicates by employee_id.
        Returns the number of new rows inserted.
        """
        filepath = Path(path or settings.employees_csv_path)
        if not filepath.exists():
            return 0
        existing = {row[0] for row in self.db.query(Employee.employee_id).all()}
        count = 0
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                eid = row.get("employee_id")
                if not eid or eid in existing:
                    continue
                emp = Employee(
                    employee_id=eid,
                    name=row.get("name", ""),
                    email=row.get("email", ""),
                    department=row.get("department", ""),
                    role=row.get("role", ""),
                )
                self.db.add(emp)
                existing.add(eid)
                count += 1
        self.db.commit()
        return count

    def load_all(self, telemetry_path: Optional[str] = None, employees_path: Optional[str] = None) -> dict:
        """Load both telemetry and employees. Returns counts."""
        telem_count = self.load_telemetry_jsonl(telemetry_path)
        emp_count = self.load_employees_csv(employees_path)
        return {"telemetry_loaded": telem_count, "employees_loaded": emp_count}
