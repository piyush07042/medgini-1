"""
Startup validation and shared application state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from ml.registry import get_model_registry, resolve_model_directory


@dataclass
class AppState:
    """Shared runtime state for the backend application."""

    supervisor: Any = None
    ml_model: Any = None
    vector_store: Any = None
    ocr_engine: Any = None
    model_registry: dict[str, Any] | None = None
    heart_disease_service: Any = None
    heart_failure_service: Any = None
    diabetes_service: Any = None
    kidney_disease_service: Any = None
    liver_disease_service: Any = None
    breast_cancer_service: Any = None
    parkinsons_service: Any = None
    hepatitis_service: Any = None
    stroke_service: Any = None
    stroke_model_directory: str | None = None
    prediction_service: Any = None


app_state = AppState()


def validate_environment() -> None:
    """
    Validate required configuration at startup.
    """
    _validate_environment()
    _validate_required_settings()
    _validate_directories()
    _validate_database_connection()
    _validate_model_registry()
    _validate_heart_disease_model_path()
    _validate_heart_failure_model_path()
    _validate_kidney_disease_model_path()
    _validate_liver_disease_model_path()
    _validate_breast_cancer_model_path()
    _validate_parkinsons_model_path()
    _validate_hepatitis_model_path()
    _validate_stroke_model_path()


ROOT_DIR = Path(__file__).resolve().parents[2]


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def _ensure_directory(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create required directory '{path}': {exc}"
        ) from exc

    if not path.exists() or not path.is_dir():
        raise RuntimeError(f"Required directory '{path}' is not available.")

    return path


def _validate_environment() -> None:
    if settings.ENVIRONMENT not in {"development", "production", "testing"}:
        raise RuntimeError(
            "ENVIRONMENT must be one of development, production, or testing."
        )

    if settings.ENVIRONMENT == "production" and settings.DEBUG:
        raise RuntimeError("DEBUG must be disabled in production environment.")


def _validate_required_settings() -> None:
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be configured.")
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured.")


def _validate_directories() -> None:
    _ensure_directory(_resolve_path(settings.UPLOAD_DIRECTORY))
    _ensure_directory(_resolve_path(settings.LOG_DIRECTORY))
    _ensure_directory(_resolve_path(settings.RAG_DB_DIRECTORY))
    _ensure_directory(_resolve_path(settings.MODEL_ROOT))


def _validate_model_registry() -> None:
    registry = get_model_registry()
    app_state.model_registry = registry
    if not registry:
        logging.warning("No packaged models were found during startup validation.")


def _validate_database_connection() -> None:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(
            f"Unable to connect to database: {exc}"
        ) from exc
    finally:
        try:
            db.close()
        except Exception:
            logging.warning("Failed to close database session during startup validation.")


def _validate_heart_disease_model_path() -> None:
    model_path = resolve_model_directory("heart_disease")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Heart disease model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Heart disease model directory is missing required artifacts: {model_path}"
        )
        # Register model path in global app state for health checks
        from app.core.startup import app_state as _app_state  # local import to avoid cycles
        try:
            _app_state.ml_model = str(model_path)
        except Exception:
            pass


def _validate_heart_failure_model_path() -> None:
    model_path = resolve_model_directory("heart_failure_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Heart failure model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Heart failure model directory is missing required artifacts: {model_path}"
        )


def _validate_kidney_disease_model_path() -> None:
    model_path = resolve_model_directory("kidney_disease_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Kidney disease model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Kidney disease model directory is missing required artifacts: {model_path}"
        )


def _validate_liver_disease_model_path() -> None:
    model_path = resolve_model_directory("liver_disease_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Liver disease model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Liver disease model directory is missing required artifacts: {model_path}"
        )


def _validate_breast_cancer_model_path() -> None:
    model_path = resolve_model_directory("breast_cancer_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Breast cancer model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Breast cancer model directory is missing required artifacts: {model_path}"
        )


def _validate_parkinsons_model_path() -> None:
    model_path = resolve_model_directory("parkinsons_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Parkinson's model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Parkinson's model directory is missing required artifacts: {model_path}"
        )


def _validate_hepatitis_model_path() -> None:
    model_path = resolve_model_directory("hepatitis_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Hepatitis model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "preprocessor.joblib", "schema.json"]
    ):
        raise RuntimeError(
            f"Hepatitis model directory is missing required artifacts: {model_path}"
        )


def _validate_stroke_model_path() -> None:
    model_path = resolve_model_directory("stroke_model")
    if not model_path.exists() or not model_path.is_dir():
        raise RuntimeError(
            f"Stroke model directory not found: {model_path}"
        )

    if not any(
        (model_path / filename).exists()
        for filename in ["model.joblib", "metadata.json", "schema.json"]
    ):
        raise RuntimeError(
            f"Stroke model directory is missing required artifacts: {model_path}"
        )
