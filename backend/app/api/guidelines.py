import logging
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from typing import Any, Dict, List

# Add backend directory to sys.path if not present to ensure knowledge module is importable
repo_root = str(Path(__file__).resolve().parents[2])
if repo_root not in sys.path:
    sys.path.append(repo_root)

from knowledge.guideline_loader import list_available_guidelines, load_guidelines
from knowledge.guideline_engine import match_guidelines
from knowledge.guideline_service import get_clinical_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guidelines", tags=["Clinical Guidelines"])

@router.get("/list", status_code=status.HTTP_200_OK)
async def list_guidelines():
    """
    Lists all loaded/available guidelines with their metadata.
    """
    try:
        return {
            "success": True,
            "guidelines": list_available_guidelines()
        }
    except Exception as e:
        logger.exception("Error listing guidelines")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list guidelines: {e}"
        )

@router.get("/{disease_key}", status_code=status.HTTP_200_OK)
async def get_guidelines_for_disease(disease_key: str):
    """
    Retrieves full structured guideline entry details for a disease.
    """
    try:
        entries = load_guidelines(disease_key)
        return {
            "success": True,
            "disease_key": disease_key,
            "guidelines": entries
        }
    except Exception as e:
        logger.exception(f"Error fetching guidelines for {disease_key}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve guidelines: {e}"
        )

@router.post("/{disease_key}/match", status_code=status.HTTP_200_OK)
async def match_guidelines_for_disease(disease_key: str, payload: Dict[str, Any]):
    """
    Matches a custom prediction/patient payload with guidelines.
    """
    try:
        prediction = payload.get("prediction", {})
        patient_data = payload.get("patient", {})
        lab_values = payload.get("lab_values", {})
        matched = match_guidelines(disease_key, prediction, patient_data, lab_values)
        recommendations = get_clinical_recommendations(disease_key, prediction, patient_data)
        return {
            "success": True,
            "matched_raw": matched,
            "structured_guidance": recommendations
        }
    except Exception as e:
        logger.exception(f"Error matching guidelines for {disease_key}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match guidelines: {e}"
        )
