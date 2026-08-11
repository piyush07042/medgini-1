"""Simple notification helpers for MediGenie.

Provides a webhook sender and a domain-specific helper for drug-safety alerts.
"""

from __future__ import annotations

import logging
import requests
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_webhook(url: str, payload: dict[str, Any], timeout: int = 5) -> dict[str, Any] | None:
    """Send a JSON webhook POST to `url`. Returns response JSON on success or None on failure."""
    if not url:
        logger.debug("No webhook URL configured; skipping notification")
        return None

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code}
    except Exception as exc:  # pragma: no cover - network behaviour
        logger.exception("Failed to send webhook: %s", exc)
        return None


def send_drug_safety_alert(payload: dict[str, Any]) -> None:
    """Domain helper to send drug-safety alerts using configured webhook URL."""
    url = getattr(settings, "DRUG_SAFETY_WEBHOOK_URL", None)
    if not url:
        logger.info("Drug safety webhook not configured; alert suppressed.")
        return

    logger.info("Sending drug safety alert to webhook: %s", url)
    send_webhook(url, payload)
