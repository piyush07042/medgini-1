"""
Common API response schemas used throughout MediGenie.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiResponse(BaseModel):
    """
    Standard successful API response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    success: bool = True

    message: str

    data: Any | None = None


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    success: bool = False

    message: str

    detail: Any | None = None