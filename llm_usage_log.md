# LLM Usage Log — Claude Code Telemetry Analytics

**Project:** Claude Code Telemetry Analytics Platform  
**Submission:** Internship assignment  
**Document purpose:** Transparent record of AI tool use, validation, and reflection.

---

## 1. AI tools used

| Tool | Use in this project |
|------|----------------------|
| **Cursor** | Primary IDE with in-editor AI (completion, chat, refactors). Used for scaffolding, implementing features, fixing errors, and writing tests. |
| **ChatGPT** | Occasional use for clarifying concepts, API patterns, and reviewing short code snippets when Cursor was not in use. |

---

## 2. What each tool was used for

**Cursor**

- **Scaffolding:** Project layout, `requirements.txt`, `.gitignore`, config and database setup, FastAPI app factory and route registration.
- **Feature implementation:** Data generator script, ingestion pipeline (JSONL parsing, batched `logEvents`, nested `message` decoding), SQLAlchemy models (telemetry_events, employees, sessions_summary, daily_metrics), and analytics functions (KPIs, trends, distributions, success rates, narrative insights).
- **Dashboard:** Jinja2 dashboard template, Chart.js integration, CSS for KPI cards and tables, minimal JS for chart initialization.
- **API design:** Route structure, request/response shapes, Pydantic schemas for analytics and metrics.
- **Fixes and robustness:** Circular import resolution (database ↔ models), SQLite `:memory:` session handling in tests (StaticPool), Jinja2 template syntax, SQLAlchemy `case()` for success/failure counts.
- **Documentation:** README structure and content, this LLM usage log.

**ChatGPT**

- **Concept checks:** When to use `StaticPool` for SQLite in-memory in pytest; Pydantic-settings with `Path` vs `str` for file paths.
- **Snippet review:** Short examples for FastAPI dependency injection and for Chart.js options (responsive, legend color) to compare with project style.
- **Wording:** Alternative phrasings for README sections and for “assumptions and tradeoffs” so the submission read clearly.

---

## 3. Example prompts (8–12)

1. **“You are my senior Python architect. Build a clean internship-quality project in this folder. Context: Python 3.9, no Streamlit/Dash/React. Use FastAPI, SQLAlchemy, SQLite, Pandas, Jinja2, Chart.js via CDN. Dataset from generate_fake_data.py → telemetry_logs.jsonl and employees.csv. I want professional architecture, clean folder structure, strong README, clear analytics, and a simple polished dashboard.”**

2. **“Move generate_fake_data.py into scripts/generate_data.py. Generated files must go into data/raw/. Build an ingestion pipeline in app/services/ingestion.py that reads telemetry_logs.jsonl, parses batched logEvents, safely decodes nested JSON message fields, loads employees.csv, joins by email when possible, and stores normalized data in SQLite. Add sessions_summary and daily_metrics models. Create scripts/ingest_data.py runnable. Give a short summary of assumptions before writing code.”**

3. **“Implement analytics for the internship. I need: app/services/analytics.py with reusable functions; metrics for token consumption by role/practice, cost trends, peak hours, tool and model usage, success vs failure rates, average session duration, top users; a narrative insights layer (5–8 bullets); API-friendly outputs for charts and tables. Modular, typed, robust, not overengineered.”**

4. **“Build a polished but simple dashboard: FastAPI + Jinja2 + Chart.js. No Streamlit/React. Include KPI cards (total events, estimated cost, total tokens, active users), charts (daily cost trend, hourly usage, tool usage bar, model usage pie, role/practice consumption), tables (top users by cost, top tools by failures), insight summary. Add /api/metrics, good CSS, minimal clean JS.”**

5. **“Rewrite README.md for internship submission. Include: project overview, architecture, tech stack, folder structure, data flow (generator → ingestion → SQLite → analytics → dashboard), setup for Python 3.9, how to generate/ingest/run, API endpoints, key insights, assumptions and tradeoffs, future improvements. Professional, concise, internship-ready, not generic.”**

6. **“Fix: SQLAlchemy circular import — app.database imports app.models, and models import Base from app.database. How do I create all tables without moving Base?”**

7. **“pytest uses in-memory SQLite but the app’s get_db still hits the file DB. How do I override get_db in FastAPI TestClient so tests use the in-memory engine? And why do I get ‘no such table: telemetry_events’ when the fixture creates tables on that engine?”**

