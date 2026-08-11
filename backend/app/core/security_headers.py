"""
HTTP security headers middleware.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"

        # Allow iframe rendering for reports; use SAMEORIGIN for other routes
        if "/reports" in request.url.path:
            if "X-Frame-Options" in response.headers:
                del response.headers["X-Frame-Options"]
        else:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["X-XSS-Protection"] = "1; mode=block"

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response


def configure_security_headers(
    app: FastAPI,
) -> None:

    app.add_middleware(
        SecurityHeadersMiddleware
    )