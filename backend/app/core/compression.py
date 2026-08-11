"""
Response compression.
"""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware


def configure_compression(
    app: FastAPI,
) -> None:

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1024,
    )