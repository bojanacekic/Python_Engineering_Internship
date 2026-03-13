"""
Analytics module: reusable, typed metrics and narrative insights for stakeholder reporting.

Metrics cover usage by role/department, trends over time, peak hours, tool/model distribution,
success rates, session duration, and top users. Outputs are API-friendly (charts and tables).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.telemetry import TelemetryEvent
from app.models.employee import Employee
from app.models.sessions_summary import SessionSummary

logger = logging.getLogger(__name__)


# ---- Typed result structures (API-friendly) ----

@dataclass
class UsageByDimension:
    """Usage (event count + duration proxy) by a dimension like role or department."""
    dimension_value: str
    event_count: int
    total_duration_ms: int
    user_count: int


@dataclass
class TrendBucket:
    """Single time bucket for trend series."""
    date: str
    event_count: int
    total_duration_ms: int


@dataclass
class HourlyBucket:
    """Usage count by hour of day (0-23)."""
    hour: int
    count: int


@dataclass
class DistributionBucket:
    """Label + count for pie/bar charts."""
    label: str
    count: int


@dataclass
class SuccessFailureRate:
    """Success vs failure for a tool/event type."""
    tool: str
    success_count: int
    failure_count: int
    success_rate_pct: float


@dataclass
class NarrativeInsights:
    """Auto-generated bullet insights in plain English."""
    bullets: List[str]
    generated_at: str


# ---- Helpers ----

def _safe_json_field(payload_str: Optional[str], key: str) -> Optional[str]:
    """Extract a string field from raw_payload JSON if present."""
    if not payload_str:
        return None
    try:
        data = json.loads(payload_str)
        if isinstance(data, dict):
            val = data.get(key)
            return str(val).strip() if val is not None else None
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _extract_model(payload_str: Optional[str]) -> str:
    """Extract model name from raw_payload; default to 'default'."""
    model = _safe_json_field(payload_str, "model") or _safe_json_field(payload_str, "model_id")
    return model if model else "default"


# ---- Core metrics ----

def usage_by_role(db: Session, days: Optional[int] = 30) -> List[UsageByDimension]:
    """Usage (event count + total duration) by employee role. Proxy for token/activity by level."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            Employee.role,
            func.count(TelemetryEvent.id).label("event_count"),
            func.coalesce(func.sum(TelemetryEvent.duration_ms), 0).label("duration_ms"),
            func.count(func.distinct(TelemetryEvent.user_id)).label("user_count"),
        )
        .join(TelemetryEvent, Employee.employee_id == TelemetryEvent.user_id)
        .group_by(Employee.role)
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    return [
        UsageByDimension(
            dimension_value=r.role,
            event_count=r.event_count,
            total_duration_ms=int(r.duration_ms),
            user_count=r.user_count,
        )
        for r in rows
    ]


def usage_by_department(db: Session, days: Optional[int] = 30) -> List[UsageByDimension]:
    """Usage by department (practice). Same shape as usage_by_role."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            Employee.department,
            func.count(TelemetryEvent.id).label("event_count"),
            func.coalesce(func.sum(TelemetryEvent.duration_ms), 0).label("duration_ms"),
            func.count(func.distinct(TelemetryEvent.user_id)).label("user_count"),
        )
        .join(TelemetryEvent, Employee.employee_id == TelemetryEvent.user_id)
        .group_by(Employee.department)
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    return [
        UsageByDimension(
            dimension_value=r.department,
            event_count=r.event_count,
            total_duration_ms=int(r.duration_ms),
            user_count=r.user_count,
        )
        for r in rows
    ]


def _cutoff_date(db: Session, days: Optional[int]) -> Optional[datetime]:
    """Return cutoff datetime for 'last N days' filter."""
    if not days:
        return None
    max_ts = db.query(func.max(TelemetryEvent.timestamp)).scalar()
    if not max_ts:
        return None
    return max_ts - timedelta(days=days)


def cost_trend_over_time(db: Session, days: int = 30) -> List[TrendBucket]:
    """
    Daily usage trend (event count + duration). Use as cost trend when cost data is available.
    API-friendly for line/area charts.
    """
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            func.date(TelemetryEvent.timestamp).label("day"),
            func.count(TelemetryEvent.id).label("event_count"),
            func.coalesce(func.sum(TelemetryEvent.duration_ms), 0).label("duration_ms"),
        )
        .group_by(func.date(TelemetryEvent.timestamp))
        .order_by(func.date(TelemetryEvent.timestamp))
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    return [
        TrendBucket(date=str(r.day), event_count=r.event_count, total_duration_ms=int(r.duration_ms))
        for r in rows
    ]


def peak_usage_hours(db: Session, days: Optional[int] = 30) -> List[HourlyBucket]:
    """Event count by hour of day (0-23 UTC). For peak usage heatmaps or bar charts."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            func.strftime("%H", TelemetryEvent.timestamp).label("hour"),
            func.count(TelemetryEvent.id).label("count"),
        )
        .group_by(func.strftime("%H", TelemetryEvent.timestamp))
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    out = [HourlyBucket(hour=int(r.hour) if r.hour else 0, count=r.count) for r in rows]
    out.sort(key=lambda x: x.hour)
    return out


