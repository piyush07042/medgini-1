"""
Medical Report Upload API
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.agents.base.agent_state import AgentState
from app.agents.supervisor.supervisor import Supervisor
from app.core.deps import get_supervisor
from app.core.file_validation import validate_upload
from app.schemas.common import ApiResponse
from app.core.rag import ingest_documents
from app.core.config import settings
from app.core.deps import get_db
from app.services.report.report_service import get_patient_id_from_context, save_ai_report

logger = logging.getLogger(__name__)


def normalize_workflow_state(state: AgentState, file_name: str) -> dict:
    """Convert workflow state into a preview-friendly payload for the UI."""
    metadata = dict(getattr(state, "metadata", {}) or {})
    metadata.setdefault("file_name", file_name)
    metadata.setdefault("workflow_status", metadata.get("workflow_status") or "completed")

    report_text = getattr(state, "report_text", "") or ""
    if not report_text.strip():
        report_text = "No OCR text was extracted from the uploaded file."

    warnings = list(getattr(state, "warnings", []) or [])
    if not warnings and metadata.get("workflow_status") != "completed":
        warnings.append("The workflow completed with non-standard status.")

    extracted_metrics = getattr(state, "extracted_metrics", {}) or {}
    if not extracted_metrics:
        ocr_res = getattr(state, "ocr_result", None)
        if isinstance(ocr_res, list) and ocr_res and isinstance(ocr_res[0], dict):
            extracted_metrics = ocr_res[0].get("metrics") or {}
        elif isinstance(ocr_res, dict):
            extracted_metrics = ocr_res.get("metrics") or {}

    disease_risk = getattr(state, "disease_risk", {}) or {}
    if not disease_risk or not any(k in disease_risk for k in ("prediction", "risk_category", "risk_level", "probability", "condition", "disease")):
        recs = getattr(state, "recommendations", []) or []
        if recs and isinstance(recs[0], dict):
            disease_risk = recs[0].get("risk_summary") or recs[0].get("risk_analysis") or disease_risk
        if not disease_risk and isinstance(getattr(state, "agent_outputs", None), dict):
            disease_risk = state.agent_outputs.get("DiseaseRiskAgent") or {}

    patient = getattr(state, "patient", {}) or {}
    if not patient or not any(k in patient for k in ("patient_id", "id", "age", "gender", "sex", "first_name", "last_name", "name")):
        patient_summary = getattr(state, "patient_summary", {}) or {}
        if isinstance(patient_summary, dict) and patient_summary:
            patient = {**patient_summary, **patient}
        elif extracted_metrics:
            metrics_patient = {k: v for k, v in extracted_metrics.items() if k in {"patient_id", "id", "age", "sex", "gender", "bmi", "glucose", "cholesterol", "systolic_bp", "diastolic_bp"}}
            if metrics_patient:
                patient = {**metrics_patient, **patient}

    processing_notes = []
    if warnings:
        processing_notes.extend(warnings)
    if not getattr(state, "ocr_result", None):
        processing_notes.append("No structured OCR output was produced for this upload.")
    if not extracted_metrics:
        processing_notes.append("No extracted metrics were available for preview.")

    metadata["processing_notes"] = processing_notes

    normalized = {
        "patient": patient,
        "patient_summary": getattr(state, "patient_summary", None) or {},
        "patient_history": getattr(state, "patient_history", {}) or {},
        "symptoms": list(getattr(state, "symptoms", []) or []),
        "medications": list(getattr(state, "medications", []) or []),
        "allergies": list(getattr(state, "allergies", []) or []),
        "uploaded_reports": list(getattr(state, "uploaded_reports", []) or []),
        "report_text": report_text,
        "ocr_result": getattr(state, "ocr_result", {}) or {},
        "extracted_metrics": extracted_metrics,
        "disease_risk": disease_risk,
        "knowledge_results": list(getattr(state, "knowledge_results", []) or []),
        "drug_analysis": getattr(state, "drug_analysis", {}) or {},
        "recommendations": list(getattr(state, "recommendations", []) or []),
        "final_report": getattr(state, "final_report", {}) or {},
        "metadata": metadata,
        "warnings": warnings,
        "errors": list(getattr(state, "errors", []) or []),
    }
    return normalized


router = APIRouter(
    prefix="/upload",
    tags=["Medical Report Upload"],
)

UPLOAD_DIRECTORY = Path(settings.UPLOAD_DIRECTORY)
UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post(
    "/report",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_report(
    file: UploadFile = File(...),
    patient_context_json: Optional[str] = Form("{}"),
    supervisor: Supervisor = Depends(get_supervisor),
    db: Session = Depends(get_db),
):
    """
    Upload a medical report and execute the Supervisor workflow.
    """

    await validate_upload(file)

    destination = UPLOAD_DIRECTORY / file.filename

    try:

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            patient_context = json.loads(
                patient_context_json
            )
        except json.JSONDecodeError:
            patient_context = {}

        state = AgentState()

        state.patient = patient_context
        state.uploaded_reports = [str(destination)]
        state.report_text = str(destination)
        state.raw_report_text = str(destination)

        final_state, results, metrics = await supervisor.run(
            state
        )

        patient_id = get_patient_id_from_context(state.patient)
        if patient_id is not None:
            logger.info("Saving report...")
            logger.info("Patient ID: %s", patient_id)
            save_ai_report(db, patient_id, final_state)
        else:
            logger.info("Skipping report persistence: no patient_id found in uploaded report context.")

        # Optional: index the extracted report text into the knowledge store.
        try:
            text = ""
            if state.report_text and isinstance(state.report_text, str):
                report_path = Path(state.report_text)
                if report_path.exists() and report_path.is_file():
                    if report_path.suffix.lower() == ".txt":
                        text = report_path.read_text(encoding="utf-8")
                    else:
                        from app.services.ocr.ocr_service import extract_text as ocr_extract_text

                        text = ocr_extract_text(str(report_path))
                else:
                    text = state.report_text

            if text and text.strip():
                ingest_documents([text], metadatas=[{"source": "uploaded_report"}])
        except Exception:
            # non-fatal
            pass

        workflow_state = normalize_workflow_state(final_state, file.filename)

        return ApiResponse(
            message="Medical report processed successfully.",
            data={
                "workflow_state": workflow_state,
                "agent_results": [result.to_dict() for result in results],
                "workflow_metrics": metrics.to_dict(),
            },
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report processing failed: {exc}",
        )

    finally:

        if destination.exists():
            destination.unlink()