"""
Model registry endpoints for MediGenie.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.startup import app_state
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/models",
    tags=["Model Registry"],
)


@router.get("", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def list_models():
    """List all packaged models discovered during startup."""
    registry = app_state.model_registry or {}
    return ApiResponse(
        message="Packaged model registry retrieved successfully.",
        data={
            "model_count": len(registry),
            "models": [
                {"name": name, "path": str(path)} for name, path in sorted(registry.items())
            ],
        },
    )
