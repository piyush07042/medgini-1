import logging
from typing import Any, Dict, List
from knowledge.guideline_engine import match_guidelines
from knowledge.recommendation_engine import build_guideline_recommendations
from knowledge.citation_engine import build_citations

logger = logging.getLogger(__name__)

def get_clinical_recommendations(disease_key: str, prediction: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Facade function that combines matching, recommendation building, and citation formatting.
    """
    # Extract lab values from patient data for criteria checking
    lab_keys = ["hba1c", "glucose", "egfr", "uacr", "blood_pressure", "ldl_cholesterol"]
    lab_values = {k: patient_data.get(k) for k in lab_keys if patient_data.get(k) is not None}

    try:
        matched = match_guidelines(disease_key, prediction, patient_data, lab_values)
        if not matched:
            return {}

        recommendations = build_guideline_recommendations(matched, patient_data)
        citations = build_citations(matched)

        # Collect follow-up actions
        follow_up_steps = []
        for entry in matched:
            for step in entry.get("follow_up", []):
                follow_up_steps.append({
                    "timeline": step.get("timeline", "General"),
                    "action": step.get("action", "")
                })

        # Collect contraindications
        contraindications = []
        for entry in matched:
            for contra in entry.get("contraindications", []):
                contraindications.append({
                    "drug": contra.get("drug", ""),
                    "condition": contra.get("condition", ""),
                    "action": contra.get("action", "")
                })

        # Collect emergency signs
        emergency_signs = []
        for entry in matched:
            for sign in entry.get("emergency_signs", []):
                emergency_signs.append(sign)

        # Choose the first guideline match details as primary metadata
        primary = matched[0]

        return {
            "Guideline": primary.get("source", "Standard Guidelines"),
            "Evidence Level": primary.get("evidence_level", "Level A"),
            "Risk Interpretation": f"Matched risk profile: {primary.get('risk_level', 'Medium')}.",
            "Clinical Summary": f"Adhere to recommendations per {primary.get('source')}.",
            "Recommended Next Steps": [r["recommendation"] for r in recommendations],
            "Lifestyle Advice": [r for r in primary.get("recommendations", []) if "lifestyle" in r.lower() or "diet" in r.lower() or "activity" in r.lower()],
            "Monitoring Schedule": [f"{s['timeline']}: {s['action']}" for s in follow_up_steps],
            "Recommended Laboratory Tests": [f"Follow-up: {s['action']}" for s in follow_up_steps if "urine" in s["action"].lower() or "hba1c" in s["action"].lower() or "lipid" in s["action"].lower()],
            "References": primary.get("references", []),
            "guideline_citations": citations,
            "follow_up_plan": follow_up_steps,
            "contraindications": contraindications,
            "emergency_signs": emergency_signs,
            "matched_guideline_count": len(matched)
        }
    except Exception as e:
        logger.exception(f"Error getting clinical recommendations: {e}")
        return {}
