"""
Run the ingestion pipeline: load data/raw/telemetry_logs.jsonl and data/raw/employees.csv
into SQLite, then rebuild sessions_summary and daily_metrics.

Run from project root: python -m scripts.ingest_data
Optional env: TELEMETRY_LOGS_PATH, EMPLOYEES_CSV_PATH, DATABASE_URL
"""
import logging
import sys
from pathlib import Path

# Project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, init_db
from app.services.ingestion import run_ingestion
from config.settings import settings


def main() -> int:
    """Run full ingestion; return 0 on success, 1 on failure."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("ingest_data")
    logger.info("Starting ingestion from data/raw/")
    init_db()
    db = SessionLocal()
    try:
        result = run_ingestion(
            db,
            telemetry_path=settings.telemetry_logs_path,
            employees_path=settings.employees_csv_path,
            rebuild_sessions=True,
            rebuild_daily_metrics=True,
        )
        logger.info(
            "Ingestion complete: employees=%s, telemetry_loaded=%s, telemetry_skipped=%s, telemetry_errors=%s, "
            "sessions=%s, daily_metrics=%s",
            result["employees_loaded"],
            result["telemetry_loaded"],
            result["telemetry_skipped"],
            result["telemetry_errors"],
            result["sessions_inserted"],
            result["daily_metrics_inserted"],
        )
        return 0
    except Exception as e:
        logger.exception("Ingestion failed: %s", e)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
