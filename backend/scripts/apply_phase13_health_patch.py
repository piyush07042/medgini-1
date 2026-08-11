from pathlib import Path

health_path = Path('app/api/health.py')
health_text = '''"""
Health check endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.config import settings
from app.core.startup import app_state
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Returns application health status.
    """

    return ApiResponse(
        message="Application health status retrieved successfully.",
        data={
            "status": "healthy",
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "services": {
                "supervisor": app_state.supervisor is not None,
                "ml_model": app_state.ml_model is not None,
                "vector_store": app_state.vector_store is not None,
                "ocr": app_state.ocr_engine is not None,
            },
        },
    )


@router.get("/ready", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def readiness_probe(request: Request):
    """
    Returns application readiness status.
    """

    startup_error = getattr(request.app.state, "startup_error", False)
    if startup_error:
        return ApiResponse(
            success=False,
            message="Application startup failed.",
            data={
                "ready": False,
                "error": getattr(request.app.state, "startup_error_details", "Unknown startup error."),
            },
        )

    return ApiResponse(
        message="Application is ready.",
        data={"ready": True},
    )
'''

main_path = Path('app/main.py')
main_text = '''"""
MediGenie FastAPI Application
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes import api_router
from app.core.config import settings
from app.core.compression import configure_compression
from app.core.cors import configure_cors
from app.core.logging import configure_logging
from app.core.startup import validate_environment
from app.core.security_headers import configure_security_headers
from app.db.session import create_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    try:
        configure_logging()
        validate_environment()
        create_database()
    except asyncio.CancelledError:
        raise
    except Exception:
        app.state.startup_error = True
        app.state.startup_error_details = "startup initialization failed"

    try:
        yield
    except asyncio.CancelledError:
        return
    except Exception:
        raise


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Multi-Agent Clinical Decision Support System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.state.startup_error = False
app.state.startup_error_details = None

configure_cors(app)
configure_security_headers(app)
configure_compression(app)


@app.get("/")
def root():
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/health")


app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)
'''

test_path = Path('tests/test_health.py')
test_text = '''"""
Health endpoint tests.
"""

from fastapi import status


def test_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Application health status retrieved successfully."
    assert isinstance(body["data"], dict)
    assert body["data"]["application"] == "MediGenie"
    assert body["data"]["status"] == "healthy"
    assert "services" in body["data"]


def test_readiness(client):
    response = client.get("/api/v1/health/ready")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Application is ready."
    assert body["data"]["ready"] is True
'''

health_path.write_text(health_text, encoding='utf-8')
main_path.write_text(main_text, encoding='utf-8')
test_path.write_text(test_text, encoding='utf-8')
print('wrote files')
