Phase 11–13 Implementation Plan
=================================

Overview
--------
This document outlines the next-phase implementation work for:

- Phase 11 — Drug safety agent integration
- Phase 12 — Report automation & templates
- Phase 13 — Full integration & stabilization

High-level goals
-----------------
- Phase 11: Surface drug-safety alerts to external APIs, notifications, and logging. Add endpoints to retrieve safety assessments for a patient or medication list.
- Phase 12: Automate report generation (CLI + schedule), add template variants, and provide tests for templates and PDF rendering.
- Phase 13: Add readiness/liveness checks, end-to-end integration tests, CI pipeline steps, and finalize cleanup/observability.

Planned tasks (initial)
-----------------------
Phase 11
- 11.1: Add an API endpoint to fetch/store drug-safety assessments (`/drug-safety`) and integrate it into the Supervisor workflow.
- 11.2: Add a notification hook (simple webhooks or event emitter) to post alerts when `DrugSafetyAgent` returns `FLAGGED`.
- 11.3: Expand `app/core/drug_safety.py` knowledge base and provide a mapping translator for clinical terms.

Phase 12
- 12.1: Provide `scripts/run_full_pipeline.py` to generate sample reports (HTML + PDF). (scaffolded)
- 12.2: Add template variants under `templates/` for short/long report formats and tests to validate rendering.
- 12.3: Add a scheduler integration plan (e.g., a simple cron-like runner or integration with APScheduler).

Phase 13
- 13.1: Create an end-to-end test that runs a sample report through intake → agents → report generation and asserts output exists.
- 13.2: Add health & readiness endpoints and integrate with container probes.
- 13.3: Add CI workflow steps to run tests and report generation in the repository.

How I can proceed next
----------------------
- Implement `app/api/drug_safety.py` endpoints and the notification hook now.
- Create template variants and add unit tests for rendering.
- Add simple health-check endpoints and a basic GitHub Actions CI workflow.

Tell me which of these to implement first, or say "implement all" and I will proceed in order.
