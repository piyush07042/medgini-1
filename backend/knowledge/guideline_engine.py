import logging
from typing import Any, Dict, List
from knowledge.guideline_loader import load_guidelines

logger = logging.getLogger(__name__)

def match_guidelines(disease_key: str, prediction: Dict[str, Any], patient_data: Dict[str, Any], lab_values: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Matches prediction result, patient metrics, and lab values against structured clinical guidelines.
    Returns list of matched guideline entries with matching metadata.
    """
    guidelines = load_guidelines(disease_key)
    if not guidelines:
        return []

    matched = []
    # Extract prediction probability and risk label
    prob = prediction.get("probability") or prediction.get("confidence") or 0.0
    risk_label = str(prediction.get("confidence_label") or prediction.get("risk_level") or "").lower()

    # Simple matching algorithm based on risk level and key criteria thresholds
    for entry in guidelines:
        entry_risk = str(entry.get("risk_level", "")).lower()
        
        # Risk level match
        risk_match = False
        if entry_risk == risk_label:
            risk_match = True
        elif risk_label in ["high", "critical", "severe"] and entry_risk == "high":
            risk_match = True
        elif risk_label in ["moderate", "medium"] and entry_risk == "moderate":
            risk_match = True
        elif risk_label in ["low", "none"] and entry_risk == "low":
            risk_match = True

        # Let's check numerical criteria thresholds if any are specified
        criteria = entry.get("criteria", {})
        criteria_match = True
        
        for criterion_key, threshold_str in criteria.items():
            # Extract numeric value from patient data or labs
            patient_val = patient_data.get(criterion_key) or lab_values.get(criterion_key)
            if patient_val is not None:
                try:
                    # Parse value
                    p_val = float(str(patient_val).replace("%", "").strip())
                    # Parse threshold: e.g. ">= 6.5%", "< 60"
                    clean_thresh = threshold_str.replace("%", "").strip()
                    if clean_thresh.startswith(">="):
                        val_limit = float(clean_thresh.replace(">=", "").strip())
                        if not (p_val >= val_limit):
                            criteria_match = False
                    elif clean_thresh.startswith("<="):
                        val_limit = float(clean_thresh.replace("<=", "").strip())
                        if not (p_val <= val_limit):
                            criteria_match = False
                    elif clean_thresh.startswith(">"):
                        val_limit = float(clean_thresh.replace(">", "").strip())
                        if not (p_val > val_limit):
                            criteria_match = False
                    elif clean_thresh.startswith("<"):
                        val_limit = float(clean_thresh.replace("<", "").strip())
                        if not (p_val < val_limit):
                            criteria_match = False
                except Exception as e:
                    logger.debug(f"Criterion matching error: {e}")

        # Matches if risk matches or criteria match
        if risk_match or (criteria and criteria_match):
            matched.append(entry)

    # Fallback to the first entry if nothing matched to ensure we always return guidelines
    if not matched and guidelines:
        matched.append(guidelines[0])

    return matched
