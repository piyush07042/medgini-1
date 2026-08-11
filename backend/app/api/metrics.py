"""
Prometheus metrics endpoint for MediGenie.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


@router.get("", response_class=Response, status_code=status.HTTP_200_OK)
async def get_metrics():
    """Return Prometheus metrics for the application."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
