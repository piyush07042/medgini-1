"""
Audit logging utilities.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("audit")


def audit_log(
    user: str,
    action: str,
    resource: str,
) -> None:

    logger.info(
        "user=%s action=%s resource=%s",
        user,
        action,
        resource,
    )