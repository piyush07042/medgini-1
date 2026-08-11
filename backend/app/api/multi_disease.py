import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.multi_disease_engine import build_unified_patient_summary
from app.models.models import AIReport, Patient
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multi-disease", tags=["Multi-Disease Intelligence"])

@router.post("/analyze", response_model=ApiResponse)
async def analyze_multi_disease_risk(payload: Dict[str, Any]):
    """
    Evaluates multi-organ risk profile, health score (0-100), disease interactions,
    and comorbidity clusters for a patient payload.
    """
    try:
        patient_data = payload.get("patient", {})
        predictions_map = payload.get("predictions", {})
        history = payload.get("history", [])

        summary = build_unified_patient_summary(patient_data, predictions_map, history)
        return ApiResponse(
            message="Multi-disease intelligence analysis completed.",
            data=summary
        )
    except Exception as e:
        logger.exception("Multi-disease analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-disease analysis failed: {e}"
        )

@router.get("/patient/{patient_id}/longitudinal", response_model=ApiResponse)
async def get_patient_longitudinal_intelligence(patient_id: int, db: Session = Depends(get_db)):
    """
    Fetches longitudinal patient history, historical prediction trend, health score,
    and multi-disease trajectory from the database.
    """
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient_data = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "age": patient.age,
            "gender": patient.gender,
            "medical_history": patient.medical_history
        }

        # Fetch all historical AI reports for this patient
        ai_reports = db.query(AIReport).filter(AIReport.patient_id == patient_id).order_by(AIReport.created_at.asc()).all()
        
        predictions_map = {}
        history = []

        for r in ai_reports:
            risk = r.risk_assessment if isinstance(r.risk_assessment, dict) else {}
            disease = risk.get("disease") or risk.get("condition") or "Clinical Analysis"
            prob = float(risk.get("probability") or risk.get("confidence") or 0.0)
            predictions_map[disease.lower().replace(" ", "_")] = risk

            history.append({
                "disease": disease.title(),
                "probability": prob,
                "confidenceLabel": risk.get("confidence_label") or risk.get("risk_category") or "Moderate",
                "createdAt": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                "summary": f"{disease} evaluated with risk score {round(prob * 100, 1)}%"
            })

        summary = build_unified_patient_summary(patient_data, predictions_map, history)

        return ApiResponse(
            message="Patient longitudinal intelligence retrieved.",
            data={
                "patient": patient_data,
                "intelligence": summary,
                "total_historical_evaluations": len(ai_reports)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get patient longitudinal intelligence")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch longitudinal intelligence: {e}"
        )
