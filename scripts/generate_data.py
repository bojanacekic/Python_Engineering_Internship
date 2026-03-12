"""
Generate fake Claude Code telemetry and employee data for development and demos.

Produces (in data/raw/):
- telemetry_logs.jsonl: one JSON object per line or compatible batched format
- employees.csv: employee_id, name, email, department, role

Run from project root: python -m scripts.generate_data
Or: python generate_fake_data.py (wrapper)
"""
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Project root: parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

EVENT_TYPES = [
    "session_start",
    "session_end",
    "completion_request",
    "completion_response",
    "edit_request",
    "error",
    "feature_used",
]

DEPARTMENTS = ["Engineering", "Product", "Data", "Design", "QA"]
ROLES = ["Intern", "Junior", "Mid", "Senior", "Lead"]


def generate_employees(n: int = 50) -> List[dict]:
    """Generate n fake employees with id, name, email, department, role."""
    first = ["Alex", "Jordan", "Sam", "Casey", "Morgan", "Riley", "Quinn", "Avery", "Blake", "Cameron"]
    last = ["Smith", "Lee", "Chen", "Williams", "Brown", "Davis", "Wilson", "Taylor", "Martinez", "Garcia"]
    employees = []
    for i in range(1, n + 1):
        name = f"{random.choice(first)} {random.choice(last)}"
        email = f"{name.lower().replace(' ', '.')}@company.com"
        employees.append({
            "employee_id": str(i),
            "name": name,
            "email": email,
            "department": random.choice(DEPARTMENTS),
            "role": random.choice(ROLES),
        })
    return employees


def generate_telemetry_events(n: int, employee_ids: List[str], days_back: int = 30) -> List[dict]:
    """Generate n telemetry events with timestamps over the last days_back days."""
    events = []
    base = datetime.utcnow() - timedelta(days=days_back)
    for i in range(n):
        ts = base + timedelta(
            seconds=random.randint(0, days_back * 24 * 3600),
            milliseconds=random.randint(0, 999),
        )
        user_id = random.choice(employee_ids)
        event_type = random.choice(EVENT_TYPES)
        payload = {
            "event_id": f"evt_{i + 1:06d}",
            "timestamp": ts.isoformat() + "Z",
            "user_id": user_id,
            "event_type": event_type,
        }
        if event_type in ("completion_request", "completion_response", "edit_request"):
            payload["duration_ms"] = random.randint(50, 5000)
        if event_type == "error":
            payload["error_code"] = random.choice(["TIMEOUT", "RATE_LIMIT", "PARSE_ERROR", "UNKNOWN"])
        events.append(payload)
    return sorted(events, key=lambda e: e["timestamp"])


def write_jsonl(path: Path, records: List[dict]) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    """Write CSV with header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main(
    out_dir: Path = DATA_RAW,
    num_employees: int = 50,
    num_events: int = 2000,
    days_back: int = 30,
) -> None:
    """Generate telemetry_logs.jsonl and employees.csv in out_dir (default data/raw/)."""
    out_dir = Path(out_dir)
    employees = generate_employees(num_employees)
    employee_ids = [e["employee_id"] for e in employees]
    events = generate_telemetry_events(num_events, employee_ids, days_back=days_back)

    out_telemetry = out_dir / "telemetry_logs.jsonl"
    out_employees = out_dir / "employees.csv"

    write_jsonl(out_telemetry, events)
    write_csv(out_employees, employees, fieldnames=["employee_id", "name", "email", "department", "role"])

    print(f"Wrote {len(events)} events to {out_telemetry}")
    print(f"Wrote {len(employees)} employees to {out_employees}")


if __name__ == "__main__":
    main()
