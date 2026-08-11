"""
Global exception definitions and handlers for MediGenie.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# =====================================================
# Base Application Exception
# =====================================================

class MediGenieException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# =====================================================
# Workflow
# =====================================================

class WorkflowException(MediGenieException):
    """Workflow execution error."""


class SupervisorException(MediGenieException):
    """Supervisor execution error."""


class AgentExecutionException(MediGenieException):
    """Agent execution failure."""


# =====================================================
# OCR
# =====================================================

class OCRException(MediGenieException):
    """OCR processing error."""


# =====================================================
# ML
# =====================================================

class ModelInferenceException(MediGenieException):
    """Disease prediction error."""


# =====================================================
# RAG
# =====================================================

class KnowledgeRetrievalException(MediGenieException):
    """Knowledge retrieval error."""


# =====================================================
# PDF
# =====================================================

class ReportGenerationException(MediGenieException):
    """PDF generation error."""


# =====================================================
# Global Handlers
# =====================================================

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all application exception handlers.
    """

    @app.exception_handler(MediGenieException)
    async def medigenie_exception_handler(
        request: Request,
        exc: MediGenieException,
    ):
        logger.error(exc.message)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "ERROR",
                "message": exc.message,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "status": "VALIDATION_ERROR",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "HTTP_ERROR",
                "message": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(exc)

        return JSONResponse(
            status_code=500,
            content={
                "status": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected server error.",
            },
        )