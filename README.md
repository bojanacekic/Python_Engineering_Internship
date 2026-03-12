# Claude Code Telemetry Analytics Platform

End-to-end analytics platform for Claude Code telemetry: generate sample data, ingest into SQLite, run analytics, and serve a stakeholder-facing dashboard. Built for Python 3.9 with a minimal, production-style stack (FastAPI, SQLAlchemy, Jinja2, Chart.js)—no Streamlit, Dash, or React. Suitable for engineering and product teams evaluating usage, cost, and reliability.

---

## 1. Project overview

The platform ingests telemetry events (session starts, completions, edits, errors, etc.) and employee metadata to produce:

- **Stored data:** Normalized events and employees in SQLite, plus session and daily aggregates.
- **Analytics:** Usage by role and department, cost/usage trends, peak hours, tool and model distribution, success/failure rates, session duration, top users and tools.
- **Dashboard:** KPI cards, trend and distribution charts, top-user and top-tool tables, and auto-generated narrative insights.
- **API:** REST endpoints for all metrics and a single-page HTML dashboard for viewing.

Target audience: engineering and product stakeholders who need usage, cost, and reliability insights from Claude Code usage.

---

## 2. Architecture overview

- **Entrypoint:** `main.py` runs the FastAPI app with uvicorn.
- **App:** `app/main.py` creates the FastAPI app, mounts static files, and registers page and API routes. `init_db()` ensures SQLite tables exist on startup.
- **Data layer:** SQLAlchemy models and sessions; config in `config/settings.py` (DB URL, paths to raw data).
- **Pipeline:** Standalone scripts under `scripts/` for generation and ingestion; services under `app/services/` for ingestion, analytics, and legacy loading.
- **Presentation:** Jinja2 templates for the dashboard; Chart.js (CDN) for charts; API returns JSON for programmatic access.

No background workers or message queues; ingestion is run-on-demand via script or (legacy) API.

---

## 3. Tech stack

| Layer        | Choice |
|-------------|--------|
| Runtime     | Python 3.9 |
| API         | FastAPI |
| Server      | Uvicorn |
| ORM / DB    | SQLAlchemy 2.x, SQLite |
| Validation  | Pydantic, pydantic-settings |
| Templates   | Jinja2 |
| Frontend    | HTML/CSS, vanilla JS, Chart.js (CDN) |
| Tests       | pytest, pytest-asyncio, httpx |

No Pandas in the critical path (analytics use SQLAlchemy and in-process aggregation). No React, Streamlit, or Dash.

---

## 4. Folder structure

```
.
├── main.py                    # Run app: uvicorn (host 0.0.0.0, port 8000)
├── generate_fake_data.py      # Wrapper → scripts.generate_data (writes data/raw/)
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py            # DB URL, telemetry_logs path, employees path
├── scripts/
│   ├── generate_data.py       # Writes telemetry_logs.jsonl + employees.csv → data/raw/
│   └── ingest_data.py         # Full pipeline: JSONL + CSV → SQLite, sessions, daily_metrics
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI factory, init_db, routes
│   ├── database.py            # Engine, SessionLocal, Base, get_db, init_db
│   ├── models/                # TelemetryEvent, Employee, SessionSummary, DailyMetric
│   ├── schemas/               # Pydantic request/response models
│   ├── services/
│   │   ├── data_loader.py     # Legacy: flat JSONL/CSV → DB
│   │   ├── ingestion.py       # Pipeline: batched/nested JSONL, employees, sessions, daily_metrics
│   │   ├── analytics.py       # KPIs, trends, distributions, insights (typed, modular)
│   │   └── analytics_service.py # Legacy summary/events-by-type/over-time
│   ├── routes/                # pages (dashboard), analytics API, metrics API
│   ├── templates/             # base.html, dashboard.html
│   └── static/                # css/style.css, js/dashboard.js
├── tests/                     # conftest (in-memory DB, client), test_api, test_services
└── data/raw/                  # telemetry_logs.jsonl, employees.csv (gitignored)
```

