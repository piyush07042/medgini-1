from typing import Dict, Any

def consolidate_clinical_context(
    patient_context: Dict[str, Any],
    ml_risk_data: Dict[str, Any],
    drug_safety_data: Dict[str, Any],
    rag_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phase 12: Aggregates findings from Risk Assessment (Phase 9), 
    RAG Guidelines (Phase 10), and Drug Safety (Phase 11) into a 
    single unified Clinical Decision Support context.
    """
    
    # Extract Risk Category
    risk_info = ml_risk_data.get("disease_risk_assessment", {})
    risk_score = risk_info.get("estimated_risk_score_percent", 0.0)
    risk_category = risk_info.get("risk_category", "Low")
    
    # Extract Drug Safety Flags
    safety_info = drug_safety_data.get("drug_safety_assessment", {})
    safety_status = safety_info.get("status", "PASS")
    allergy_conflicts = safety_info.get("allergies", []) or safety_info.get("allergy_conflicts", [])
    interaction_warnings = safety_info.get("interactions", []) or safety_info.get("interaction_warnings", [])

    # Synthesize High-Priority Clinical Directives
    priority_directives = []
    
    if safety_status == "FLAGGED":
        priority_directives.append(
            f"CRITICAL: Resolved {len(allergy_conflicts)} allergy conflicts and {len(interaction_warnings)} drug interactions before prescribing."
        )
        
    if risk_category == "High":
        priority_directives.append(
            f"URGENT: Patient evaluated with {risk_score}% elevated metabolic/cardiovascular risk profile."
        )

    return {
        "unified_cdss_summary": {
            "patient_name": patient_context.get("name", "Unknown"),
            "overall_urgency": "High" if (risk_category == "High" or safety_status == "FLAGGED") else "Routine",
            "priority_directives": priority_directives,
            "integrated_findings": {
                "risk_profile": risk_info,
                "drug_safety": safety_info,
                "rag_guidelines": rag_data
            }
        }
    }