"""
Central logging configuration for MediGenie.
"""

from __future__ import annotations

import contextvars
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


REQUEST_ID = contextvars.ContextVar("request_id", default="undefined")

LOG_DIRECTORY = Path(getattr(settings, "LOG_DIRECTORY", "logs"))
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "request_id=%(request_id)s | "
    "%(message)s"
)


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get("undefined")
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = settings.REQUEST_ID_HEADER):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name) or str(uuid4())
        REQUEST_ID.set(request_id)
        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


def configure_logging() -> None:
    """
    Configure application-wide logging.
    """

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(settings.LOG_LEVEL.upper())

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_DIRECTORY / "medigenie.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    request_id_filter = RequestIDFilter()
    console_handler.addFilter(request_id_filter)
    file_handler.addFilter(request_id_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger.
    """

    return logging.getLogger(name)