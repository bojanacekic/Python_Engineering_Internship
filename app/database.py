"""
SQLAlchemy engine and session factory. Uses SQLite and creates tables on startup.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings

Base = declarative_base()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not exist."""
    # Import models so they register with Base.metadata (avoids circular import)
    from app.models import telemetry as _telemetry  # noqa: F401
    from app.models import employee as _employee   # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
