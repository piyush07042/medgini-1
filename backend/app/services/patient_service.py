"""
Patient management service helpers.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.models import AIReport, DrugSafetyAssessment, MedicalReport, Patient
from app.schemas.schemas import (
    MedicalHistoryEntryCreate,
    PaginatedPatientsSchema,
    PatientResponse,
    TimelineEventSchema,
    VisitRecordSchema,
)

RISK_LABELS = {
    "low": "Low",
    "moderate": "Moderate",
    "medium": "Moderate",
    "high": "High",
    "critical": "Critical",
}


def _format_date(value: datetime | None) -> str:
    if value is None:
        return datetime.utcnow().strftime("%Y-%m-%d")
    return value.strftime("%Y-%m-%d")


def _extract_risk(risk_assessment: dict[str, Any] | None) -> str:
    if not isinstance(risk_assessment, dict):
        return "Moderate"
    raw = (
        risk_assessment.get("risk_category")
        or risk_assessment.get("risk_level")
        or risk_assessment.get("confidence_label")
        or "moderate"
    )
    normalized = str(raw).strip().lower()
    return RISK_LABELS.get(normalized, str(raw).title())


def _extract_disease(risk_assessment: dict[str, Any] | None) -> str:
    if not isinstance(risk_assessment, dict):
        return "Clinical Analysis"
    for key in ("disease", "disease_type", "model_name", "condition", "target"):
        value = risk_assessment.get(key)
        if value:
            return str(value).replace("_", " ").title()
    return "Clinical Analysis"


def list_patients_paginated(
    db: Session,
    doctor_id: int,
    *,
    search: str = "",
    gender: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 8,
) -> PaginatedPatientsSchema:
    query = db.query(Patient).filter(Patient.doctor_id == doctor_id)

    normalized_search = search.strip().lower()
    if normalized_search:
        like_pattern = f"%{normalized_search}%"
        query = query.filter(
            or_(
                func.lower(Patient.first_name).like(like_pattern),
                func.lower(Patient.last_name).like(like_pattern),
                func.lower(func.concat(Patient.first_name, " ", Patient.last_name)).like(like_pattern),
            )
        )

    if gender and gender.lower() != "all":
        query = query.filter(func.lower(Patient.gender) == gender.lower())

    sort_column = {
        "first_name": Patient.first_name,
        "age": Patient.age,
        "gender": Patient.gender,
        "created_at": Patient.created_at,
    }.get(sort_by, Patient.created_at)

    if sort_dir.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 500)
    items = query.offset((safe_page - 1) * safe_page_size).limit(safe_page_size).all()

    return PaginatedPatientsSchema(
        items=[PatientResponse.model_validate(item) for item in items],
        total=total,
        page=safe_page,
        page_size=safe_page_size,
        total_pages=max(1, math.ceil(total / safe_page_size)) if total else 1,
    )


def build_medical_timeline(db: Session, patient: Patient) -> list[TimelineEventSchema]:
    events: list[TimelineEventSchema] = []

    events.append(
        TimelineEventSchema(
            id=f"registration-{patient.id}",
            title="Patient registered",
            description=f"{patient.first_name} {patient.last_name} was added to the registry.",
            event_type="registration",
            date=_format_date(patient.created_at),
            source="system",
        )
    )

    history = patient.medical_history if isinstance(patient.medical_history, dict) else {}
    manual_events = history.get("events") or []
    if isinstance(manual_events, list):
        for index, entry in enumerate(manual_events):
            if not isinstance(entry, dict):
                continue
            events.append(
                TimelineEventSchema(
                    id=str(entry.get("id") or f"history-{index}"),
                    title=str(entry.get("title") or "Medical history note"),
                    description=str(entry.get("description") or ""),
                    event_type=str(entry.get("event_type") or entry.get("type") or "note"),
                    date=str(entry.get("date") or _format_date(patient.created_at)),
                    source="manual",
                )
            )

    for report in (
        db.query(MedicalReport)
        .filter(MedicalReport.patient_id == patient.id)
        .order_by(MedicalReport.uploaded_at.desc())
        .all()
    ):
        status = "Completed" if report.extracted_text else "Pending OCR"
        events.append(
            TimelineEventSchema(
                id=f"report-{report.id}",
                title="Medical report uploaded",
                description=f"{report.file_name} — {status}",
                event_type="report",
                date=_format_date(report.uploaded_at),
                source="report",
            )
        )

    for ai_report in (
        db.query(AIReport)
        .filter(AIReport.patient_id == patient.id)
        .order_by(AIReport.created_at.desc())
        .all()
    ):
        disease = _extract_disease(ai_report.risk_assessment)
        risk = _extract_risk(ai_report.risk_assessment)
        events.append(
            TimelineEventSchema(
                id=f"prediction-{ai_report.id}",
                title=f"{disease} prediction",
                description=f"Risk level: {risk}",
                event_type="prediction",
                date=_format_date(ai_report.created_at),
                source="prediction",
            )
        )

    for assessment in (
        db.query(DrugSafetyAssessment)
        .filter(DrugSafetyAssessment.patient_id == patient.id)
        .order_by(DrugSafetyAssessment.created_at.desc())
        .all()
    ):
        events.append(
            TimelineEventSchema(
                id=f"drug-{assessment.id}",
                title="Drug safety review",
                description="Medication interaction and safety assessment completed.",
                event_type="medication",
                date=_format_date(assessment.created_at),
                source="drug_safety",
            )
        )

    events.sort(key=lambda item: item.date, reverse=True)
    return events


def build_visit_history(db: Session, patient: Patient) -> list[VisitRecordSchema]:
    visits: list[VisitRecordSchema] = []

    for report in (
        db.query(MedicalReport)
        .filter(MedicalReport.patient_id == patient.id)
        .order_by(MedicalReport.uploaded_at.desc())
        .all()
    ):
        visits.append(
            VisitRecordSchema(
                id=f"visit-report-{report.id}",
                date=_format_date(report.uploaded_at),
                visit_type="Report upload",
                summary=report.file_name,
                status="Completed" if report.extracted_text else "Pending",
            )
        )

    for ai_report in (
        db.query(AIReport)
        .filter(AIReport.patient_id == patient.id)
        .order_by(AIReport.created_at.desc())
        .all()
    ):
        disease = _extract_disease(ai_report.risk_assessment)
        risk = _extract_risk(ai_report.risk_assessment)
        visits.append(
            VisitRecordSchema(
                id=f"visit-prediction-{ai_report.id}",
                date=_format_date(ai_report.created_at),
                visit_type="Clinical prediction",
                summary=f"{disease} — {risk} risk",
                status="Completed",
            )
        )

    visits.sort(key=lambda item: item.date, reverse=True)
    return visits


def append_medical_history_entry(
    patient: Patient,
    entry: MedicalHistoryEntryCreate,
) -> dict[str, Any]:
    history = dict(patient.medical_history) if isinstance(patient.medical_history, dict) else {}
    events = list(history.get("events") or [])
    new_entry = {
        "id": str(uuid.uuid4()),
        "title": entry.title,
        "description": entry.description,
        "event_type": entry.event_type,
        "date": entry.date or datetime.utcnow().strftime("%Y-%m-%d"),
    }
    events.insert(0, new_entry)
    history["events"] = events
    patient.medical_history = history
    return new_entry
