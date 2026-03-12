# Claude Code Telemetry Analytics Platform

A clean, internship-quality analytics platform for Claude Code telemetry. Built with FastAPI, SQLAlchemy, SQLite, Pandas, and a simple HTML/CSS/JS dashboard with Chart.js.

## Requirements

- Python 3.9+
- No Streamlit, Dash, or heavy frontend frameworks—only Python and simple HTML/CSS/JS.

## Project Structure

```
.
├── main.py                 # Application entrypoint
├── generate_fake_data.py   # Generates telemetry_logs.jsonl and employees.csv
├── config/                 # Configuration
├── app/
│   ├── main.py             # FastAPI application
│   ├── database.py         # SQLAlchemy engine and session
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic (data loading, analytics)
│   ├── routes/             # API and page routes
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS and JS (Chart.js via CDN)
├── tests/                  # Pytest tests
└── data/                   # Optional: generated data (gitignored except .gitkeep)
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

3. **Generate sample data:**

   ```bash
   python generate_fake_data.py
   ```

   This creates `telemetry_logs.jsonl` and `employees.csv` in the project root (or in `data/` if you prefer—adjust paths in `config/settings.py`).

4. **Run the application:**

   ```bash
   python main.py
   ```

   The API and dashboard are available at:

   - **Dashboard:** http://127.0.0.1:8000/
   - **API docs:** http://127.0.0.1:8000/docs

5. **Load data into the database (first run):**

   - Open the dashboard; the app can auto-load from JSONL/CSV on startup if files exist, or call the load endpoint once (see API docs).

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
