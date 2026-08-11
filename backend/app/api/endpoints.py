"""
General API Endpoints
=====================

Small compatibility router for project-level utility endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }
