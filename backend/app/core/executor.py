"""
Shared thread pool for CPU-intensive work.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(
    max_workers=4,
)