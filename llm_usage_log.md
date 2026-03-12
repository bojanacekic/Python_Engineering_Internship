# LLM Usage Log

This document describes how AI tools were used during the development of the Claude Code Telemetry Analytics Platform. It is intended to provide transparency for evaluators and future maintainers.

---

## 1. AI Tools Used

- **ChatGPT** — Used for high-level design questions, algorithm ideas (e.g. rolling averages for anomaly detection), and quick sanity checks on Python/SQL patterns. Also used to draft section text for documentation and to explore FastAPI and SQLAlchemy usage.

- **Cursor AI** — Used inside the IDE for code generation, refactors, and file-level edits. Cursor was the primary tool for implementing features (ingestion, analytics, insights, dashboard styling), fixing bugs, and updating the README and this log. Prompts were given in natural language with concrete file names and requirements.

---

## 2. Tasks Assisted by AI

- **Architecture design** — Discussed pipeline (raw data → ingestion → SQLite → analytics → dashboard), separation between scripts and app services, and where to place insight generation and cost anomaly logic.

- **Data ingestion logic** — Implementation of JSONL/CSV parsing, deduplication by `event_id`, employee join rules, and session/daily aggregate rebuilds. AI suggested structure and edge cases; developer verified against sample data and tests.

- **Analytics implementation** — KPIs, trend and distribution queries, peak hours, tool/model usage, success rates, session duration, top users, and cost anomaly detection (daily cost vs rolling average). AI helped with SQLAlchemy patterns and typing; developer validated outputs and formulas.

- **Dashboard styling** — CSS variables, card layout, chart color palette (single primary + shades), grid and legend styling, and ensuring a consistent dark theme. AI proposed rules (e.g. line vs bar vs doughnut colors); developer reviewed and adjusted for consistency.

- **Documentation writing** — README structure, project overview, architecture diagram, tech stack table, run instructions, and this LLM usage log. AI drafted sections; developer edited for accuracy and tone.

---

## 3. Example Prompts

1. *"Add an automated insight generator to the analytics engine. Create a module app/services/insights.py that analyzes computed metrics and produces 5–8 narrative insights. Expose them through analytics.get_insights() and render in the dashboard under Key Insights."*

2. *"Add simple cost anomaly detection. In analytics.py compute the daily average cost. If a day exceeds the rolling average by more than 30%, mark it as a potential anomaly. Return anomalies as { date, cost, deviation_percent }. Display anomalies in the insights section."*

3. *"Improve the visual consistency of the dashboard. Use a single main chart color with lighter shades. Define a palette: primary, primaryLight, primaryLighter, neutral, danger. Line charts → primary, bar → primaryLight, pie/donut → [primary, primaryLight, primaryLighter]. Grid lines subtle, legends #94a3b8."*

4. *"Fix the dashboard chart rendering. Several charts are blank. Check backend metric variable names, Jinja template names, JSON serialization with tojson, and Chart.js dataset structure. If a dataset is empty, show 'No data available for this chart'."*

5. *"Rewrite README.md to be a professional internship project README. Include: Project Overview, Key Features, Architecture pipeline, Tech Stack, Project Structure, Running the project (generate → ingest → run server), Dashboard Overview, Analytics Capabilities, Future Improvements. Keep it concise and professional."*

6. *"Remove FastAPI API documentation. Disable /docs and /redoc in FastAPI initialization. Remove README references to API Docs and the API Docs link from the dashboard header."*

7. *"Standardize the dashboard color palette. Define primary, secondary, accent, danger, purple, cyan. Apply to all Chart.js charts: line → primary, bar → primary or secondary, pie/doughnut → palette only, max 5 colors. Update KPI cards with subtle accent colors per metric."*

8. *"Create llm_usage_log.md describing how AI tools were used during development. Sections: AI Tools Used, Tasks Assisted by AI, Example Prompts, Validation Process, Human Oversight, Reflection. Keep the tone honest and professional."*

---

## 4. Validation Process

Generated code was not used as-is. It was:

- **Reviewed** — Line-by-line read for logic, naming, and consistency with the rest of the codebase. Obvious mistakes (e.g. wrong variable names, off-by-one in rolling windows) were corrected.

- **Tested** — Existing tests (pytest for ingestion, analytics, and API) were run after changes. Manual checks were performed: generate data, ingest, open dashboard, and verify charts, KPIs, and insights with different time windows. Edge cases (e.g. empty data, single model) were checked where relevant.

- **Adjusted manually** — Prompts often produced *almost* correct behavior. The developer fixed serialization (e.g. ensuring analytics return native Python types for JSON), template/JS alignment (e.g. camelCase in `DASHBOARD_DATA`), and styling (e.g. card radius, shadow, spacing) to match project standards.

---

## 5. Human Oversight

The developer ensured correctness and data validity by:

- **Owning the data model and schema** — Tables, columns, and relationships were defined and reviewed by the developer; AI suggested queries and service structure but not schema changes without explicit request.

- **Verifying formulas** — Cost and token proxies (duration-based tokens, $/1k tokens, rolling average for anomalies) were checked against the intended business rules. Where AI proposed a formula, it was compared to existing logic (e.g. `dashboard_kpis`) for consistency.

- **Controlling scope** — Features were requested in small, testable steps (e.g. "add cost anomalies" then "display in insights") so each change could be validated before building on it.

- **Reviewing security and safety** — No secrets or credentials were put in prompts; generated code was checked for safe use of user/request data and for proper escaping in templates (e.g. `| safe` only where content is trusted).

---

## 6. Reflection

AI tools significantly accelerated development: they produced boilerplate (routes, Pydantic schemas, CSS variables), suggested SQLAlchemy patterns and Chart.js options, and drafted documentation quickly. Without that assistance, the same features would have taken longer to implement and document. At the same time, quality was maintained by treating AI output as a draft. Every change was reviewed and tested; mistakes and mismatches (e.g. chart data not reaching the frontend, or README inaccuracies) were caught and fixed by the developer. The result is a codebase that reflects both AI-assisted speed and human oversight for correctness, consistency, and maintainability.
