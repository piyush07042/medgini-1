"""
Patient Management API
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.file_validation import validate_image_upload
from app.db.session import get_db
from app.models.models import AIReport, DrugSafetyAssessment, MedicalReport, Patient, User
from app.schemas.common import ApiResponse
from app.schemas.schemas import (
    MedicalHistoryEntryCreate,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import (
    append_medical_history_entry,
    build_medical_timeline,
    build_visit_history,
    list_patients_paginated,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

AVATAR_DIRECTORY = Path(settings.UPLOAD_DIRECTORY) / "avatars"
AVATAR_DIRECTORY.mkdir(parents=True, exist_ok=True)


def _avatar_file_path(avatar_url: str) -> Path:
    relative = avatar_url.removeprefix("/uploads/").lstrip("/")
    return Path(settings.UPLOAD_DIRECTORY) / relative


def _get_owned_patient(db: Session, doctor_id: int, patient_id: int) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == doctor_id)
        .first()
    )
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )
    return patient


@router.post(
    "/",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(
    patient_in: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = Patient(
        doctor_id=current_user.id,
        **patient_in.model_dump(),
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return ApiResponse(
        message="Patient created successfully.",
        data=PatientResponse.model_validate(patient),
    )


@router.get(
    "/",
    response_model=ApiResponse,
)
def list_patients(
    search: str = Query("", description="Search by patient name"),
    gender: str = Query("all", description="Filter by gender"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_dir: str = Query("desc", description="Sort direction"),
    page: int = Query(1, ge=1),
    page_size: int = Query(8, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = list_patients_paginated(
        db,
        current_user.id,
        search=search,
        gender=gender,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )

    return ApiResponse(
        message="Patients retrieved successfully.",
        data=[item.model_dump() for item in payload.items],
    )


@router.get(
    "/{patient_id}",
    response_model=ApiResponse,
)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    return ApiResponse(
        message="Patient retrieved successfully.",
        data=PatientResponse.model_validate(patient),
    )


@router.put(
    "/{patient_id}",
    response_model=ApiResponse,
)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    updates = patient_in.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return ApiResponse(
        message="Patient updated successfully.",
        data=PatientResponse.model_validate(patient),
    )


@router.delete(
    "/{patient_id}",
    response_model=ApiResponse,
)
def delete_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)

    if patient.avatar_url:
        avatar_path = _avatar_file_path(patient.avatar_url)
        if avatar_path.exists():
            avatar_path.unlink()

    db.query(AIReport).filter(AIReport.patient_id == patient_id).delete(synchronize_session=False)
    db.query(MedicalReport).filter(MedicalReport.patient_id == patient_id).delete(synchronize_session=False)
    db.query(DrugSafetyAssessment).filter(DrugSafetyAssessment.patient_id == patient_id).delete(
        synchronize_session=False
    )
    db.delete(patient)
    db.commit()

    return ApiResponse(
        message="Patient deleted successfully.",
        data=None,
    )


@router.post(
    "/{patient_id}/avatar",
    response_model=ApiResponse,
)
async def upload_patient_avatar(
    patient_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    filename = await validate_image_upload(file)
    extension = Path(filename).suffix.lower()
    stored_name = f"patient_{patient_id}_{uuid.uuid4().hex}{extension}"
    destination = AVATAR_DIRECTORY / stored_name

    if patient.avatar_url:
        old_path = _avatar_file_path(patient.avatar_url)
        if old_path.exists():
            old_path.unlink()

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    patient.avatar_url = f"/uploads/avatars/{stored_name}"
    db.commit()
    db.refresh(patient)

    return ApiResponse(
        message="Patient avatar uploaded successfully.",
        data=PatientResponse.model_validate(patient),
    )


@router.get(
    "/{patient_id}/timeline",
    response_model=ApiResponse,
)
def get_patient_timeline(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    timeline = build_medical_timeline(db, patient)
    return ApiResponse(
        message="Patient timeline retrieved successfully.",
        data=[event.model_dump() for event in timeline],
    )


@router.get(
    "/{patient_id}/visits",
    response_model=ApiResponse,
)
def get_patient_visits(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    visits = build_visit_history(db, patient)
    return ApiResponse(
        message="Patient visit history retrieved successfully.",
        data=[visit.model_dump() for visit in visits],
    )


@router.post(
    "/{patient_id}/history",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_medical_history_entry(
    patient_id: int,
    entry: MedicalHistoryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = _get_owned_patient(db, current_user.id, patient_id)
    new_entry = append_medical_history_entry(patient, entry)
    db.commit()
    db.refresh(patient)

    return ApiResponse(
        message="Medical history entry added successfully.",
        data={
            "entry": new_entry,
            "patient": PatientResponse.model_validate(patient).model_dump(),
        },
    )
