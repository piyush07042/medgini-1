"""
Dashboard API endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import AIReport, Patient, User
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardDataSchema
from app.services.dashboard_service import build_dashboard

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


class PredictionSaveSchema(BaseModel):
    patient_id: int
    risk_assessment: dict[str, Any]
    rag_evidence: list[dict[str, Any]] = []
    drug_safety_alerts: dict[str, Any] = {}
    clinical_summary: str = ""
    clinical_intelligence: dict[str, Any] = {}


def _build_dashboard_data(current_user: User, db: Session) -> dict[str, Any]:
    dashboard = build_dashboard(db, current_user.id)
    return DashboardDataSchema.model_validate(dashboard).model_dump()


@router.get(
    "",
    response_model=ApiResponse,
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return aggregated dashboard data for the authenticated clinician.
    """
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Dashboard data retrieved successfully.",
        data=dashboard,
    )


@router.get("/overview", response_model=ApiResponse)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Dashboard overview retrieved successfully.",
        data={
            "summary": dashboard["summary"],
            "stats": dashboard["stats"],
        },
    )


@router.get("/prediction-distribution", response_model=ApiResponse)
def get_prediction_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Prediction distribution retrieved successfully.",
        data=dashboard["prediction_distribution"],
    )


@router.get("/monthly-predictions", response_model=ApiResponse)
def get_monthly_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Monthly predictions retrieved successfully.",
        data=dashboard["monthly_trends"],
    )


@router.get("/risk-distribution", response_model=ApiResponse)
def get_risk_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Risk distribution retrieved successfully.",
        data=dashboard["risk_distribution"],
    )


@router.get("/reports-summary", response_model=ApiResponse)
def get_reports_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard = _build_dashboard_data(current_user, db)
    return ApiResponse(
        message="Reports summary retrieved successfully.",
        data=dashboard["reports_area"],
    )


@router.post("/prediction", response_model=ApiResponse)
def save_dashboard_prediction(
    payload: PredictionSaveSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == payload.patient_id, Patient.doctor_id == current_user.id)
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    ai_report = AIReport(
        patient_id=patient.id,
        risk_assessment=payload.risk_assessment,
        rag_evidence=payload.rag_evidence,
        drug_safety_alerts=payload.drug_safety_alerts,
        clinical_summary=payload.clinical_summary or "",
        clinical_intelligence=payload.clinical_intelligence or {},
    )
    db.add(ai_report)
    db.commit()
    db.refresh(ai_report)

    return ApiResponse(
        message="Prediction saved successfully.",
        data={"id": ai_report.id},
    )
