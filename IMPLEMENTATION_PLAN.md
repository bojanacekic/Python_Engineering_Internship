# Implementation Plan — Assignment Alignment

## Current state (brief)
- **Structure:** Clean separation (config, app/models, services, routes, templates, static, scripts, tests). API, services, DB, schemas, templates, scripts already separated.
- **Pipeline:** Ingestion supports flat/batched JSONL, nested `message`, CSV employees; normalizes and joins; sessions_summary + daily_metrics. Data loader (legacy) also present.
- **Storage:** SQLite + SQLAlchemy; telemetry_events, employees, sessions_summary, daily_metrics with indexes.
- **Analytics:** Full set (KPIs, role/department usage, cost trend, peak hours, tool/model distribution, success/failure, session duration, top users/tools, narrative insights 5–8 bullets).
- **Dashboard:** KPIs, 5 charts, 2 tables, insights; no filter controls yet.
- **API:** /api/metrics, /api/analytics/* (summary, trends, top users, tool stats, insights). No /health.
- **Tests:** 10 tests (dashboard, summary, events-by-type, load-data, data_loader, analytics_service). No ingestion or analytics-module or /api/metrics tests.
- **Docs:** README comprehensive; llm_usage_log.md and presentation_outline.md exist.

## Planned changes

1. **Architecture & code quality**
   - Add type hints and docstrings where missing in key modules (ingestion, analytics, routes).
   - Add structured logging and try/except in ingestion for file I/O and DB commits; log skipped/error counts.
   - Remove any dead code (unused imports/vars); ensure naming consistent (session_summary not session_summaries in code; README can use “session summaries” in prose).

2. **Data pipeline**
   - Keep existing behavior; add explicit input validation (e.g. CSV required columns) and safe defaults in normalization.
   - Document rerunnable semantics in ingestion docstring; ensure malformed-row handling is clear in logs.

3. **Storage**
   - Add short comments in model files on index usage for retrieval. No schema changes.

4. **Analytics & insights**
   - Extend narrative_insights: add optional “unusual spike” (e.g. day with events >2× recent average) and one stakeholder-oriented line (e.g. cost or reliability takeaway). Keep 5–8 bullets total.

5. **Dashboard**
   - Add date-range filter: query param `days` (e.g. 7, 30, 90); pass from route to template; add “Last 7 / 30 / 90 days” links or dropdown in UI. No React; minimal JS if needed.

6. **API**
   - No changes; already complete. No /health.

7. **Testing**
   - Add: test run_ingestion returns expected keys and doesn’t crash; test dashboard_kpis returns expected keys; test narrative_insights returns bullets and generated_at; test GET /api/metrics returns 200 and expected keys.

8. **README**
   - Verify and lightly edit for internship-submission checklist: overview, architecture, data flow, setup, generate, ingest, run, structure, API, assumptions, future improvements.

9. **llm_usage_log.md**
   - Ensure sections: tools used, example prompts, validation approach, manual review, risks and mitigations. Add or tighten any missing part.

10. **presentation_outline.md**
   - Keep 5 slides; add one-line note that deck can be condensed to 3 (e.g. combine problem+architecture, analytics+findings, conclusion).

## Out of scope
- No Streamlit, Dash, React, Docker.
- No new dependencies beyond current (Python 3.9).
- No placeholder code; all changes will be working.
