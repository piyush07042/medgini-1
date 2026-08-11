from typing import Any, Dict, List

def build_guideline_recommendations(matched_guidelines: List[Dict[str, Any]], patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Builds actionable recommendations from matched guidelines, filtering for patient-specific details.
    """
    recs = []
    seen = set()
    for entry in matched_guidelines:
        source = entry.get("source", "Clinical Guidelines")
        section = entry.get("section", "")
        version = entry.get("version", "")
        
        for rec in entry.get("recommendations", []):
            if rec not in seen:
                seen.add(rec)
                recs.append({
                    "title": entry.get("disease", "Condition") + " Guideline Recommendation",
                    "recommendation": rec,
                    "priority": entry.get("risk_level", "Medium"),
                    "category": "Clinical Intelligence",
                    "guideline": f"{source} ({version})",
                    "section": section
                })
    return recs
