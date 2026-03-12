# File-by-file summary of changes (assignment alignment)

## 1. Architecture and code quality

| File | Changes |
|------|---------|
| **app/services/ingestion.py** | Expanded module docstring (rerunnable, validation, logging). Added `REQUIRED_CSV_FIELDS` and CSV column check with safe defaults. Wrapped employee load in try/except for DB and file I/O; commit/rollback on failure. Safe defaults for CSV fields (strip, truncate to column max). Logging on missing files, invalid CSV, commit failure, and final `run_ingestion` summary. |
| **app/models/telemetry.py** | Docstring and class comment updated; noted indexes for dedup and analytics. |
| **app/models/employee.py** | Module and class docstrings; noted indexes and join usage. |
| **app/models/sessions_summary.py** | Module and class docstrings; noted indexes and rebuild-on-ingest. |
| **app/models/daily_metrics.py** | Module and class docstrings; noted indexes and rebuild-on-ingest. |

## 2. Data pipeline

| File | Changes |
|------|---------|
| **app/services/ingestion.py** | Same as above: validation (required CSV columns), safe defaults (strip + length limits), error handling and logging, rerunnable semantics documented. No change to JSONL parsing or join logic. |

## 3. Storage design

| File | Changes |
|------|---------|
| **app/models/*.py** | Comments only; existing indexes and schema unchanged. |

## 4. Analytics and insights

| File | Changes |
|------|---------|
| **app/services/analytics.py** | In `narrative_insights`: (1) Unusual-spike bullet when latest day ≥ 2× prior 7-day average. (2) Stakeholder bullet with estimated cost from `dashboard_kpis`. Bullets still capped at 8. |

## 5. Dashboard

| File | Changes |
|------|---------|
| **app/routes/pages.py** | Added optional query param `days` (7, 30, or 90). `_coerce_days()` validates; default 30. All analytics calls use selected `days`. Template context extended with `days` and `allowed_days`. |
| **app/templates/dashboard.html** | Date-range filter: “Date range: Last 7 days | 30 days | 90 days” with links to `?days=7` etc. Active link styled with `.active`. |
| **app/static/css/style.css** | Styles for `.filter-label`, `.filter-days`, `.filter-link`, `.filter-link.active`. |

## 6. API endpoints

| File | Changes |
|------|---------|
| None | No changes. Existing metrics, trends, top users, tool stats, and insights endpoints kept. No /health. |

## 7. Testing

| File | Changes |
|------|---------|
| **tests/test_services.py** | Imports for `SessionSummary`, `DailyMetric`, `run_ingestion`, `analytics_module`. New tests: `test_ingestion_run` (temp JSONL + CSV, run_ingestion returns dict with expected keys); `test_dashboard_kpis_keys` (dashboard_kpis returns total_events, estimated_cost_usd, total_tokens, active_users); `test_narrative_insights_structure` (bullets list, generated_at, len ≤ 8). |
| **tests/test_api.py** | New test: `test_api_metrics` (GET /api/metrics returns 200 and expected KPI keys). |

## 8. README

| File | Changes |
|------|---------|
| **README.md** | Data flow section: dashboard now mentions date-range filter `?days=7|30|90`. Key insights section: narrative bullets extended to include “unusual spikes” and “estimated cost for stakeholders.” |

## 9. LLM usage log

| File | Changes |
|------|---------|
| **llm_usage_log.md** | None. Already had tools, prompts, validation, manual review, risks. |

## 10. Presentation support

| File | Changes |
|------|---------|
| **presentation_outline.md** | Subtitle updated: “5 slides (can be condensed to 3: combine Problem+Architecture, Analytics+Findings, Conclusion).” |

## New file

| File | Purpose |
|------|---------|
| **IMPLEMENTATION_PLAN.md** | Short implementation plan used to drive the changes above. |
| **CHANGES_SUMMARY.md** | This file-by-file summary. |

---

**Tests:** 14 passing (including 4 new: ingestion run, dashboard_kpis keys, narrative_insights structure, API metrics).  
**Linting:** No new issues reported on modified files.