8. **“In Jinja2, I have summary.date_range.min and summary.date_range.max; sometimes they’re None. I want to show first 10 chars or ‘—’ if missing. I tried {{ summary.date_range.min|default('—')[:10] }} and get ‘expected token end of print statement, got [’.”**

9. **“Add a GET /api/metrics endpoint that returns total_events, estimated_cost_usd, total_tokens, active_users. We don’t have real token/cost in the schema — use duration_ms and event count as proxy and document it as estimated.”**

10. **“Create llm_usage_log.md for the submission. Include: AI tools (Cursor, ChatGPT), what each was used for, 8–12 example prompts, how AI-generated code was validated, which parts were reviewed manually, risks and mitigations, short reflection on AI-first development. Honest, professional, strong for internship evaluation.”**

---

## 4. How AI-generated code was validated

- **Tests:** Pytest suite for API (dashboard HTML, summary, events-by-type, load-data, invalid params) and for services (DataLoader JSONL/CSV, AnalyticsService summary and events-by-type). All tests run before considering a feature done; failures were fixed by adjusting logic or test expectations.
- **Running the app:** After major changes, the app was started locally; dashboard and key API routes (e.g. `/api/metrics`, `/api/analytics/insights`, `/api/analytics/cost-trend`) were called to confirm responses and that the dashboard rendered without errors.
- **Data path:** Generator and ingestion scripts were run in sequence (generate → ingest); row counts and DB content were spot-checked to ensure events and employees were present and sessions/daily_metrics looked plausible.
- **Linting:** IDE linting (and, where run, `read_lints`) was used to catch type and style issues in edited files.
- **Read-through:** All added or modified files were read in full at least once to ensure naming, structure, and behavior matched the intended design and project conventions.

---

## 5. Which parts were reviewed manually

- **Security and paths:** Config and ingestion paths (e.g. `data/raw/`, settings) were checked so that no sensitive paths or credentials were hardcoded and so paths work from project root.
- **SQL and performance:** Queries in analytics and ingestion (aggregations, joins, filters) were reviewed for correctness and for reasonable use of indexes (e.g. on timestamp, user_id, event_type). No N+1 patterns were introduced in list endpoints.
- **Error handling:** Ingestion logging and skip-on-error behavior for malformed JSONL/CSV were reviewed so that bad rows do not crash the pipeline and are logged clearly.
- **API contract:** Response shapes for new endpoints (e.g. `/api/metrics`, analytics responses) were checked against the README and dashboard expectations (e.g. `estimated_cost_usd`, `total_tokens`, chart payloads).
- **Dashboard data flow:** Template variable names and `DASHBOARD_DATA` keys were verified to match what the page route passes and what `dashboard.js` expects (e.g. `cost_trend`, `peak_hours`, `tool_usage`, `model_usage`, `usageByRole`, `usageByDepartment`).
- **README and log:** README setup, commands, and endpoint list were verified against the actual codebase. This LLM usage log was written and then reviewed for accuracy and tone.

---

## 6. Risks of AI generation and mitigations

| Risk | Mitigation |
|------|------------|
| **Incorrect or outdated APIs** | Checked FastAPI, SQLAlchemy, and Pydantic usage against current project and, when unsure, official docs or minimal runs. Test suite and manual runs catch signature and behavior mismatches. |
| **Overfitting to demo data** | Analytics and ingestion are written for generic schemas and optional fields (e.g. missing `message`, missing model). Edge cases (no events, no employees, no failures) are handled in code and in templates (e.g. “No data” / “No failures”). |
| **Copy-paste without understanding** | Every added file and non-trivial block was read and reasoned about; prompts asked for explanations (e.g. “summary of assumptions”) and for modular, typed code so structure stays understandable. |
| **Silent bugs or wrong formulas** | Cost/token proxies and success/failure logic were reviewed explicitly. Tests assert counts and response shapes; manual checks confirmed that numbers (e.g. KPIs, chart series) are consistent with the DB. |
| **Generic or brittle prompts** | Prompts were made project-specific (stack, file names, data flow). When the model suggested a different structure, it was accepted only if it matched the intended architecture and was validated as above. |
| **Overstated or vague documentation** | README and this log were written to describe what the project actually does and how it was validated, and were revised to remove vague or inflated claims. |

---

## 7. Reflection on AI-first development

Using Cursor and ChatGPT for this project made it possible to move quickly from an empty folder to a working pipeline, analytics layer, and dashboard without getting stuck on boilerplate or syntax. The main benefit was **speed and consistency**: project layout, FastAPI wiring, SQLAlchemy models, and Chart.js integration came together in a coherent style because the same context (stack, naming, data flow) was carried across prompts.

The main **cost** was the need to validate almost everything. Generated code often looked right but had subtle issues (circular imports, SQLite connection scope in tests, Jinja2 filters, or missing edge cases). Relying on tests and manual runs, plus a full read-through of changed code, was necessary to avoid shipping wrong behavior or misleading metrics.

**What I’d do again:** Use AI for scaffolding, repetitive patterns, and first drafts of documentation, and for exploring options (e.g. “how do I override get_db in tests?”). Keep prompts concrete and project-scoped.

**What I’d do differently:** Ask for smaller, incremental changes and run tests after each step instead of batching many features into one prompt. That would make it easier to attribute bugs to a specific change and to learn the codebase step by step.

Overall, AI-first development was effective for this internship-sized project because the scope was well defined and the validation steps (tests, run app, read code, review contracts) were applied consistently. For larger or less well-specified systems, I would treat AI output even more as a draft and increase the share of hand-written logic and design decisions.
