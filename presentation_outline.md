# Presentation Outline — Claude Code Telemetry Analytics

**Format:** 5 slides | **Audience:** Internship evaluation / stakeholders

---

## Slide 1: Problem and objective

**Title:** Problem and objective

**Bullets:**
- **Problem:** No single place to see how Claude Code is used—usage, cost, reliability, and who drives adoption.
- **Goal:** Build an end-to-end analytics platform: ingest telemetry and employee data, store it, analyze it, and surface it for stakeholders.
- **Scope:** Python 3.9, no heavy frontends (no Streamlit/React); FastAPI + SQLite + a simple dashboard.
- **Deliverables:** Data generator, ingestion pipeline, SQLite storage, analytics layer, REST API, and a stakeholder-facing dashboard with KPIs, charts, and insights.

**Speaker notes:**  
Open with the gap: teams have telemetry events but no unified view of usage, cost, or reliability. The objective was to build a full pipeline from raw data to insights in one place. Keep the stack constraints brief—they show you can work within requirements. Emphasize “end-to-end” and “stakeholder-facing” so the business value is clear.

---

## Slide 2: Architecture and pipeline

**Title:** Architecture and pipeline

**Bullets:**
- **Generate:** Script produces `telemetry_logs.jsonl` and `employees.csv` in `data/raw/` (events + employee dimension).
- **Ingest:** Pipeline reads JSONL (flat or batched), decodes nested JSON when present, joins events to employees by email or user_id, writes to SQLite, and rebuilds sessions and daily metrics.
- **Store:** Single SQLite DB with `telemetry_events`, `employees`, `sessions_summary`, and `daily_metrics`.
- **Serve:** FastAPI app exposes REST endpoints and a Jinja2 dashboard; Chart.js renders charts client-side from server-injected data.
- **Flow:** Generator → ingest script → SQLite → analytics service → API and dashboard.

**Speaker notes:**  
Walk the flow left to right. Stress that ingestion is flexible (flat and batched JSONL, optional nested `message`) so it can handle different upstream formats. Mention “sessions” and “daily metrics” as the first level of aggregation before analytics. One sentence on why SQLite: simple, file-based, no extra infrastructure for an internship-scale project.

---

## Slide 3: Data model and analytics

**Title:** Data model and analytics

**Bullets:**
- **Core tables:** `telemetry_events` (event_id, timestamp, user_id, event_type, duration_ms, error_code, optional employee_id); `employees` (id, employee_id, name, email, department, role).
- **Aggregates:** `sessions_summary` (user, start/end, event_count, duration_seconds); `daily_metrics` (date, metric_name, value) for events, sessions, and unique users per day.
- **Analytics:** Reusable, typed functions: KPIs (events, estimated cost, token proxy, active users), usage by role and department, cost/usage trend, peak hours, tool and model distribution, tool success/failure rates, average session duration, top users by cost, top tools by failures.
- **Insights:** Auto-generated 5–8 narrative bullets (totals, top role/department/tool, lowest success rate, peak hour, session duration, day-over-day change).

**Speaker notes:**  
Keep the data model to “what we store and why.” For analytics, say “one module, many functions” so it’s clear the design is modular. Call out that cost and tokens are *estimated* from duration/events until real billing data exists. The narrative insights are the bridge from raw metrics to a story—mention that they’re generated from the same metrics the dashboard uses.

---

## Slide 4: Key findings and story from the data

**Title:** Key findings and story from the data

**Bullets:**
- **Volume and reach:** Total events and active users over the window; date range shows coverage (e.g. last 30 days).
- **Where usage goes:** Usage by role (e.g. Intern vs Senior) and by department (e.g. Engineering, QA) shows which groups adopt the tool most.
- **When it’s used:** Peak usage by hour (UTC) and daily trend highlight busy periods and growth or seasonality.
- **What’s used and how well:** Tool (event type) distribution shows dominant actions; model distribution (when present) shows model mix; success/failure rates and “top tools by failures” surface reliability issues.
- **Story in one line:** The dashboard and narrative insights turn these metrics into a short, readable story (e.g. “X events from Y users; peak at Z; most used tool is W; lowest success rate on T”).

**Speaker notes:**  
This slide answers “so what?” Use the sample data if you have it (e.g. “In our sample run, we saw N events, peak at 2 PM UTC, completion_request as top tool”). If you’re presenting without live data, describe the *kind* of story the platform enables: “Stakeholders can see who uses the product, when, and where failures concentrate.” One sentence on “key finding” as a takeaway (e.g. “The main finding is that we can now attribute usage and cost to role and department and flag tools with high failure rates.”).

---

## Slide 5: Future improvements and conclusion

**Title:** Future improvements and conclusion

**Bullets:**
- **Real cost and tokens:** Ingest actual token and cost fields (or billing feed) and replace current proxies in analytics and dashboard.
- **Scale and operations:** Async or background ingestion for large loads; optional caching for heavy analytics; auth and scoping for multi-tenant or team-level views.
- **Product and UX:** CSV/Excel export for top users and trends; alerts on cost or failure-rate thresholds; project or repo dimension for “top projects” and per-project analytics.
- **Conclusion:** Delivered an end-to-end pipeline from raw telemetry to a stakeholder dashboard, with clear architecture, modular analytics, and a path to production-style improvements.

**Speaker notes:**  
Group improvements into “data,” “scale/ops,” and “product.” Keep conclusion to two sentences: what was delivered (end-to-end pipeline, dashboard, insights) and what it enables next (real cost data, scale, alerts, exports). End with a clear closing line (e.g. “Thank you—happy to take questions.”).

---

*Use this outline as the backbone; adjust bullets and speaker notes to match your actual demo or emphasis.*
