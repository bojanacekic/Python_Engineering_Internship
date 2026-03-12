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


# ---- Narrative insights ----

def narrative_insights(db: Session, days: int = 30) -> NarrativeInsights:
    """
    Generate 5-8 plain-English bullet insights from current data.
    Business- and developer-friendly summaries.
    """
    bullets: List[str] = []
    cutoff = _cutoff_date(db, days)

    total_events = db.query(func.count(TelemetryEvent.id))
    if cutoff:
        total_events = total_events.filter(TelemetryEvent.timestamp >= cutoff)
    total_events = total_events.scalar() or 0

    unique_users = db.query(func.count(func.distinct(TelemetryEvent.user_id)))
    if cutoff:
        unique_users = unique_users.filter(TelemetryEvent.timestamp >= cutoff)
    unique_users = unique_users.scalar() or 0

    if total_events > 0:
        bullets.append(
            f"Total of {total_events:,} events from {unique_users} active user(s) in the last {days} days."
        )

    by_role = usage_by_role(db, days=days)
    if by_role:
        top_role = max(by_role, key=lambda x: x.event_count)
        bullets.append(
            f"'{top_role.dimension_value}' has the highest usage with {top_role.event_count:,} events "
            f"({top_role.user_count} user(s))."
        )

    by_dept = usage_by_department(db, days=days)
    if by_dept:
        top_dept = max(by_dept, key=lambda x: x.event_count)
        bullets.append(
            f"'{top_dept.dimension_value}' is the most active department with {top_dept.event_count:,} events."
        )

    tools = tool_usage_distribution(db, days=days)
    if tools:
        top_tool = tools[0]
        pct = (100.0 * top_tool.count / total_events) if total_events else 0
        bullets.append(
            f"Most used tool is '{top_tool.label}' ({top_tool.count:,} events, {pct:.0f}% of total)."
        )

    rates = tool_success_failure_rates(db, days=days)
    if rates:
        lowest = min(rates, key=lambda x: x.success_rate_pct)
        if lowest.failure_count > 0:
            bullets.append(
                f"'{lowest.tool}' has the lowest success rate at {lowest.success_rate_pct:.0f}% "
                f"({lowest.failure_count} failures)."
            )

    avg_dur = average_session_duration(db, days=days)
    if avg_dur is not None and avg_dur > 0:
        bullets.append(f"Average session duration is {avg_dur:.1f} seconds.")

    hours = peak_usage_hours(db, days=days)
    if hours:
        peak = max(hours, key=lambda x: x.count)
        bullets.append(f"Peak usage hour is {peak.hour}:00 UTC with {peak.count} events.")

    trend = cost_trend_over_time(db, days=days)
    if len(trend) >= 2:
        recent = trend[-1].event_count
        prev = trend[-2].event_count
        if prev > 0:
            chg = 100.0 * (recent - prev) / prev
            bullets.append(
                f"Latest day had {recent:,} events ({chg:+.0f}% vs previous day)."
            )
    # Unusual spike: last day > 2x average of previous 7 days
    if len(trend) >= 8:
        last_day = trend[-1].event_count
        prev_7_avg = sum(t.event_count for t in trend[-8:-1]) / 7.0
        if prev_7_avg > 0 and last_day >= 2.0 * prev_7_avg:
            bullets.append(
                f"Unusual spike: latest day ({last_day:,} events) is at least 2x the prior 7-day average."
            )
    # Stakeholder-oriented: estimated cost
    kpis = dashboard_kpis(db, days=days)
    if kpis.get("estimated_cost_usd") is not None and kpis["estimated_cost_usd"] > 0:
        bullets.append(
            f"Estimated cost over the period (usage proxy): ${kpis['estimated_cost_usd']:.2f}."
        )

    # Cap at 8
    bullets = bullets[:8]
    return NarrativeInsights(
        bullets=bullets,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )


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
