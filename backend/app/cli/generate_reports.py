from __future__ import annotations

import argparse
import time
import os
from pathlib import Path
from typing import Optional, Callable, Any

from sqlalchemy.orm import DeclarativeMeta

from app.db.session import SessionLocal
from app.models.models import Patient, AIReport
from app.core.pdf_generator import generate_clinical_pdf_report
from app.services.report.report_service import build_report_from_storage


def _serialize_model(model: object) -> dict[str, object]:
    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if isinstance(model.__class__, DeclarativeMeta):
        return {column.key: getattr(model, column.key) for column in model.__table__.columns}
    return {
        key: getattr(model, key)
        for key in dir(model)
        if not key.startswith("_") and not callable(getattr(model, key, None))
    }


def run_reports(
    patient_id: Optional[int] = None,
    out_dir: str = "temp_reports",
    dry_run: bool = False,
    session_factory: Callable[[], Any] = SessionLocal,
) -> list[str]:
    """Generate PDF clinical reports for patients.

    Returns a list of produced file paths (or would-be paths in dry-run).
    """
    os.makedirs(out_dir, exist_ok=True)

    db = session_factory()
    try:
        if patient_id is not None:
            patients = db.query(Patient).filter(Patient.id == patient_id).all()
        else:
            patients = db.query(Patient).all()

        outputs: list[str] = []

        for patient in patients:
            summary = (
                db.query(AIReport)
                .filter(AIReport.patient_id == patient.id)
                .order_by(AIReport.id.desc())
                .first()
            )

            if summary is None:
                print(f"Skipping patient {patient.id}: no AI report available.")
                continue

            report = build_report_from_storage(
                patient=_serialize_model(patient),
                summary=_serialize_model(summary),
                generated_at=getattr(summary, "created_at", None).isoformat() if getattr(summary, "created_at", None) else None,
            )

            pdf_bytes = generate_clinical_pdf_report(report)

            filename = f"MediGenie_Report_{patient.id}.pdf"
            out_path = Path(out_dir) / filename

            if not dry_run:
                out_path.write_bytes(pdf_bytes)

            print(f"Report generated: {out_path}")
            outputs.append(str(out_path))

        return outputs
    finally:
        db.close()


def cli() -> None:
    parser = argparse.ArgumentParser(description="Generate clinical PDF reports for patients.")
    parser.add_argument("--patient-id", type=int, help="Single patient id to generate report for")
    parser.add_argument("--out-dir", type=str, default="temp_reports", help="Output directory for reports")
    parser.add_argument("--interval", type=int, default=0, help="If >0, run repeatedly every INTERVAL seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; show what would be generated")

    args = parser.parse_args()

    try:
        if args.interval and args.interval > 0:
            print(f"Starting scheduled report generation every {args.interval} seconds. Ctrl+C to stop.")
            while True:
                run_reports(patient_id=args.patient_id, out_dir=args.out_dir, dry_run=args.dry_run)
                time.sleep(args.interval)
        else:
            run_reports(patient_id=args.patient_id, out_dir=args.out_dir, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("Scheduler stopped by user.")


if __name__ == "__main__":
    cli()
