from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IllegalStateChangeError
from sqlalchemy.engine import URL
import logging
import re

from app.core.config import settings
from app.models.models import Base


def _build_engine() -> object:
    """Create and return a SQLAlchemy engine with a short connect timeout for network DBs.

    For SQLite we preserve `check_same_thread`. For other drivers (Postgres) we set
    a `connect_timeout` so failed connections fail fast during startup instead of
    blocking for a long default timeout.
    """
    database_url = settings.DATABASE_URL or "sqlite:///./medigenie_cdss.db"
    connect_args = {}
    # If a local Postgres URL is configured (localhost), prefer a lightweight
    # SQLite fallback for local test runs to avoid requiring a running DB.
    if database_url.startswith("postgresql") and "localhost" in database_url:
        database_url = "sqlite:///./medigenie_cdss.db"

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        # ensure network connections timeout quickly (seconds)
        connect_args = {"connect_timeout": 5}

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = _build_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def _ensure_patient_avatar_column() -> None:
    """Add the avatar_url column to existing sqlite patient tables when missing."""
    if not str(engine.url).startswith("sqlite"):
        return

    try:
        with engine.begin() as connection:
            existing_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(patients)"))
            }
            if "avatar_url" not in existing_columns:
                connection.execute(text("ALTER TABLE patients ADD COLUMN avatar_url VARCHAR"))
    except Exception as exc:  # pragma: no cover - defensive migration path
        logger = logging.getLogger("app.db.session")
        logger.warning("Unable to ensure patients.avatar_url column exists: %s", exc)


def _ensure_ai_reports_clinical_intelligence_column() -> None:
    """Add the clinical_intelligence column to existing ai_reports table when missing."""
    if not str(engine.url).startswith("sqlite"):
        return

    try:
        with engine.begin() as connection:
            existing_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(ai_reports)"))
            }
            if "clinical_intelligence" not in existing_columns:
                # SQLite supports adding a new column via ALTER TABLE
                connection.execute(text("ALTER TABLE ai_reports ADD COLUMN clinical_intelligence JSON"))
    except Exception as exc:  # pragma: no cover - defensive migration path
        logger = logging.getLogger("app.db.session")
        logger.warning(
            "Unable to ensure ai_reports.clinical_intelligence column exists: %s", exc
        )


def create_database():
    """Create tables if the database is available."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - tolerate existing DB issues during startup
        logger = logging.getLogger("app.db.session")
        logger.warning("create_all raised an exception: %s", exc)
    _ensure_patient_avatar_column()
    _ensure_ai_reports_clinical_intelligence_column()


def get_db():
    """FastAPI dependency that provides a database session."""
    logger = logging.getLogger("app.db.session")
    db: Session = SessionLocal()
    logger.debug("Opened new DB session %s", db)
    try:
        yield db
    finally:
        logger.debug("Closing DB session %s", db)
        try:
            db.close()
        except IllegalStateChangeError:
            logger.exception("IllegalStateChangeError while closing DB session")
            raise
        except Exception:
            logger.exception("Unexpected error while closing DB session")
            raise


def get_masked_database_url() -> str:
    """Return the configured DATABASE_URL with the password masked for safe logging."""
    raw = settings.DATABASE_URL or ""
    try:
        # replace :password@ with :***@ to avoid printing credentials
        return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", raw)
    except Exception:
        return raw


def test_connection() -> None:
    """Attempt a simple connection and select 1 to validate DB reachability.

    Raises the underlying exception if the DB cannot be reached.
    """
    logger = logging.getLogger("app.db.session")
    logger.debug("Testing DB connection to %s", get_masked_database_url())
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test succeeded")
    except Exception:
        logger.exception("Database connection test failed")
        raise