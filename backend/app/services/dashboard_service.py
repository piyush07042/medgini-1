"""
Dashboard aggregation service.
"""

from __future__ import annotations

from calendar import month_abbr
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.startup import app_state
from app.models.models import (
    AIReport,
    DrugSafetyAssessment,
    MedicalReport,
    Patient,
)
from app.schemas.dashboard import (
    ActivityEventSchema,
    AreaDataSchema,
    BarSliceSchema,
    DashboardDataSchema,
    DashboardStatSchema,
    DashboardSummarySchema,
    LinePointSchema,
    PieSliceSchema,
    RecentPatientSchema,
    RecentPredictionSchema,
    RecentReportSchema,
    SystemStatusSchema,
)

DISEASE_MODELS = [
    "Heart Disease",
    "Heart Failure",
    "Diabetes",
    "Kidney Disease",
    "Liver Disease",
    "Breast Cancer",
    "Parkinson's",
    "Hepatitis",
    "Stroke",
]

RISK_LABELS = {
    "low": "Low",
    "moderate": "Moderate",
    "medium": "Moderate",
    "high": "High",
    "critical": "Critical",
}


def _start_of_month(reference: datetime) -> datetime:
    return reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_shift(reference: datetime, months: int) -> datetime:
    month_index = reference.month - 1 + months
    year = reference.year + month_index // 12
    month = month_index % 12 + 1
    return reference.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _format_trend(current: int, previous: int) -> tuple[str, bool]:
    if previous <= 0:
        if current <= 0:
            return "No change", True
        return f"+{current}", True

    delta = ((current - previous) / previous) * 100
    rounded = round(delta, 1)
    if rounded > 0:
        return f"+{rounded}%", True
    if rounded < 0:
        return f"{rounded}%", False
    return "No change", True


def _format_number(value: int) -> str:
    return f"{value:,}"


def _extract_risk_category(risk_assessment: dict[str, Any] | None) -> str:
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

    nested = risk_assessment.get("disease_risk_assessment")
    if isinstance(nested, dict):
        for key in ("disease", "disease_type", "model_name"):
            value = nested.get(key)
            if value:
                return str(value).replace("_", " ").title()

    return "Clinical Analysis"


def _extract_confidence(risk_assessment: dict[str, Any] | None) -> str:
    if not isinstance(risk_assessment, dict):
        return "N/A"

    for key in ("confidence", "probability", "risk_score", "estimated_risk_score_percent"):
        value = risk_assessment.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
            if numeric <= 1:
                numeric *= 100
            return f"{round(numeric)}%"
        except (TypeError, ValueError):
            continue
    return "N/A"


def _is_high_risk(risk_assessment: dict[str, Any] | None) -> bool:
    category = _extract_risk_category(risk_assessment).lower()
    return category in {"high", "critical"}


def _relative_time(value: datetime | None) -> str:
    if value is None:
        return "Unknown"

    now = datetime.utcnow()
    delta = now - value.replace(tzinfo=None)
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    return value.strftime("%Y-%m-%d")


def _patient_ids_for_doctor(db: Session, doctor_id: int) -> list[int]:
    rows = (
        db.query(Patient.id)
        .filter(Patient.doctor_id == doctor_id)
        .all()
    )
    return [row[0] for row in rows]


def _count_in_range(
    db: Session,
    model,
    timestamp_column,
    patient_ids: list[int],
    start: datetime,
    end: datetime,
    patient_column=None,
) -> int:
    if not patient_ids:
        return 0

    query = db.query(func.count(model.id))
    if patient_column is not None:
        query = query.filter(patient_column.in_(patient_ids))
    return int(
        query.filter(timestamp_column >= start, timestamp_column < end).scalar() or 0
    )


