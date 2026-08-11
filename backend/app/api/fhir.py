"""
FHIR Export API
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import Patient, User
from app.schemas.common import ApiResponse
from app.services.fhir_service import FHIRService

router = APIRouter(
    prefix="/fhir",
    tags=["FHIR"],
)


@router.get(
    "/patient/{patient_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def export_patient_fhir(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export a patient record as a FHIR Bundle.
    """

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.doctor_id == current_user.id,
        )
        .first()
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    bundle = FHIRService().build_patient_bundle(
        patient=patient,
    )

    return ApiResponse(
        message="FHIR bundle generated successfully.",
        data=bundle,
    )