def tool_usage_distribution(db: Session, days: Optional[int] = 30) -> List[DistributionBucket]:
    """Most common tool/action usage (event_type). For pie or bar charts."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(TelemetryEvent.event_type, func.count(TelemetryEvent.id).label("count"))
        .group_by(TelemetryEvent.event_type)
        .order_by(func.count(TelemetryEvent.id).desc())
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    return [DistributionBucket(label=r.event_type, count=r.count) for r in rows]


def model_usage_distribution(db: Session, days: Optional[int] = 30) -> List[DistributionBucket]:
    """Model usage from raw_payload when present; else 'default'. For pie chart."""
    cutoff = _cutoff_date(db, days)
    q = db.query(TelemetryEvent.raw_payload).filter(TelemetryEvent.raw_payload.isnot(None))
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    counts: Dict[str, int] = {}
    for (payload,) in rows:
        model = _extract_model(payload)
        counts[model] = counts.get(model, 0) + 1
    if not counts:
        # No raw_payload: treat all as "default" (single bucket)
        q2 = db.query(func.count(TelemetryEvent.id))
        if cutoff:
            q2 = q2.filter(TelemetryEvent.timestamp >= cutoff)
        total = q2.scalar() or 0
        return [DistributionBucket(label="default", count=total)] if total else [DistributionBucket(label="default", count=0)]
    return [DistributionBucket(label=k, count=v) for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def tool_success_failure_rates(db: Session, days: Optional[int] = 30) -> List[SuccessFailureRate]:
    """Per event_type: success vs failure (failure = has error_code or event_type=='error')."""
    cutoff = _cutoff_date(db, days)
    q = db.query(
        TelemetryEvent.event_type,
        func.count(TelemetryEvent.id).label("total"),
        func.sum(case((TelemetryEvent.error_code.isnot(None), 1), else_=0)).label("with_error"),
    ).group_by(TelemetryEvent.event_type)
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    out: List[SuccessFailureRate] = []
    for r in rows:
        total = int(r.total or 0)
        with_error = int(r.with_error or 0)
        if r.event_type == "error":
            fail, succ = total, 0
        else:
            fail, succ = with_error, total - with_error
        rate = (100.0 * succ / total) if total else 0.0
        out.append(SuccessFailureRate(tool=r.event_type, success_count=succ, failure_count=fail, success_rate_pct=round(rate, 1)))
    return out


def average_session_duration(db: Session, days: Optional[int] = 30) -> Optional[float]:
    """Mean session duration in seconds. Returns None if no sessions."""
    cutoff = _cutoff_date(db, days)
    q = db.query(func.avg(SessionSummary.duration_seconds)).filter(
        SessionSummary.duration_seconds.isnot(None)
    )
    if cutoff:
        q = q.filter(SessionSummary.session_start_ts >= cutoff)
    val = q.scalar()
    return round(float(val), 2) if val is not None else None


def top_users_activity(db: Session, limit: int = 10, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Top users by event count. Optional join to employee name/department."""
    cutoff = _cutoff_date(db, days)
    subq = (
        db.query(
            TelemetryEvent.user_id,
            func.count(TelemetryEvent.id).label("event_count"),
        )
        .group_by(TelemetryEvent.user_id)
    )
    if cutoff:
        subq = subq.filter(TelemetryEvent.timestamp >= cutoff)
    subq = subq.subquery()
    q = (
        db.query(
            subq.c.user_id,
            subq.c.event_count,
            Employee.name,
            Employee.department,
        )
        .outerjoin(Employee, Employee.employee_id == subq.c.user_id)
        .order_by(subq.c.event_count.desc())
        .limit(limit)
    )
    rows = q.all()
    return [
        {
            "user_id": r.user_id,
            "event_count": r.event_count,
            "name": r.name or None,
            "department": r.department or None,
        }
        for r in rows
    ]


