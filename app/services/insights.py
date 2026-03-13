"""
Automated insight generator for the analytics dashboard.

Analyzes computed metrics and produces 5–8 short narrative insights in plain English,
suitable for an executive dashboard. Used by analytics.get_insights().
"""
from __future__ import annotations

from typing import Any, Dict, List


def generate_insights(metrics: Dict[str, Any]) -> List[str]:
    """
    Produce 5–8 plain-English bullet insights from pre-computed metrics.

    Args:
        metrics: Dict with keys such as total_events, active_users, by_role, by_dept,
                 tool_distribution, model_distribution, peak_hours, trend, avg_session_duration,
                 estimated_cost_usd, success_rates, top_users.

    Returns:
        List of short insight strings (5–8 items).
    """
    bullets: List[str] = []

    total_events = metrics.get("total_events") or 0
    active_users = metrics.get("active_users") or 0
    days = metrics.get("days", 30)

    if total_events > 0:
        bullets.append(
            f"{total_events:,} events from {active_users} active users in the last {days} days."
        )

    # Peak usage hour
    peak_hours = metrics.get("peak_hours") or []
    if peak_hours:
        peak = max(peak_hours, key=lambda x: x.get("count", 0))
        hour = peak.get("hour", 0)
        count = peak.get("count", 0)
        bullets.append(f"Peak usage hour: {hour}:00 UTC ({count:,} events).")

    # Dominant model usage
    model_dist = metrics.get("model_distribution") or []
    if model_dist:
        top = model_dist[0] if model_dist else None
        if top and total_events > 0:
            pct = 100.0 * top.get("count", 0) / total_events
            bullets.append(
                f"Dominant model: \"{top.get('label', 'unknown')}\" ({pct:.0f}% of usage)."
            )

    # Highest token/usage department (proxy: event count or duration)
    by_dept = metrics.get("by_dept") or []
    if by_dept:
        top_dept = max(by_dept, key=lambda x: x.get("event_count", 0))
        name = top_dept.get("dimension_value", "Unknown")
        count = top_dept.get("event_count", 0)
        bullets.append(f"Highest-usage department: \"{name}\" ({count:,} events).")

    # Average tokens/session (we use session duration as proxy; tokens ≈ duration-based)
    avg_duration = metrics.get("avg_session_duration")
    if avg_duration is not None and avg_duration > 0:
        bullets.append(f"Average session duration: {avg_duration:.1f} seconds.")

    # Unusual spikes (latest day vs prior 7-day average)
    trend = metrics.get("trend") or []
    if len(trend) >= 8:
        last_day = trend[-1].get("event_count", 0)
        prev_7 = [trend[i].get("event_count", 0) for i in range(-8, -1)]
        avg_7 = sum(prev_7) / 7.0 if prev_7 else 0
        if avg_7 > 0 and last_day >= 2.0 * avg_7:
            bullets.append(
                f"Usage spike: latest day ({last_day:,} events) is at least 2× the prior 7-day average."
            )
    elif len(trend) >= 2:
        recent = trend[-1].get("event_count", 0)
        prev = trend[-2].get("event_count", 0)
        if prev > 0:
            chg = 100.0 * (recent - prev) / prev
            bullets.append(f"Latest day: {recent:,} events ({chg:+.0f}% vs previous day).")

    # Most active users (top 1–2 by event count or cost)
    top_users = metrics.get("top_users") or []
    if top_users:
        top = top_users[0]
        name = top.get("name") or top.get("user_id") or "Unknown"
        count = top.get("event_count", 0)
        bullets.append(f"Most active user: {name} ({count:,} events).")

    # Most used tool/feature
    tool_dist = metrics.get("tool_distribution") or []
    if tool_dist and total_events > 0:
        top_tool = tool_dist[0]
        label = top_tool.get("label", "unknown")
        count = top_tool.get("count", 0)
        pct = 100.0 * count / total_events
        bullets.append(f"Most used feature: \"{label}\" ({pct:.0f}% of events).")

    # Estimated cost
    cost = metrics.get("estimated_cost_usd")
    if cost is not None and cost > 0:
        bullets.append(f"Estimated period cost: ${cost:.2f}.")

    # Cost anomalies (days >30% above rolling average)
    anomalies = metrics.get("cost_anomalies") or []
    for a in anomalies[:3]:
        date_str = a.get("date", "?")
        cost_val = a.get("cost", 0)
        dev = a.get("deviation_percent", 0)
        bullets.append(
            f"Cost anomaly on {date_str}: ${cost_val:.2f} ({dev:+.0f}% above rolling average)."
        )

    # Advanced: busiest weekday
    usage_weekday = metrics.get("usage_by_weekday") or []
    if usage_weekday:
        busiest = max(usage_weekday, key=lambda x: x.get("count", 0))
        if busiest.get("count", 0) > 0:
            bullets.append(
                f"Busiest weekday: {busiest.get('weekday', '?')} ({busiest.get('count', 0):,} events)."
            )

    # Advanced: most volatile day (largest day-over-day change)
    vol = metrics.get("most_volatile_day")
    if vol and vol.get("date"):
        chg = vol.get("change_pct", 0)
        bullets.append(
            f"Largest day-over-day change: {vol['date']} ({chg:+.0f}% vs previous day)."
        )

    # Advanced: avg events per active user
    avg_events_user = metrics.get("avg_events_per_active_user")
    if avg_events_user is not None and active_users > 0:
        bullets.append(
            f"Average events per active user: {avg_events_user:.0f}."
        )

    # Advanced: top department by cost
    cost_by_dept = metrics.get("cost_by_department") or []
    if cost_by_dept and len(cost_by_dept) > 0:
        top = cost_by_dept[0]
        bullets.append(
            f"Highest cost department: \"{top.get('department', '?')}\" (${top.get('estimated_cost_usd', 0):.2f})."
        )

    return bullets[:12]
