from __future__ import annotations

import os

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session, DeclarativeMeta

from app.db.session import get_db
from app.core.pdf_generator import generate_clinical_pdf_report
from app.core.report_renderer import (
    list_report_templates,
    render_report_html,
)
from app.services.report.report_service import build_report_from_storage
from app.utils.pdf_report import generate_medigenie_report
from io import BytesIO
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from app.models.models import (
    AIReport,
    Patient,
)

router = APIRouter(
    prefix="/reports",
    tags=["Clinical Reports"],
)

TEMP_DIR = "temp_reports"
os.makedirs(TEMP_DIR, exist_ok=True)


def _serialize_model(model: object) -> dict[str, object]:
    """Serialize a SQLAlchemy ORM model to a plain dict for template rendering."""
    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if isinstance(model.__class__, DeclarativeMeta):
        return {
            column.key: getattr(model, column.key)
            for column in model.__table__.columns
        }
    return {
        key: getattr(model, key)
        for key in dir(model)
        if not key.startswith("_") and not callable(getattr(model, key, None))
    }


@router.get("/{patient_id}/pdf")
def generate_pdf(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate a clinical PDF report for a patient (or report ID).
    If no AI report exists yet for a valid patient, generates a baseline patient clinical report.
    """
    logger.info("Searching report for target_id=%s", patient_id)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    summary = None

    if patient is not None:
        summary = (
            db.query(AIReport)
            .filter(AIReport.patient_id == patient.id)
            .order_by(AIReport.id.desc())
            .first()
        )

    # Fallback: Check if target_id is actually an AIReport ID
    if summary is None:
        summary = db.query(AIReport).filter(AIReport.id == patient_id).first()
        if summary is not None:
            patient = db.query(Patient).filter(Patient.id == summary.patient_id).first()

    if patient is None:
        logger.info("Patient not found for id=%s", patient_id)
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    summary_dict = _serialize_model(summary) if summary else {}
    report = build_report_from_storage(
        patient=_serialize_model(patient),
        summary=summary_dict,
        generated_at=summary.created_at.isoformat() if getattr(summary, 'created_at', None) else None,
    )

    pdf_bytes = generate_clinical_pdf_report(report)

    filename = f"MediGenie_Report_{patient.id}.pdf"
    output_path = os.path.join(TEMP_DIR, filename)

    with open(output_path, "wb") as fp:
        fp.write(pdf_bytes)

    logger.info("Generated PDF report output path=%s for patient_id=%s", output_path, patient.id)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/medigenie/{patient_id}/pdf")
def generate_medigenie_pdf(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate a MediGenie-styled clinical PDF report for a patient using the ReportLab template.
    Accepts patient_id or report_id as target_id.
    If no AI report exists yet for a valid patient, generates a baseline patient clinical report.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    summary = None

    if patient is not None:
        summary = (
            db.query(AIReport)
            .filter(AIReport.patient_id == patient.id)
            .order_by(AIReport.id.desc())
            .first()
        )

    # Fallback: Check if target_id is actually an AIReport ID
    if summary is None:
        summary = db.query(AIReport).filter(AIReport.id == patient_id).first()
        if summary is not None:
            patient = db.query(Patient).filter(Patient.id == summary.patient_id).first()

    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    summary_dict = _serialize_model(summary) if summary else {}
    report = build_report_from_storage(
        patient=_serialize_model(patient),
        summary=summary_dict,
        generated_at=summary.created_at.isoformat() if getattr(summary, 'created_at', None) else None,
    )

    pdf_bytes = generate_medigenie_report(report)

    stream = BytesIO(pdf_bytes)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=MediGenie_Report_{patient.id}.pdf"})


@router.get("/{patient_id}/html")
def generate_html(
    patient_id: int,
    template: str = "report_template.html",
    db: Session = Depends(get_db),
):
    """Return an HTML-rendered clinical report for a patient."""
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    summary = (
        db.query(AIReport)
        .filter(
            AIReport.patient_id == patient.id
        )
        .order_by(AIReport.id.desc())
        .first()
    )

    summary_dict = _serialize_model(summary) if summary else {}

    report = build_report_from_storage(
        patient=_serialize_model(patient),
        summary=summary_dict,
        generated_at=summary.created_at.isoformat() if getattr(summary, 'created_at', None) else None,
    )

    html = render_report_html(report, template_name=template)

    return HTMLResponse(content=html, media_type="text/html")


@router.get("/templates")
def available_templates():
    """Return a list of available report HTML templates."""
    return {"templates": list_report_templates()}