---

## 5. Data flow

1. **Generate** (`scripts/generate_data.py` or `python generate_fake_data.py`)  
   Produces `data/raw/telemetry_logs.jsonl` (flat events: event_id, timestamp, user_id, event_type, duration_ms, error_code) and `data/raw/employees.csv` (employee_id, name, email, department, role).

2. **Ingest** (`python -m scripts.ingest_data`)  
   - Reads JSONL (supports flat lines and batched `logEvents`; decodes nested `message` JSON when present).  
   - Normalizes and deduplicates by event_id; loads employees from CSV.  
   - Joins events to employees by email (if present) or user_id → employee_id.  
   - Writes to **SQLite**: `telemetry_events`, `employees`, then rebuilds `sessions_summary` (session boundaries by user + 30‑min gap / session_start) and `daily_metrics` (total_events, total_sessions, unique_users per day).  
   - Logging and skip-on-error for malformed rows.

3. **SQLite**  
   Single file (default `telemetry.db`). Tables: `telemetry_events`, `employees`, `sessions_summary`, `daily_metrics`.

4. **Analytics** (`app/services/analytics.py`)  
   Reusable, typed functions over the DB: KPIs (events, estimated cost, token proxy, active users), usage by role/department, cost/usage trend over time, peak hours, tool/model distribution, tool success/failure rates, average session duration, top users by cost, top tools by failures, and narrative insights (5–8 bullets).

5. **Dashboard**  
   Server-rendered Jinja2 page: KPIs, charts (daily trend, hourly, tool bar, model doughnut, role/practice bar), tables (top users by cost, top tools by failures), and insight summary. Date-range filter: `?days=7`, `?days=30`, or `?days=90`. Data injected as `DASHBOARD_DATA`; Chart.js renders client-side.

---

## 6. Setup (Python 3.9)

