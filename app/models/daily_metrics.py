"""SQLAlchemy model for daily aggregated metrics."""
from datetime import date
from sqlalchemy import Column, Date, Integer, String
from app.database import Base


class DailyMetric(Base):
    """One row per (date, metric_name). metric_name: total_events, total_sessions, unique_users."""

    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(Date, nullable=False, index=True)
    metric_name = Column(String(64), nullable=False, index=True)
    value = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<DailyMetric date={self.metric_date} {self.metric_name}={self.value}>"
