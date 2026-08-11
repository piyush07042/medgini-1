from __future__ import annotations

from typing import List

import logging

from fastapi import APIRouter, Body, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.drug_safety import analyze_drug_safety
from app.db.session import get_db
from app.models.models import DrugSafetyAssessment, Patient
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/drug-safety",
    tags=["Drug Safety"],
)


@router.post("/analyze", response_model=ApiResponse)
def analyze(medications: List[str] = Body(...), allergies: List[str] | None = Body(None)):
    """Analyze provided medications and allergies and return a safety assessment."""
    try:
        result = analyze_drug_safety(medications=medications, patient_allergies=allergies or [])
        return ApiResponse(
            message="Drug safety analysis completed successfully.",
            data=result,
        )
    except Exception as exc:
        logger.exception("Drug safety analyze failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/store", response_model=ApiResponse)
def store_assessment(
    patient_id: int | None = Body(None, description="Optional patient id to associate"),
    medications: List[str] = Body(...),
    allergies: List[str] | None = Body(None),
    db: Session = Depends(get_db),
):
    """Store a computed drug safety assessment in the database."""
    try:
        logger.info("Drug safety store starting: patient_id=%s medications=%s allergies=%s", patient_id, medications, allergies)
        assessment = analyze_drug_safety(medications=medications, patient_allergies=allergies or [])
        logger.info("Drug safety analysis completed before DB insert")

        db_obj = DrugSafetyAssessment(
            patient_id=patient_id,
            medications=medications,
            allergies=allergies or [],
            assessment=assessment,
        )
        logger.info("DrugSafetyAssessment instance created: %s", db_obj)

        db.add(db_obj)
        logger.info("Added DrugSafetyAssessment to session")

        db.commit()
        logger.info("Committed DrugSafetyAssessment to database")

        db.refresh(db_obj)
        logger.info("Refreshed DrugSafetyAssessment from database with id=%s", db_obj.id)

        return ApiResponse(
            message="Drug safety assessment stored successfully.",
            data={"id": db_obj.id, "status": db_obj.assessment},
        )
    except Exception:
        try:
            db.rollback()
            logger.info("Rolled back DB session after failure")
        except Exception:
            logger.exception("Failed to rollback DB session after drug safety store failure")
        logger.exception("Drug safety store failed")
        raise


@router.get("/patient/{patient_id}", response_model=ApiResponse)
def get_for_patient(patient_id: int, db: Session = Depends(get_db)):
    """Return the latest drug safety assessments for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    rows = (
        db.query(DrugSafetyAssessment)
        .filter(DrugSafetyAssessment.patient_id == patient_id)
        .order_by(DrugSafetyAssessment.created_at.desc())
        .limit(10)
        .all()
    )

    return ApiResponse(
        message="Drug safety assessments retrieved successfully.",
        data=[
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "assessment": r.assessment,
            }
            for r in rows
        ],
    )


@router.get("/assessment/{assessment_id}", response_model=ApiResponse)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Return a stored drug safety assessment by assessment id."""
    assessment = db.query(DrugSafetyAssessment).filter(DrugSafetyAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return ApiResponse(
        message="Drug safety assessment retrieved successfully.",
        data={
            "id": assessment.id,
            "patient_id": assessment.patient_id,
            "medications": assessment.medications,
            "allergies": assessment.allergies,
            "assessment": assessment.assessment,
            "created_at": assessment.created_at.isoformat(),
        },
    )
