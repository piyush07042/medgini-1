from __future__ import annotations
"""
ASGI compatibility shim: expose the FastAPI `app` object as
`app.main:app` for deployments that expect this module layout.
"""

# Import the real application object from the package root `main.py`.
# This file intentionally keeps the import minimal to act as a thin shim.
from main import app  # noqa: E402

__all__ = ["app"]