def build_dashboard(db: Session, doctor_id: int) -> DashboardDataSchema:
    now = datetime.utcnow()
    current_month_start = _start_of_month(now)
    previous_month_start = _month_shift(current_month_start, -1)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    patient_ids = _patient_ids_for_doctor(db, doctor_id)
    total_patients = len(patient_ids)

    ai_report_query = db.query(AIReport).filter(AIReport.patient_id.in_(patient_ids)) if patient_ids else db.query(AIReport).filter(AIReport.patient_id == -1)
    total_ai_reports = ai_report_query.count()

    medical_report_query = (
        db.query(MedicalReport).filter(MedicalReport.patient_id.in_(patient_ids))
        if patient_ids
        else db.query(MedicalReport).filter(MedicalReport.patient_id == -1)
    )
    total_medical_reports = medical_report_query.count()
    ocr_reports = medical_report_query.filter(MedicalReport.extracted_text.isnot(None)).count()

    high_risk_today = 0
    high_risk_total = 0
    if patient_ids:
        ai_reports = ai_report_query.all()
        for report in ai_reports:
            if _is_high_risk(report.risk_assessment):
                high_risk_total += 1
                created_at = report.created_at or now
                if created_at >= today_start:
                    high_risk_today += 1

    model_count = len(app_state.model_registry or {}) or len(DISEASE_MODELS)

    patients_this_month = _count_in_range(
        db, Patient, Patient.created_at, patient_ids, current_month_start, now
    )
    patients_last_month = _count_in_range(
        db, Patient, Patient.created_at, patient_ids, previous_month_start, current_month_start
    )
    reports_this_month = _count_in_range(
        db, AIReport, AIReport.created_at, patient_ids, current_month_start, now, AIReport.patient_id
    )
    reports_last_month = _count_in_range(
        db, AIReport, AIReport.created_at, patient_ids, previous_month_start, current_month_start, AIReport.patient_id
    )
    predictions_this_month = reports_this_month
    predictions_last_month = reports_last_month
    ocr_this_month = _count_in_range(
        db,
        MedicalReport,
        MedicalReport.uploaded_at,
        patient_ids,
        current_month_start,
        now,
        MedicalReport.patient_id,
    )
    ocr_last_month = _count_in_range(
        db,
        MedicalReport,
        MedicalReport.uploaded_at,
        patient_ids,
        previous_month_start,
        current_month_start,
        MedicalReport.patient_id,
    )

    patient_trend, patient_positive = _format_trend(patients_this_month, patients_last_month)
    report_trend, report_positive = _format_trend(reports_this_month, reports_last_month)
    prediction_trend, prediction_positive = _format_trend(predictions_this_month, predictions_last_month)
    ocr_trend, ocr_positive = _format_trend(ocr_this_month, ocr_last_month)

    stats = [
        DashboardStatSchema(
            title="Total Patients",
            value=_format_number(total_patients),
            trend=patient_trend,
            positive=patient_positive,
            label="Month over month",
        ),
        DashboardStatSchema(
            title="AI Reports Generated",
            value=_format_number(total_ai_reports),
            trend=report_trend,
            positive=report_positive,
            label="Last 30 days trend",
        ),
        DashboardStatSchema(
            title="Total Disease Predictions",
            value=_format_number(total_ai_reports),
            trend=prediction_trend,
            positive=prediction_positive,
            label="Clinical workflow runs",
        ),
        DashboardStatSchema(
            title="Disease Models Available",
            value=str(model_count),
            trend="Stable",
            positive=True,
            label="Clinical catalog",
        ),
        DashboardStatSchema(
            title="High Risk Cases",
            value=str(high_risk_today),
            trend=f"{high_risk_total} total",
            positive=high_risk_today == 0,
            label="Current day",
        ),
        DashboardStatSchema(
            title="OCR Reports Processed",
            value=_format_number(ocr_reports or total_medical_reports),
            trend=ocr_trend,
            positive=ocr_positive,
            label="This month",
        ),
    ]

    recent_patients: list[RecentPatientSchema] = []
    if patient_ids:
        patients = (
            db.query(Patient)
            .filter(Patient.doctor_id == doctor_id)
            .order_by(Patient.created_at.desc())
            .limit(5)
            .all()
        )
        for patient in patients:
            last_ai = (
                db.query(AIReport.created_at)
                .filter(AIReport.patient_id == patient.id)
                .order_by(AIReport.created_at.desc())
                .first()
            )
            last_medical = (
                db.query(MedicalReport.uploaded_at)
                .filter(MedicalReport.patient_id == patient.id)
                .order_by(MedicalReport.uploaded_at.desc())
                .first()
            )
            candidates = [patient.created_at]
            if last_ai and last_ai[0]:
                candidates.append(last_ai[0])
            if last_medical and last_medical[0]:
                candidates.append(last_medical[0])
            last_visit = max(candidates).strftime("%Y-%m-%d") if candidates else "N/A"

            recent_patients.append(
                RecentPatientSchema(
                    id=patient.id,
                    name=f"{patient.first_name} {patient.last_name}".strip(),
                    age=patient.age,
                    gender=patient.gender,
                    lastVisit=last_visit,
                )
            )

    recent_reports: list[RecentReportSchema] = []
    if patient_ids:
        medical_reports = (
            db.query(MedicalReport)
            .filter(MedicalReport.patient_id.in_(patient_ids))
            .order_by(MedicalReport.uploaded_at.desc())
            .limit(5)
            .all()
        )
        for report in medical_reports:
            status = "Completed" if report.extracted_text else "Pending"
            recent_reports.append(
                RecentReportSchema(
                    id=report.id,
                    filename=report.file_name,
                    uploadedAt=(report.uploaded_at or now).strftime("%Y-%m-%d"),
                    status=status,
                )
            )

        if len(recent_reports) < 5:
            ai_reports = (
                db.query(AIReport, Patient)
                .join(Patient, Patient.id == AIReport.patient_id)
                .filter(AIReport.patient_id.in_(patient_ids))
                .order_by(AIReport.created_at.desc())
                .limit(5 - len(recent_reports))
                .all()
            )
            for ai_report, patient in ai_reports:
                recent_reports.append(
                    RecentReportSchema(
                        id=ai_report.id,
                        filename=f"AI Report - {patient.first_name} {patient.last_name}",
                        uploadedAt=(ai_report.created_at or now).strftime("%Y-%m-%d"),
                        status="Completed",
                    )
                )

    recent_predictions: list[RecentPredictionSchema] = []
    if patient_ids:
        prediction_rows = (
            db.query(AIReport, Patient)
            .join(Patient, Patient.id == AIReport.patient_id)
            .filter(AIReport.patient_id.in_(patient_ids))
            .order_by(AIReport.created_at.desc())
            .limit(5)
            .all()
        )
        for ai_report, patient in prediction_rows:
            recent_predictions.append(
                RecentPredictionSchema(
                    id=ai_report.id,
                    patient=f"{patient.first_name} {patient.last_name}".strip(),
                    disease=_extract_disease(ai_report.risk_assessment),
                    risk=_extract_risk_category(ai_report.risk_assessment),
                    confidence=_extract_confidence(ai_report.risk_assessment),
                    date=(ai_report.created_at or now).strftime("%Y-%m-%d"),
                )
            )

    disease_counts: dict[str, int] = {name: 0 for name in DISEASE_MODELS}
    risk_counts = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    monthly_predictions: dict[str, int] = {}
    monthly_reports: dict[str, int] = {}
    monthly_generated: dict[str, int] = {}

    if patient_ids:
        for ai_report in ai_report_query.all():
            disease = _extract_disease(ai_report.risk_assessment)
            matched = False
            for model_name in DISEASE_MODELS:
                if model_name.lower() in disease.lower() or disease.lower() in model_name.lower():
                    disease_counts[model_name] += 1
                    matched = True
                    break
            if not matched and disease != "Clinical Analysis":
                disease_counts[disease] = disease_counts.get(disease, 0) + 1

            risk_label = _extract_risk_category(ai_report.risk_assessment)
            if risk_label in risk_counts:
                risk_counts[risk_label] += 1

            created_at = ai_report.created_at or now
            month_key = month_abbr[created_at.month]
            monthly_predictions[month_key] = monthly_predictions.get(month_key, 0) + 1
            monthly_generated[month_key] = monthly_generated.get(month_key, 0) + 1

        for report in medical_report_query.all():
            uploaded_at = report.uploaded_at or now
            month_key = month_abbr[uploaded_at.month]
            monthly_reports[month_key] = monthly_reports.get(month_key, 0) + 1
            monthly_generated[month_key] = monthly_generated.get(month_key, 0) + 1

    prediction_distribution = [
        PieSliceSchema(name=name, value=count)
        for name, count in disease_counts.items()
        if count > 0
    ]
    if not prediction_distribution:
        prediction_distribution = [
            PieSliceSchema(name=name, value=0) for name in DISEASE_MODELS[:4]
        ]

    risk_distribution = [
        BarSliceSchema(category=category, value=count)
        for category, count in risk_counts.items()
        if count > 0
    ]
    if not risk_distribution:
        risk_distribution = [BarSliceSchema(category=category, value=0) for category in risk_counts]

    month_labels: list[str] = []
    cursor = _month_shift(current_month_start, -7)
    while cursor <= current_month_start:
        month_labels.append(month_abbr[cursor.month])
        cursor = _month_shift(cursor, 1)

    monthly_trends = [
        LinePointSchema(
            month=label,
            predictions=monthly_predictions.get(label, 0),
            reports=monthly_reports.get(label, 0),
        )
        for label in month_labels
    ]
    reports_area = [
        AreaDataSchema(month=label, generated=monthly_generated.get(label, 0))
        for label in month_labels
    ]

    activity: list[ActivityEventSchema] = []
    event_id = 1
    if patient_ids:
        for patient in (
            db.query(Patient)
            .filter(Patient.doctor_id == doctor_id)
            .order_by(Patient.created_at.desc())
            .limit(3)
            .all()
        ):
            activity.append(
                ActivityEventSchema(
                    id=event_id,
                    title="Patient registered",
                    description=f"{patient.first_name} {patient.last_name} was added to the registry.",
                    time=_relative_time(patient.created_at),
                )
            )
            event_id += 1

        for ai_report, patient in (
            db.query(AIReport, Patient)
            .join(Patient, Patient.id == AIReport.patient_id)
            .filter(AIReport.patient_id.in_(patient_ids))
            .order_by(AIReport.created_at.desc())
            .limit(3)
            .all()
        ):
            activity.append(
                ActivityEventSchema(
                    id=event_id,
                    title="Prediction completed",
                    description=(
                        f"{_extract_disease(ai_report.risk_assessment)} analysis finished for "
                        f"{patient.first_name} {patient.last_name}."
                    ),
                    time=_relative_time(ai_report.created_at),
                )
            )
            event_id += 1

        for report in (
            db.query(MedicalReport)
            .filter(MedicalReport.patient_id.in_(patient_ids))
            .order_by(MedicalReport.uploaded_at.desc())
            .limit(2)
            .all()
        ):
            activity.append(
                ActivityEventSchema(
                    id=event_id,
                    title="Report uploaded",
                    description=f"{report.file_name} was uploaded for processing.",
                    time=_relative_time(report.uploaded_at),
                )
            )
            event_id += 1

        for assessment in (
            db.query(DrugSafetyAssessment)
            .filter(DrugSafetyAssessment.patient_id.in_(patient_ids))
            .order_by(DrugSafetyAssessment.created_at.desc())
            .limit(2)
            .all()
        ):
            activity.append(
                ActivityEventSchema(
                    id=event_id,
                    title="Drug interaction checked",
                    description="Medication review completed for a care plan.",
                    time=_relative_time(assessment.created_at),
                )
            )
            event_id += 1

    activity = activity[:8]

    pending_reports = 0
    if patient_ids:
        pending_reports = medical_report_query.filter(MedicalReport.extracted_text.is_(None)).count()

    summary = DashboardSummarySchema(
        pending_reports=pending_reports,
        high_risk_patients=high_risk_total,
        text=(
            f"You have {pending_reports} pending report{'s' if pending_reports != 1 else ''} "
            f"and {high_risk_total} high-risk patient{'s' if high_risk_total != 1 else ''}."
        ),
    )

    system_status = _build_system_status(db)

    return DashboardDataSchema(
        stats=stats,
        recent_patients=recent_patients,
        recent_reports=recent_reports,
        recent_predictions=recent_predictions,
        system_status=system_status,
        activity=activity,
        prediction_distribution=prediction_distribution,
        monthly_trends=monthly_trends,
        risk_distribution=risk_distribution,
        reports_area=reports_area,
        summary=summary,
    )


