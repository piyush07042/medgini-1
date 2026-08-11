from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.core.config import settings


_scheduler: Optional[object] = None


def _run_reports_job(patient_id: Optional[int], out_dir: str, dry_run: bool):
    # Import here to avoid circular imports at module import time
    from app.cli.generate_reports import run_reports

    try:
        # run_reports is synchronous; run in a thread to avoid blocking the event loop
        return asyncio.get_event_loop().run_in_executor(None, run_reports, patient_id, out_dir, dry_run)
    except Exception as exc:
        logging.exception("Report job failed: %s", exc)


def start_scheduler(app=None) -> AsyncIOScheduler:
    """Start the AsyncIO scheduler if enabled via settings.

    Returns the scheduler instance (started) or raises if disabled.
    """
    global _scheduler

    if not settings.SCHEDULER_ENABLED or settings.SCHEDULER_INTERVAL_SECONDS <= 0:
        raise RuntimeError("Scheduler is not enabled or interval is not set")

    if _scheduler is not None:
        return _scheduler

    interval = settings.SCHEDULER_INTERVAL_SECONDS
    patient_id = settings.SCHEDULER_PATIENT_ID
    out_dir = settings.SCHEDULER_OUT_DIR
    dry_run = settings.SCHEDULER_DRY_RUN
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except Exception as exc:
        raise RuntimeError("APScheduler is not installed: %s" % exc)

    scheduler = AsyncIOScheduler()
    trigger = IntervalTrigger(seconds=interval)
    scheduler.add_job(_run_reports_job, trigger, args=[patient_id, out_dir, dry_run], id="medigenie_report_job", replace_existing=True)

    scheduler.start()
    _scheduler = scheduler
    logging.getLogger("medigenie").info("Report scheduler started (every %s seconds)", interval)
    return _scheduler


def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            logging.exception("Error shutting down scheduler")
        _scheduler = None


def is_scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running