```bash
# Clone or unpack the project, then:
python3.9 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set `DATABASE_URL`, `TELEMETRY_LOGS_PATH`, `EMPLOYEES_CSV_PATH` if you need to override defaults (see `config/settings.py`).

---

## 7. Generate data

Writes into `data/raw/` (directory created if missing).

```bash
python generate_fake_data.py
# or
python -m scripts.generate_data
```

Default: 50 employees, 2000 events over the last 30 days. Outputs `data/raw/telemetry_logs.jsonl` and `data/raw/employees.csv`.

---

## 8. Ingest data

Loads from `data/raw/` into SQLite and rebuilds session and daily aggregates.

```bash
python -m scripts.ingest_data
```

Uses paths from config (default `data/raw/telemetry_logs.jsonl` and `data/raw/employees.csv`). Idempotent for events and employees (skips duplicates by event_id / employee_id). Sessions and daily_metrics are replaced on each run.

---

## 9. Run the app

```bash
python main.py
```

- **Dashboard:** http://127.0.0.1:8000/  
- **API docs:** http://127.0.0.1:8000/docs  

The dashboard “Refresh data from files” button runs the legacy loader (flat JSONL/CSV) against the same paths; for the full pipeline (batched/nested JSONL, sessions, daily_metrics), run `python -m scripts.ingest_data` and refresh the page.

---

## 10. API endpoints

| Method + Path | Description |
|---------------|-------------|
| **Metrics (KPIs)** | |
| `GET /api/metrics?days=30` | `total_events`, `estimated_cost_usd`, `total_tokens`, `active_users` |
| **Analytics** (prefix `/api/analytics`, optional `?days=30`) | |
| `GET /summary` | Total events, employees, unique users, event types, date range |
| `GET /events-by-type` | Counts per event_type |
| `GET /events-over-time` | Daily event counts |
| `GET /events-by-department` | Counts per department |
| `GET /top-users?limit=10` | Top users by event count |
| `GET /usage-by-role` | Event count + duration by role |
| `GET /usage-by-department` | Event count + duration by department |
| `GET /cost-trend` | Daily trend (labels, event_counts, total_duration_ms) |
| `GET /peak-usage-hours` | Count by hour (0–23) |
| `GET /tool-usage` | Event-type distribution (labels, values, total) |
| `GET /model-usage` | Model distribution (from payload or default) |
| `GET /tool-success-rates` | Per-tool success/failure and success_rate_pct |
| `GET /average-session-duration` | Mean session duration (seconds) |
| `GET /top-users-activity?limit=10` | Top users with name/department |
| `GET /top-departments?limit=10` | Top departments by usage |
| `GET /insights` | Narrative bullets + generated_at |
| `POST /load-data` | Legacy: load flat JSONL + CSV into DB |

---

## 11. Key insights supported by the analytics

- **Volume and reach:** Total events, active users, and date range (summary + metrics).
- **Cost and tokens:** Estimated cost (USD) and total tokens from duration/event proxies; daily trend for “cost” over time; top users by estimated cost.
- **When usage happens:** Peak usage by hour (UTC); daily trend for usage over time.
- **What is used:** Tool (event type) distribution; model distribution (when present in payload).
- **Who uses it:** Usage by role (Intern, Junior, Mid, Senior, Lead) and by department (practice); top users and top departments.
- **Reliability:** Per-tool success vs failure and success rate; top tools by failure count.
- **Sessions:** Average session duration; session and daily aggregates in DB.
- **Narrative:** Auto-generated 5–8 bullet insights (totals, top role/department/tool, lowest success rate, avg session duration, peak hour, latest-day change, unusual spikes when applicable, estimated cost for stakeholders).

---

## 12. Assumptions and tradeoffs

- **Cost and tokens:** No raw token or cost fields in the schema. Analytics use duration_ms and event counts as proxies (e.g. tokens from duration, fixed rate per 1k tokens for estimated cost). Dashboard and API expose these as “estimated” so stakeholders understand they are approximations until real billing/token data is available.
- **Input format:** Ingestion supports flat JSONL, batched `logEvents`, and optional nested `message` JSON. Generator produces only flat JSONL; the pipeline is built for future or external batched/nested sources.
- **Identity:** Employee join is by email (if present in event) or user_id ↔ employee_id. Events without a match keep user_id only; optional employee_id FK when matched.
- **Sessions:** Session boundary = session_start event or gap > 30 minutes; no explicit session_id in raw events.
- **Single process:** No Celery or job queue; ingestion is script or one-off API. Suitable for internship-scale data and demos; for large volumes, a queue and worker would be a natural extension.
- **Frontend:** Server-rendered HTML + Chart.js. No SPA or React to keep scope and stack minimal while still delivering a professional dashboard.

---

## 13. Future improvements

- **Real cost and tokens:** Add token/cost fields to telemetry (or from a separate billing feed) and replace proxy logic in analytics and dashboard.
- **Auth and multi-tenant:** Optional login and scoping by team/org so dashboards and APIs only show allowed data.
- **Caching:** Cache heavy analytics (e.g. cost trend, insights) with TTL or invalidation on ingest.
- **Async ingestion:** Run ingestion in a background task or worker and expose status (e.g. “ingestion in progress” or last run time) on the dashboard or API.
- **Exports:** CSV/Excel export for top users, tool success rates, and trend data.
- **Alerts:** Thresholds on cost, failure rate, or session duration with optional notifications.
- **More dimensions:** Project or repo from payload or separate mapping table to support “top projects” and per-project analytics.

---

## Testing

From the project root (with virtualenv activated):

```bash
# Ensure project root is on PYTHONPATH when needed
set PYTHONPATH=.   # Windows
# export PYTHONPATH=.  # macOS/Linux

pytest tests/ -v
```

Tests use an in-memory SQLite DB and override the app’s DB dependency so no file DB is required.

---

*Claude Code Telemetry Analytics — Python 3.9 · FastAPI · SQLAlchemy · Jinja2 · Chart.js*