def top_departments_by_usage(db: Session, limit: int = 10, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Top departments by event count."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            Employee.department,
            func.count(TelemetryEvent.id).label("event_count"),
            func.count(func.distinct(TelemetryEvent.user_id)).label("user_count"),
        )
        .join(TelemetryEvent, Employee.employee_id == TelemetryEvent.user_id)
        .group_by(Employee.department)
        .order_by(func.count(TelemetryEvent.id).desc())
        .limit(limit)
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    return [
        {"department": r.department, "event_count": r.event_count, "user_count": r.user_count}
        for r in rows
    ]


# ---- Dashboard KPIs (cost/tokens are estimated from duration when not in schema) ----

# Proxy: 1 min duration ≈ 500 tokens, $0.001 per 1k tokens → estimated_cost = total_duration_ms/60000 * 500 * 0.001/1000
def dashboard_kpis(db: Session, days: int = 30) -> Dict[str, Any]:
    """Return total_events, estimated_cost (USD), total_tokens (proxy), active_users."""
    cutoff = _cutoff_date(db, days)
    q_events = db.query(func.count(TelemetryEvent.id))
    q_duration = db.query(func.coalesce(func.sum(TelemetryEvent.duration_ms), 0))
    q_users = db.query(func.count(func.distinct(TelemetryEvent.user_id)))
    if cutoff:
        q_events = q_events.filter(TelemetryEvent.timestamp >= cutoff)
        q_duration = q_duration.filter(TelemetryEvent.timestamp >= cutoff)
        q_users = q_users.filter(TelemetryEvent.timestamp >= cutoff)
    total_events = q_events.scalar() or 0
    total_duration_ms = int(q_duration.scalar() or 0)
    active_users = q_users.scalar() or 0
    # Proxy: 1 event ≈ 300 tokens if no duration; else duration_ms/1000 * 60 tokens/sec
    total_tokens = total_duration_ms // 1000 * 60 if total_duration_ms > 0 else total_events * 300
    # Estimated cost: $0.002 per 1k tokens
    estimated_cost_usd = round(total_tokens / 1000 * 0.002, 2)
    return {
        "total_events": total_events,
        "estimated_cost_usd": estimated_cost_usd,
        "total_tokens": total_tokens,
        "active_users": active_users,
    }


def top_users_by_cost(db: Session, limit: int = 10, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Top users by estimated cost (duration_ms sum as proxy). Includes name, department, event_count, estimated_cost_usd."""
    cutoff = _cutoff_date(db, days)
    subq = (
        db.query(
            TelemetryEvent.user_id,
            func.count(TelemetryEvent.id).label("event_count"),
            func.coalesce(func.sum(TelemetryEvent.duration_ms), 0).label("duration_ms"),
        )
        .group_by(TelemetryEvent.user_id)
    )
    if cutoff:
        subq = subq.filter(TelemetryEvent.timestamp >= cutoff)
    subq = subq.subquery()
    q = (
        db.query(
            subq.c.user_id,
            subq.c.event_count,
            subq.c.duration_ms,
            Employee.name,
            Employee.department,
        )
        .outerjoin(Employee, Employee.employee_id == subq.c.user_id)
        .order_by(subq.c.duration_ms.desc())
        .limit(limit)
    )
    rows = q.all()
    out = []
    for r in rows:
        dur_ms = int(r.duration_ms or 0)
        tokens = dur_ms // 1000 * 60 if dur_ms > 0 else r.event_count * 300
        cost = round(tokens / 1000 * 0.002, 2)
        out.append({
            "user_id": r.user_id,
            "name": r.name or "—",
            "department": r.department or "—",
            "event_count": r.event_count,
            "estimated_cost_usd": cost,
        })
    return out


def top_tools_by_failures(db: Session, limit: int = 10, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Top tools by failure count (for table). Sorted by failure_count desc."""
    rates = tool_success_failure_rates(db, days=days)
    sorted_rates = sorted([r for r in rates if r.failure_count > 0], key=lambda x: -x.failure_count)
    return [
        {"tool": r.tool, "failure_count": r.failure_count, "success_count": r.success_count, "success_rate_pct": r.success_rate_pct}
        for r in sorted_rates[:limit]
    ]


# ---- Advanced statistical analysis (bonus) ----

_WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def usage_by_weekday(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """
    Event count by day of week (Monday=0 .. Sunday=6). API-friendly list of {weekday, count}.
    SQLite strftime('%w') gives 0=Sunday; we map to Mon–Sun order.
    """
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            func.strftime("%w", TelemetryEvent.timestamp).label("dow"),
            func.count(TelemetryEvent.id).label("count"),
        )
        .group_by(func.strftime("%w", TelemetryEvent.timestamp))
    )
    if cutoff:
        q = q.filter(TelemetryEvent.timestamp >= cutoff)
    rows = q.all()
    # SQLite %w: 0=Sun, 1=Mon, ..., 6=Sat. Map to index 0=Mon .. 6=Sun: (int(dow) + 6) % 7
    by_index: Dict[int, int] = {}
    for r in rows:
        dow = int(r.dow) if r.dow is not None else 0
        idx = (dow + 6) % 7
        by_index[idx] = by_index.get(idx, 0) + r.count
    return [
        {"weekday": _WEEKDAY_NAMES[i], "count": by_index.get(i, 0)}
        for i in range(7)
    ]


