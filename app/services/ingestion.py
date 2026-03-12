"""
Ingestion pipeline: read raw telemetry JSON/JSONL and employee CSV; clean and normalize;
store in SQLite; build session and daily aggregates.

- Supports flat JSONL, batched logEvents, and nested JSON message fields. Malformed rows
  are logged and skipped; ingestion is rerunnable (deduplication by event_id and employee_id).
- CSV input is validated with safe defaults for missing columns. Joins telemetry to employees
  by email when present, else by user_id. Includes error handling and structured logging.
"""
import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import settings
from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee
from app.models.sessions_summary import SessionSummary
from app.models.daily_metrics import DailyMetric

logger = logging.getLogger(__name__)

# Session gap threshold (minutes): gap larger than this starts a new session
SESSION_GAP_MINUTES = 30


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse ISO timestamp string; return None on failure."""
    if value is None:
        return None
    s = str(value).strip().rstrip("Z").replace("Z", "")
    try:
        if "." in s:
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _safe_decode_message(raw: Any) -> Dict[str, Any]:
    """If raw is a JSON string, decode and return dict; else return empty dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_event(raw: Dict[str, Any], line_num: int) -> Optional[Dict[str, Any]]:
    """
    Extract normalized event from raw dict. Handles optional 'message' as JSON string.
    Returns dict with event_id, timestamp, user_id, event_type, duration_ms, error_code, email (optional).
    Returns None if required fields missing or invalid.
    """
    # Merge decoded message into event for field extraction
    message = _safe_decode_message(raw.get("message"))
    merged = dict(raw)
    merged.update(message)

    event_id = merged.get("event_id")
    if not event_id:
        logger.warning("Line %s: missing event_id", line_num)
        return None
    ts = _parse_timestamp(merged.get("timestamp"))
    if not ts:
        logger.warning("Line %s: missing or invalid timestamp (event_id=%s)", line_num, event_id)
        return None
    user_id = merged.get("user_id")
    if user_id is None:
        user_id = merged.get("userId") or message.get("user_id") or ""
    user_id = str(user_id)
    event_type = merged.get("event_type") or merged.get("eventType") or "unknown"
    duration_ms = merged.get("duration_ms") or merged.get("durationMs")
    if duration_ms is not None:
        try:
            duration_ms = int(duration_ms)
        except (TypeError, ValueError):
            duration_ms = None
    error_code = merged.get("error_code") or merged.get("errorCode")
    if error_code is not None:
        error_code = str(error_code)
    email = merged.get("email")
    if email is not None:
        email = str(email).strip() or None
    return {
        "event_id": event_id,
        "timestamp": ts,
        "user_id": user_id,
        "event_type": event_type,
        "duration_ms": duration_ms,
        "error_code": error_code,
        "email": email,
        "raw_payload": json.dumps(raw, ensure_ascii=False),
    }


def _iter_telemetry_events(path: Path, line_num_ref: List[int]) -> List[Dict[str, Any]]:
    """
    Yield normalized events from JSONL. Supports:
    - One JSON object per line (flat)
    - Batched: line with top-level "logEvents": [ ... ]
    line_num_ref[0] is updated to current line number for logging.
    """
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_num_ref[0] = line_num
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("Line %s: invalid JSON - %s", line_num, e)
                continue
            if not isinstance(data, dict):
                logger.warning("Line %s: expected JSON object", line_num)
                continue
            # Batched format
            log_events = data.get("logEvents")
            if isinstance(log_events, list):
                for i, evt in enumerate(log_events):
                    if not isinstance(evt, dict):
                        continue
                    norm = _normalize_event(evt, line_num)
                    if norm:
                        out.append(norm)
                continue
            # Single event per line
            norm = _normalize_event(data, line_num)
            if norm:
                out.append(norm)
    return out


REQUIRED_CSV_FIELDS = ("employee_id", "name", "email", "department", "role")