def _build_system_status(db: Session) -> list[SystemStatusSchema]:
    services = {
        "supervisor": app_state.supervisor is not None,
        "ml_model": app_state.ml_model is not None,
        "vector_store": app_state.vector_store is not None,
        "ocr": app_state.ocr_engine is not None,
    }

    db_status = "Online"
    db_description = "Primary instance is healthy."
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "Offline"
        db_description = f"Database check failed: {exc}"

    return [
        SystemStatusSchema(
            service="Backend API",
            status="Online",
            description=f"{settings.APP_NAME} v{settings.APP_VERSION} is responding normally.",
        ),
        SystemStatusSchema(
            service="Database",
            status=db_status,
            description=db_description,
        ),
        SystemStatusSchema(
            service="OCR Service",
            status="Online" if services["ocr"] else "Degraded",
            description=(
                "OCR engine is ready."
                if services["ocr"]
                else "OCR runs on-demand; dedicated engine not preloaded."
            ),
        ),
        SystemStatusSchema(
            service="AI Models Loaded",
            status="Online" if services["ml_model"] else "Degraded",
            description=(
                "Prediction models are available."
                if services["ml_model"]
                else "Some models may load lazily on first request."
            ),
        ),
        SystemStatusSchema(
            service="Knowledge Base",
            status="Online" if services["vector_store"] else "Degraded",
            description=(
                "Search index is synchronized."
                if services["vector_store"]
                else "Vector store is unavailable or still initializing."
            ),
        ),
        SystemStatusSchema(
            service="Authentication",
            status="Online",
            description="Session validation is healthy.",
        ),
    ]
