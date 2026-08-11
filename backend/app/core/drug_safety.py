from typing import List, Dict, Any

from app.services.drug_safety_service import get_drug_safety_service


# Compatibility wrapper for legacy core use.

def analyze_drug_safety(
    medications: List[str],
    patient_allergies: List[str],
    patient_context: dict[str, Any] | None = None,
) -> Dict[str, Any]:
    service = get_drug_safety_service()
    return service.analyze(
        medications=medications,
        patient_allergies=patient_allergies,
        patient_context=patient_context,
    )
