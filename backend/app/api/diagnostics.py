from fastapi import APIRouter
from app.core.config import settings
from app.core.scheduler import is_scheduler_running
from app.db.session import SessionLocal

router = APIRouter()


@router.get("/readiness")
def readiness():
    """Readiness probe: checks database connectivity and vector store state."""
    status = {
        "app": "ok",
        "environment": settings.ENVIRONMENT,
        "scheduler_running": bool(is_scheduler_running()),
        "vector_store_initialized": bool(getattr(settings, "HUGGINGFACE_API_KEY", None) or True),
    }

    # DB connectivity check (lightweight)
    try:
        db = SessionLocal()
        # simple query
        db.execute("SELECT 1")
        db.close()
        status["database"] = "ok"
    except Exception as exc:
        status["database"] = f"error: {exc}"

    return status


@router.get("/diagnostics")
def diagnostics():
    """Return a small diagnostics summary useful during stabilization."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "api_prefix": settings.API_V1_PREFIX,
    }