def load_employees_into_db(db: Session, path: Optional[Path] = None) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Load employees from CSV into DB (skip duplicates). Uses safe defaults for missing columns.
    Returns email -> employees.id, employee_id -> employees.id. Rerunnable: skips existing employee_id.
    """
    path = path or Path(settings.employees_csv_path)
    email_to_id: Dict[str, int] = {}
    user_id_to_id: Dict[str, int] = {}
    if not path.exists():
        logger.warning("Employees file not found: %s", path)
        return email_to_id, user_id_to_id
    try:
        existing = {row[0]: row[1] for row in db.query(Employee.employee_id, Employee.id).all()}
    except Exception as e:
        logger.exception("DB query failed when loading employees: %s", e)
        return email_to_id, user_id_to_id
    try:
        f = open(path, "r", encoding="utf-8", newline="")
    except OSError as e:
        logger.exception("Could not open employees CSV %s: %s", path, e)
        return email_to_id, user_id_to_id
    with f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not all(col in (reader.fieldnames or []) for col in REQUIRED_CSV_FIELDS):
            logger.warning("CSV missing expected columns (expected at least: %s)", REQUIRED_CSV_FIELDS)
        for row in reader:
            eid = (row.get("employee_id") or "").strip()
            if not eid or eid in existing:
                if eid:
                    user_id_to_id[eid] = existing[eid]
                continue
            emp = Employee(
                employee_id=eid,
                name=(row.get("name") or "").strip()[:256],
                email=(row.get("email") or "").strip()[:256],
                department=(row.get("department") or "").strip()[:128],
                role=(row.get("role") or "").strip()[:64],
            )
            db.add(emp)
            db.flush()
            existing[eid] = emp.id
            user_id_to_id[eid] = emp.id
            email = (emp.email or "").strip()
            if email:
                email_to_id[email] = emp.id
        try:
            db.commit()
        except Exception as e:
            logger.exception("Commit failed after loading employees: %s", e)
            db.rollback()
            return email_to_id, user_id_to_id
    # Reload email_to_id from DB for all employees (in case we only had some new)
    try:
        for email, pk in db.query(Employee.email, Employee.id).filter(Employee.email.isnot(None)).all():
            if email:
                email_to_id[email.strip()] = pk
        for eid, pk in db.query(Employee.employee_id, Employee.id).all():
            user_id_to_id[str(eid)] = pk
    except Exception as e:
        logger.exception("DB query failed when building employee lookups: %s", e)
    return email_to_id, user_id_to_id


def load_telemetry_into_db(
    db: Session,
    path: Optional[Path] = None,
    email_to_id: Optional[Dict[str, int]] = None,
    user_id_to_id: Optional[Dict[str, int]] = None,
) -> Tuple[int, int, int]:
    """
    Read telemetry_logs.jsonl, normalize, join to employees (by email or user_id), insert into telemetry_events.
    Returns (loaded, skipped, errors).
    """
    path = path or Path(settings.telemetry_logs_path)
    email_to_id = email_to_id or {}
    user_id_to_id = user_id_to_id or {}
    if not path.exists():
        logger.warning("Telemetry file not found: %s", path)
        return 0, 0, 0
    line_num_ref: List[int] = [0]
    events = _iter_telemetry_events(path, line_num_ref)
    existing_ids = {row[0] for row in db.query(TelemetryEvent.event_id).all()}
    loaded = 0
    skipped = 0
    errors = 0
    for rec in events:
        if rec["event_id"] in existing_ids:
            skipped += 1
            continue
        employee_id = None
        if rec.get("email") and rec["email"] in email_to_id:
            employee_id = email_to_id[rec["email"]]
        elif rec["user_id"] in user_id_to_id:
            employee_id = user_id_to_id[rec["user_id"]]
        try:
            ev = TelemetryEvent(
                event_id=rec["event_id"],
                timestamp=rec["timestamp"],
                user_id=rec["user_id"],
                employee_id=employee_id,
                event_type=rec["event_type"],
                duration_ms=rec.get("duration_ms"),
                error_code=rec.get("error_code"),
                raw_payload=rec.get("raw_payload"),
            )
            db.add(ev)
            existing_ids.add(rec["event_id"])
            loaded += 1
        except Exception as e:
            logger.exception("Insert failed for event_id=%s: %s", rec["event_id"], e)
            errors += 1
    db.commit()
    return loaded, skipped, errors


def _build_sessions(db: Session, events: List[Tuple[str, datetime, str]]) -> int:
    """Group events by user, split on session_start or gap > SESSION_GAP_MINUTES. Insert SessionSummary. Returns count."""
    from collections import defaultdict
    by_user: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)
    for user_id, ts, etype in events:
        by_user[user_id].append((ts, etype))
    for user_id in by_user:
        by_user[user_id].sort(key=lambda x: x[0])
    count = 0
    for user_id, list_ts_type in by_user.items():
        session_start = None
        session_end = None
        event_count = 0
        for ts, etype in list_ts_type:
            gap_exceeded = session_start is not None and session_end is not None and (ts - session_end).total_seconds() > SESSION_GAP_MINUTES * 60
            if etype == "session_start" or gap_exceeded:
                if session_start is not None:
                    dur = (session_end - session_start).total_seconds() if session_end else 0
                    db.add(SessionSummary(
                        user_id=user_id,
                        session_start_ts=session_start,
                        session_end_ts=session_end or session_start,
                        event_count=event_count,
                        duration_seconds=dur,
                    ))
                    count += 1
                session_start = ts
                session_end = ts
                event_count = 1
            else:
                if session_start is not None:
                    event_count += 1
                    session_end = ts
                else:
                    session_start = ts
                    session_end = ts
                    event_count = 1
        if session_start is not None:
            dur = (session_end - session_start).total_seconds() if session_end else 0
            db.add(SessionSummary(
                user_id=user_id,
                session_start_ts=session_start,
                session_end_ts=session_end or session_start,
                event_count=event_count,
                duration_seconds=dur,
            ))
            count += 1
    db.commit()
    return count


def _build_daily_metrics(db: Session) -> int:
    """Compute daily_metrics from telemetry_events and sessions_summary. Returns count inserted."""
    from sqlalchemy import func
    from datetime import date as date_type
    # Total events per day
    day_events = db.query(
        func.date(TelemetryEvent.timestamp).label("d"),
        func.count(TelemetryEvent.id).label("c"),
    ).group_by(func.date(TelemetryEvent.timestamp)).all()
    existing = {(row[0], "total_events") for row in db.query(DailyMetric.metric_date, DailyMetric.metric_name).all()}
    count = 0
    for row in day_events:
        d = row.d if isinstance(row.d, date_type) else date_type.fromisoformat(str(row.d))
        if (d, "total_events") in existing:
            continue
        db.add(DailyMetric(metric_date=d, metric_name="total_events", value=row.c))
        count += 1
    # Unique users per day
    day_users = db.query(
        func.date(TelemetryEvent.timestamp).label("d"),
        func.count(func.distinct(TelemetryEvent.user_id)).label("c"),
    ).group_by(func.date(TelemetryEvent.timestamp)).all()
    for row in day_users:
        d = row.d if isinstance(row.d, date_type) else date_type.fromisoformat(str(row.d))
        if (d, "unique_users") in existing:
            continue
        db.add(DailyMetric(metric_date=d, metric_name="unique_users", value=row.c))
        count += 1
    # Sessions per day from sessions_summary
    day_sessions = db.query(
        func.date(SessionSummary.session_start_ts).label("d"),
        func.count(SessionSummary.id).label("c"),
    ).group_by(func.date(SessionSummary.session_start_ts)).all()
    for row in day_sessions:
        d = row.d if isinstance(row.d, date_type) else date_type.fromisoformat(str(row.d))
        if (d, "total_sessions") in existing:
            continue
        db.add(DailyMetric(metric_date=d, metric_name="total_sessions", value=row.c))
        count += 1
    db.commit()
    return count


def run_ingestion(
    db: Session,
    telemetry_path: Optional[str] = None,
    employees_path: Optional[str] = None,
    rebuild_sessions: bool = True,
    rebuild_daily_metrics: bool = True,
) -> Dict[str, Any]:
    """
    Full pipeline: load employees, load telemetry (with join), optionally rebuild sessions_summary and daily_metrics.
    Returns dict with counts: employees_loaded, telemetry_loaded, telemetry_skipped, telemetry_errors,
    sessions_inserted, daily_metrics_inserted.
    """
    tp = Path(telemetry_path) if telemetry_path else Path(settings.telemetry_logs_path)
    ep = Path(employees_path) if employees_path else Path(settings.employees_csv_path)

    email_to_id, user_id_to_id = load_employees_into_db(db, ep)
    employees_loaded = len(email_to_id)  # approximate; we loaded from CSV
    emp_count = db.query(Employee).count()
    telemetry_loaded, telemetry_skipped, telemetry_errors = load_telemetry_into_db(
        db, tp, email_to_id=email_to_id, user_id_to_id=user_id_to_id
    )

    sessions_inserted = 0
    daily_metrics_inserted = 0
    if rebuild_sessions:
        db.query(SessionSummary).delete()
        db.commit()
        events_for_sessions = [
            (r.user_id, r.timestamp, r.event_type)
            for r in db.query(TelemetryEvent.user_id, TelemetryEvent.timestamp, TelemetryEvent.event_type)
            .order_by(TelemetryEvent.timestamp)
            .all()
        ]
        sessions_inserted = _build_sessions(db, events_for_sessions)
    if rebuild_daily_metrics:
        db.query(DailyMetric).delete()
        db.commit()
        daily_metrics_inserted = _build_daily_metrics(db)

    result = {
        "employees_loaded": emp_count,
        "telemetry_loaded": telemetry_loaded,
        "telemetry_skipped": telemetry_skipped,
        "telemetry_errors": telemetry_errors,
        "sessions_inserted": sessions_inserted,
        "daily_metrics_inserted": daily_metrics_inserted,
    }
    logger.info(
        "Ingestion complete: employees=%s, telemetry_loaded=%s, skipped=%s, errors=%s, sessions=%s, daily_metrics=%s",
        result["employees_loaded"],
        result["telemetry_loaded"],
        result["telemetry_skipped"],
        result["telemetry_errors"],
        result["sessions_inserted"],
        result["daily_metrics_inserted"],
    )
    return result
