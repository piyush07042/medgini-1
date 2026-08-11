"""
Health check endpoints.
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.core.startup import app_state
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

_STARTUP_TIME = datetime.now(timezone.utc).isoformat()


@router.get("", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Returns comprehensive application health status including all services,
    model registry, agent registry and Phase C capability flags.
    """

    # ── Service status ────────────────────────────────────────────────
    services = {
        "supervisor": app_state.supervisor is not None,
        "ml_model": app_state.ml_model is not None,
        "vector_store": app_state.vector_store is not None,
        "ocr": app_state.ocr_engine is not None,
        "heart_disease_model": app_state.heart_disease_service is not None,
        "diabetes_model": app_state.diabetes_service is not None,
        "breast_cancer_model": app_state.breast_cancer_service is not None,
        "parkinsons_model": app_state.parkinsons_service is not None,
        "kidney_disease_model": app_state.kidney_disease_service is not None,
    }

    # ── Model registry breakdown ──────────────────────────────────────
    model_registry = app_state.model_registry or {}
    model_registry_detail = {
        name: {"loaded": True}
        for name in model_registry
    }

    # ── Agent registry count ──────────────────────────────────────────
    agent_registry_size = 0
    try:
        from app.agents.supervisor.registry import get_workflow_agents
        from app.agents.base.agent_state import AgentState
        _sample_state = AgentState()
        agents = get_workflow_agents(_sample_state)
        agent_registry_size = len(agents)
        agent_names = [getattr(a, "agent_name", str(type(a).__name__)) for a in agents]
    except Exception:
        agent_names = []

    # ── Phase C capability flags ──────────────────────────────────────
    capabilities = {
        "clinical_intelligence": True,          # Phase B
        "execution_logging": True,              # Phase C – orchestrator
        "rag_re_ranking": True,                 # Phase C – knowledge agent
        "drug_severity_scoring": True,          # Phase C – drug safety
        "alternative_medications": True,        # Phase C – drug safety
        "ci_integrated_recommendations": True,  # Phase C – recommendation service
        "nine_section_reports": True,           # Phase C – report service
        "chat_follow_up_suggestions": True,     # Phase C – chat agent
        "rag_source_citations": True,           # Phase C – chat agent
        "streaming_chat": True,
    }

    overall_status = "healthy" if all(
        services[k] for k in ("supervisor", "ml_model", "vector_store")
        if services[k] is not None
    ) else "degraded"

    return ApiResponse(
        message="Application health status retrieved successfully.",
        data={
            "status": overall_status,
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "startup_time": _STARTUP_TIME,
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "services": services,
            "model_registry": {
                "size": len(model_registry),
                "models": model_registry_detail,
            },
            "agent_registry": {
                "size": agent_registry_size,
                "agents": agent_names,
            },
            "capabilities": capabilities,
        },
    )


@router.get("/ready", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def readiness_probe(request: Request):
    """
    Returns application readiness status.
    Returns 503 if startup failed.
    """

    startup_error = getattr(request.app.state, "startup_error", False)
    if startup_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Application startup failed.",
                "data": {
                    "ready": False,
                    "error": getattr(request.app.state, "startup_error_details", "Unknown startup error."),
                },
            },
        )

    return ApiResponse(
        success=True,
        message="Application is ready.",
        data={
            "ready": True,
            "services_online": {
                "supervisor": app_state.supervisor is not None,
                "ml_model": app_state.ml_model is not None,
                "vector_store": app_state.vector_store is not None,
            },
        },
    )


@router.get("/live", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def liveness_probe():
    """
    Returns application liveness status (always 200 if process is alive).
    """

    return ApiResponse(
        message="Application is live.",
        data={
            "live": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

