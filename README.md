# Claude Code Telemetry Analytics Platform

A clean, internship-quality analytics platform for Claude Code telemetry. Built with FastAPI, SQLAlchemy, SQLite, Pandas, and a simple HTML/CSS/JS dashboard with Chart.js.

## Requirements

- Python 3.9+
- No Streamlit, Dash, or heavy frontend frameworks—only Python and simple HTML/CSS/JS.

## Project Structure

```
.
├── main.py                 # Application entrypoint
├── generate_fake_data.py   # Backward-compat wrapper → scripts/generate_data (writes data/raw/)
├── config/                 # Configuration
├── scripts/
│   ├── generate_data.py    # Generate telemetry_logs.jsonl + employees.csv into data/raw/
│   └── ingest_data.py      # Run full ingestion pipeline (JSONL + CSV → SQLite, sessions, daily_metrics)
├── app/
│   ├── main.py             # FastAPI application
│   ├── database.py         # SQLAlchemy engine and session
│   ├── models/             # SQLAlchemy models (telemetry_events, employees, sessions_summary, daily_metrics)
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Data loading, ingestion pipeline, analytics
│   ├── routes/             # API and page routes
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS and JS (Chart.js via CDN)
├── tests/                  # Pytest tests
└── data/raw/               # Generated and ingested data (gitignored)
```

## Quick Start

1. **Create a virtual environment (recommended):**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Generate sample data** (writes to `data/raw/`):

   ```bash
   python generate_fake_data.py
   # or: python -m scripts.generate_data
   ```

   This creates `data/raw/telemetry_logs.jsonl` and `data/raw/employees.csv`.

4. **Ingest into the database:**

   ```bash
   python -m scripts.ingest_data
   ```

   This loads employees and telemetry (supports flat JSONL, batched `logEvents`, and nested JSON `message` fields), joins by email when possible, and rebuilds `sessions_summary` and `daily_metrics`.

5. **Run the application:**

   ```bash
   python main.py
   ```

   - **Dashboard:** http://127.0.0.1:8000/
   - **API docs:** http://127.0.0.1:8000/docs

   You can also use the dashboard "Load / refresh data" button to run the legacy loader (flat JSONL/CSV); for full pipeline use `python -m scripts.ingest_data`.

## Features

- **Data pipeline:** Ingest `telemetry_logs.jsonl` and `employees.csv` into SQLite via SQLAlchemy.
- **Analytics:** Aggregations by event type, user, time period, and basic KPIs (sessions, completions, errors).
- **Dashboard:** Simple, polished single-page dashboard with Chart.js charts (e.g. events over time, by type, by user/department).
- **API:** REST endpoints for analytics and health checks; no heavy frontend frameworks.
- **Quality:** Modular architecture, validation, error handling, and basic tests.

## Configuration

Edit `config/settings.py` to change:

- Database path (default: SQLite file in project root).
- Paths to `telemetry_logs.jsonl` and `employees.csv`.

## Testing

```bash
pytest tests/ -v
```

## License

Internship project—use as needed.
