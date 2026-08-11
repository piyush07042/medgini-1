"""
Performance utilities.
"""

from __future__ import annotations

import time
from functools import wraps


def measure_execution_time(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):

        start = time.perf_counter()

        result = await func(
            *args,
            **kwargs,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"{func.__name__}: "
            f"{elapsed:.3f}s"
        )

        return result

    return wrapper