def average_session_duration_by_department(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Mean session duration in seconds by department. Joins SessionSummary to Employee."""
    cutoff = _cutoff_date(db, days)
    q = (
        db.query(
            Employee.department,
            func.avg(SessionSummary.duration_seconds).label("avg_seconds"),
            func.count(SessionSummary.id).label("session_count"),
        )
        .join(SessionSummary, SessionSummary.user_id == Employee.employee_id)
        .filter(SessionSummary.duration_seconds.isnot(None))
        .group_by(Employee.department)
    )
    if cutoff:
        q = q.filter(SessionSummary.session_start_ts >= cutoff)
    rows = q.all()
    return [
        {
            "department": r.department or "—",
            "avg_duration_seconds": round(float(r.avg_seconds), 2) if r.avg_seconds is not None else None,
            "session_count": r.session_count,
        }
        for r in rows
    ]


def cost_by_department(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Estimated cost (USD) and event count per department. Same cost proxy as dashboard KPIs."""
    depts = usage_by_department(db, days=days)
    out: List[Dict[str, Any]] = []
    for u in depts:
        dur_ms = u.total_duration_ms
        tokens = dur_ms // 1000 * 60 if dur_ms > 0 else u.event_count * 300
        cost = round(tokens / 1000 * 0.002, 2)
        out.append({
            "department": u.dimension_value,
            "event_count": u.event_count,
            "estimated_cost_usd": cost,
            "user_count": u.user_count,
        })
    return sorted(out, key=lambda x: -x["estimated_cost_usd"])


def failure_rate_by_tool(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """Per-tool failure rate (failure_count / total * 100). For reliability analysis."""
    rates = tool_success_failure_rates(db, days=days)
    return [
        {
            "tool": r.tool,
            "failure_count": r.failure_count,
            "success_count": r.success_count,
            "success_rate_pct": r.success_rate_pct,
            "failure_rate_pct": round(100.0 - r.success_rate_pct, 1),
        }
        for r in rates
    ]


def most_volatile_day(db: Session, days: int = 30) -> Optional[Dict[str, Any]]:
    """
    The day (date) with the largest absolute percentage change in event count vs previous day.
    Returns {date, event_count, change_pct} or None if insufficient data.
    """
    trend = cost_trend_over_time(db, days=days)
    if len(trend) < 2:
        return None
    best: Optional[Dict[str, Any]] = None
    for i in range(1, len(trend)):
        prev_count = trend[i - 1].event_count
        curr_count = trend[i].event_count
        if prev_count <= 0:
            change_pct = 100.0 if curr_count > 0 else 0.0
        else:
            change_pct = 100.0 * (curr_count - prev_count) / prev_count
        if best is None or abs(change_pct) > abs(best.get("change_pct", 0)):
            best = {
                "date": trend[i].date,
                "event_count": curr_count,
                "change_pct": round(change_pct, 1),
            }
    return best


def average_events_per_active_user(db: Session, days: Optional[int] = 30) -> Optional[float]:
    """Mean events per active user over the period. Returns None if no active users."""
    kpis = dashboard_kpis(db, days=days or 30)
    active = kpis.get("active_users") or 0
    total = kpis.get("total_events") or 0
    if active <= 0:
        return None
    return round(total / active, 2)


def advanced_stats(db: Session, days: int = 30) -> Dict[str, Any]:
    """
    Single call that returns all advanced statistical analyses for dashboard and API.
    Reuses existing models and helpers.
    """
    return {
        "usage_by_weekday": usage_by_weekday(db, days=days),
        "avg_session_duration_by_department": average_session_duration_by_department(db, days=days),
        "cost_by_department": cost_by_department(db, days=days),
        "failure_rate_by_tool": failure_rate_by_tool(db, days=days),
        "most_volatile_day": most_volatile_day(db, days=days),
        "avg_events_per_active_user": average_events_per_active_user(db, days=days),
    }


# ---- Cost anomaly detection ----

def _daily_cost_usd(duration_ms: int, event_count: int) -> float:
    """Estimated cost for one day (same proxy as dashboard_kpis)."""
    tokens = duration_ms // 1000 * 60 if duration_ms > 0 else event_count * 300
    return round(tokens / 1000 * 0.002, 2)


def cost_anomalies(db: Session, days: int = 30, threshold_pct: float = 30.0) -> List[Dict[str, Any]]:
    """
    Days where daily cost exceeds the rolling (previous 7-day) average by more than threshold_pct.
    Returns list of { date, cost, deviation_percent }.
    """
    trend = cost_trend_over_time(db, days=days)
    if len(trend) < 2:
        return []
    daily_costs: List[float] = [
        _daily_cost_usd(b.total_duration_ms, b.event_count) for b in trend
    ]
    anomalies: List[Dict[str, Any]] = []
    window = 7
    for i in range(1, len(trend)):
        start = max(0, i - window)
        rolling_avg = sum(daily_costs[start:i]) / (i - start) if i > start else 0.0
        if rolling_avg <= 0:
            continue
        cost = daily_costs[i]
        if cost > rolling_avg * (1 + threshold_pct / 100.0):
            deviation_pct = round(100.0 * (cost - rolling_avg) / rolling_avg, 1)
            anomalies.append({
                "date": trend[i].date,
                "cost": cost,
                "deviation_percent": deviation_pct,
            })
    return anomalies


# ---- Simple next-day forecast (baseline) ----

def next_day_forecast(db: Session, days: int = 7) -> Dict[str, Any]:
    """
    Lightweight next-day forecast for event volume and estimated cost.

    Method: simple rolling average over the last N days of daily metrics (event_count
    and estimated cost). This is intentionally transparent and non-ML for an
    internship setting.
    """
    if days < 1:
        days = 1
    trend = cost_trend_over_time(db, days=days)
    if not trend:
        return {
            "method": "rolling_mean_last_N_days",
            "window_days": 0,
            "next_date": None,
            "expected_events": None,
            "expected_cost_usd": None,
        }
    window = min(days, len(trend))
    recent = trend[-window:]
    total_events = sum(b.event_count for b in recent)
    avg_events = total_events / window if window else 0.0
    daily_costs = [_daily_cost_usd(b.total_duration_ms, b.event_count) for b in recent]
    avg_cost = sum(daily_costs) / window if window else 0.0

    next_date: Optional[str]
    try:
        # cost_trend_over_time uses DATE(timestamp) which yields YYYY-MM-DD on SQLite.
        last_date = datetime.strptime(trend[-1].date, "%Y-%m-%d").date()
        next_date = (last_date + timedelta(days=1)).isoformat()
    except Exception:
        next_date = None

    return {
        "method": "rolling_mean_last_N_days",
        "window_days": window,
        "next_date": next_date,
        "expected_events": int(round(avg_events)) if avg_events > 0 else 0,
        "expected_cost_usd": round(avg_cost, 2) if avg_cost > 0 else 0.0,
    }


# ---- Insights (delegate to insights module) ----

def get_insights(db: Session, days: int = 30) -> NarrativeInsights:
    """
    Produce 5–8 narrative insights from computed metrics via the insights module.
    Suitable for the executive dashboard "Key Insights" section.
    """
    from app.services import insights as insights_module

    kpis = dashboard_kpis(db, days=days)
    peak_api = peak_usage_hours_for_api(db, days=days)
    model_api = model_usage_for_api(db, days=days)
    dept_api = usage_by_department_for_api(db, days=days)
    tool_api = tool_usage_for_api(db, days=days)
    trend_buckets = cost_trend_over_time(db, days=days)
    top_users_list = top_users_by_cost(db, limit=5, days=days)

    anomalies_list = cost_anomalies(db, days=days, threshold_pct=30.0)
    advanced = advanced_stats(db, days=days)
    metrics: Dict[str, Any] = {
        "total_events": kpis.get("total_events", 0),
        "active_users": kpis.get("active_users", 0),
        "estimated_cost_usd": kpis.get("estimated_cost_usd"),
        "days": days,
        "peak_hours": peak_api.get("buckets", []),
        "model_distribution": [
            {"label": l, "count": v}
            for l, v in zip(model_api.get("labels", []), model_api.get("values", []))
        ],
        "by_dept": [
            {"dimension_value": d["department"], "event_count": d["event_count"]}
            for d in dept_api
        ],
        "tool_distribution": [
            {"label": l, "count": v}
            for l, v in zip(tool_api.get("labels", []), tool_api.get("values", []))
        ],
        "trend": [
            {"date": b.date, "event_count": b.event_count}
            for b in trend_buckets
        ],
        "avg_session_duration": average_session_duration(db, days=days),
        "top_users": top_users_list,
        "cost_anomalies": anomalies_list,
        "usage_by_weekday": advanced.get("usage_by_weekday", []),
        "avg_session_duration_by_department": advanced.get("avg_session_duration_by_department", []),
        "cost_by_department": advanced.get("cost_by_department", []),
        "failure_rate_by_tool": advanced.get("failure_rate_by_tool", []),
        "most_volatile_day": advanced.get("most_volatile_day"),
        "avg_events_per_active_user": advanced.get("avg_events_per_active_user"),
    }
    bullets = insights_module.generate_insights(metrics)
    return NarrativeInsights(
        bullets=bullets,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )


def narrative_insights(db: Session, days: int = 30) -> NarrativeInsights:
    """Generate 5-8 plain-English bullet insights. Delegates to get_insights()."""
    return get_insights(db, days=days)


# ---- Serialization for API ----

def usage_by_role_for_api(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """API-friendly list of usage by role."""
    items = usage_by_role(db, days=days)
    return [
        {
            "role": u.dimension_value,
            "event_count": u.event_count,
            "total_duration_ms": u.total_duration_ms,
            "user_count": u.user_count,
        }
        for u in items
    ]


def usage_by_department_for_api(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """API-friendly list of usage by department."""
    items = usage_by_department(db, days=days)
    return [
        {
            "department": u.dimension_value,
            "event_count": u.event_count,
            "total_duration_ms": u.total_duration_ms,
            "user_count": u.user_count,
        }
        for u in items
    ]


def cost_trend_for_api(db: Session, days: int = 30) -> Dict[str, Any]:
    """API-friendly trend: labels and series for charts."""
    buckets = cost_trend_over_time(db, days=days)
    return {
        "labels": [b.date for b in buckets],
        "event_counts": [b.event_count for b in buckets],
        "total_duration_ms": [b.total_duration_ms for b in buckets],
        "buckets": [{"date": b.date, "event_count": b.event_count, "total_duration_ms": b.total_duration_ms} for b in buckets],
    }


def peak_usage_hours_for_api(db: Session, days: Optional[int] = 30) -> Dict[str, Any]:
    """API-friendly: labels (hours) and values for bar chart."""
    buckets = peak_usage_hours(db, days=days)
    return {
        "labels": [str(b.hour) for b in buckets],
        "values": [b.count for b in buckets],
        "buckets": [{"hour": b.hour, "count": b.count} for b in buckets],
    }


def tool_usage_for_api(db: Session, days: Optional[int] = 30) -> Dict[str, Any]:
    """API-friendly: labels and values for pie/bar chart."""
    buckets = tool_usage_distribution(db, days=days)
    return {
        "labels": [b.label for b in buckets],
        "values": [b.count for b in buckets],
        "total": sum(b.count for b in buckets),
    }


def model_usage_for_api(db: Session, days: Optional[int] = 30) -> Dict[str, Any]:
    """API-friendly: model distribution for pie chart."""
    buckets = model_usage_distribution(db, days=days)
    return {
        "labels": [b.label for b in buckets],
        "values": [b.count for b in buckets],
        "total": sum(b.count for b in buckets),
    }


def tool_success_rates_for_api(db: Session, days: Optional[int] = 30) -> List[Dict[str, Any]]:
    """API-friendly: table of success/failure by tool."""
    rates = tool_success_failure_rates(db, days=days)
    return [
        {
            "tool": r.tool,
            "success_count": r.success_count,
            "failure_count": r.failure_count,
            "success_rate_pct": r.success_rate_pct,
        }
        for r in rates
    ]
