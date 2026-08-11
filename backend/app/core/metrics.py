"""
Application metrics support for MediGenie.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry
from prometheus_client import CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "medigenie_http_requests_total",
    "Total HTTP requests processed by MediGenie",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "medigenie_http_request_duration_seconds",
    "HTTP request latency for MediGenie",
    ["method", "endpoint"],
)

registry = CollectorRegistry()


def configure_metrics(app: FastAPI) -> None:
    """Attach metrics middleware to the FastAPI app."""

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        path = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=path,
            http_status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=path,
        ).observe(elapsed)
        return response


def get_metrics() -> str:
    """Return the current Prometheus metrics payload."""
    return generate_latest()
