# Claude Code Telemetry Analytics Platform

A professional analytics platform for **Claude Code telemetry data**, built as an internship-style project. It ingests event telemetry and employee data, stores it in SQLite, and serves an interactive dashboard with usage metrics, charts, and automated insights.

---

## Project Overview

This project is an **analytics platform for Claude Code telemetry data**. It processes raw telemetry events (session starts, completions, edits, errors, etc.) and employee metadata to deliver:

- Normalized storage and session/daily aggregates
- Usage and cost metrics with optional cost anomaly detection
- An interactive, stakeholder-facing dashboard with KPIs, charts, and narrative insights

The platform is designed for engineering and product teams who need visibility into usage patterns, cost estimates, and reliability from Claude Code usage.

---

## Key Features

- **Telemetry ingestion** — Ingest JSONL telemetry logs and CSV employee data; supports flat and batched formats with validation and deduplication
- **Analytics engine** — Typed, modular analytics for KPIs, trends, distributions, success rates, and session metrics
- **Usage metrics** — Total events, active users, token proxies, estimated cost, usage by role and department
- **Automated insights** — 5–10 plain-English bullet insights (peak usage, dominant model, top department, cost anomalies, etc.)
- **Interactive dashboard** — Server-rendered dashboard with KPI cards, time-window filter, charts, tables, and Key Insights section

---

## Architecture

End-to-end pipeline:

```
Raw telemetry data (JSONL + CSV)
    → Data ingestion (scripts + app/services)
    → SQLite storage (events, employees, sessions, daily_metrics)
    → Analytics engine (KPIs, trends, distributions, insights)
    → Dashboard visualization (Jinja2 + Chart.js)
```

- **Entrypoint:** `main.py` runs the FastAPI app with Uvicorn.
- **App:** `app/main.py` creates the app, mounts static files, and registers page and API routes.
- **Data layer:** SQLAlchemy models and sessions; config in `config/settings.py`.
- **Pipeline:** Scripts under `scripts/` for generation and ingestion; services under `app/services/` for ingestion, analytics, and insights.
- **Presentation:** Jinja2 templates and Chart.js for the dashboard; REST API for programmatic access.

---

## Tech Stack

| Layer     | Technology   |
|----------|--------------|
| Runtime  | Python 3.9   |
| API      | FastAPI      |
| Data     | Pandas, SQLAlchemy, SQLite |
| Templates| Jinja2       |
| Frontend | HTML/CSS, vanilla JS, Chart.js |
| Tests    | pytest, pytest-asyncio, httpx |

---

## Project Structure

```
.
├── main.py                 # Application entrypoint (Uvicorn)
├── generate_fake_data.py    # Wrapper to generate sample data
├── requirements.txt
├── config/
│   └── settings.py         # DB URL, paths to telemetry and employees
├── scripts/
│   ├── generate_data.py    # Writes telemetry_logs.jsonl + employees.csv
│   └── ingest_data.py      # Full pipeline: JSONL + CSV → SQLite + aggregates
├── app/
│   ├── main.py             # FastAPI factory, static files, routes
│   ├── database.py         # Engine, session, init_db
│   ├── models/             # TelemetryEvent, Employee, SessionSummary, DailyMetric
│   ├── schemas/            # Pydantic request/response models
│   ├── services/
│   │   ├── ingestion.py    # Batched/nested JSONL + CSV → DB
│   │   ├── analytics.py    # KPIs, trends, distributions, cost anomalies
│   │   └── insights.py     # Automated narrative insight generator
│   ├── routes/             # Dashboard and analytics API
│   ├── templates/          # base.html, dashboard.html
│   └── static/             # CSS and dashboard JavaScript (Chart.js)
├── tests/                  # pytest tests (API, services)
└── data/raw/               # Generated telemetry and CSV (gitignored)
```

---

## Running the Project

### 1. Setup

```bash
python3.9 -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Generate data

Produces sample telemetry and employee data in `data/raw/`:

```bash
python generate_fake_data.py
# or: python -m scripts.generate_data
```

### 3. Ingest data

Loads raw data into SQLite and builds session/daily aggregates:

```bash
python -m scripts.ingest_data
```

### 4. Run the server

```bash
python main.py
```

Open the **dashboard** at **http://127.0.0.1:8000/**.

Use the time-window filter (e.g. Last 7 / 30 / 90 days) to scope metrics. For a full refresh, run `python -m scripts.ingest_data` again and reload the page.

---

## Dashboard Overview

- **KPI cards** — Total events, estimated cost (USD), total tokens (proxy), and active users
- **Charts** — Daily usage trend (line), peak usage by hour (bar), feature/tool usage (bar), model distribution (doughnut), usage by role and department (bar)
- **Tables** — Top users by estimated cost; tools with most failures
- **Key insights** — Automated bullet insights (volume, peak hour, dominant model, top department, session duration, usage spikes, cost anomalies, most active user, estimated cost)

---

## Analytics Capabilities

- **Token usage trends** — Daily event counts and duration-based token proxy; estimated cost over time
- **Model usage distribution** — From telemetry payload or default bucket
- **Hourly activity** — Peak usage by hour (UTC) for bar chart
- **Top users** — By event count and estimated cost (with name/department when linked)
- **Department usage** — Event count and duration by department; highest-usage department in insights
- **Cost estimation** — Duration- and event-based token proxy with $/1k-token rate; cost anomaly detection (days >30% above 7-day rolling average)

Additional metrics: usage by role, tool/feature distribution, tool success/failure rates, average session duration, top tools by failures.

---

## Future Improvements

- **Real-time streaming analytics** — Ingest and aggregate telemetry via a message queue or streaming pipeline
- **ML-based anomaly detection** — Replace or augment rule-based cost anomalies with learned baselines
- **Alerting system** — Thresholds on cost, failure rate, or usage with email/Slack notifications
- **Exports** — CSV/Excel export for top users, trends, and insights
- **Auth and multi-tenant** — Login and scoping by team or organization

---

## Testing

From the project root with the virtualenv activated:

```bash
set PYTHONPATH=.   # Windows
# export PYTHONPATH=.   # macOS/Linux
pytest tests/ -v
```

Tests use an in-memory SQLite database; no file DB is required.

---

*Claude Code Telemetry Analytics — Python 3.9 · FastAPI · SQLAlchemy · Jinja2 · Chart.js*
