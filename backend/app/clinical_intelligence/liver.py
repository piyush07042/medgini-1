"""
Chronic Liver Disease Clinical Intelligence Module
"""
from typing import Any

def generate_guidance(prediction: dict[str, Any], patient: dict[str, Any]) -> dict[str, Any]:
    risk_level = prediction.get("risk_category") or prediction.get("risk_level") or "Unknown"
    confidence = prediction.get("confidence") or prediction.get("probability") or 0.0
    
    # Base recommendations
    next_steps = ["Evaluate current metabolic status"]
    lifestyle = ["Maintain a balanced diet", "Regular exercise"]
    monitoring = ["Annual checkup"]
    lab_tests = ["Basic Metabolic Panel"]
    medications = ["Review current medication list"]
    
    # Tailor based on risk
    if risk_level.lower() in ["high", "critical", "severe"]:
        next_steps = ["Immediate specialist consultation required", "Urgent diagnostic workup"]
        monitoring = ["Monthly follow-up until stable"]
        lab_tests.append("Comprehensive disease-specific panel")
        medications.append("Urgent clinical evaluation is recommended. Further management should be determined by a qualified clinician according to applicable clinical guidelines (EASL).")
    elif risk_level.lower() in ["moderate", "medium"]:
        next_steps = ["Schedule outpatient follow-up within 2-4 weeks"]
        monitoring = ["Quarterly monitoring"]
        
    return {
        "Guideline": "AASLD",
        "Evidence Level": "Level A",
        "Risk Interpretation": f"The patient is assessed as {risk_level} risk based on current predictive models.",
        "Clinical Summary": f"Based on available parameters, the patient requires {'immediate' if risk_level.lower() in ['high', 'severe'] else 'routine'} clinical evaluation for Chronic Liver Disease.",
        "Recommended Next Steps": next_steps,
        "Lifestyle Advice": lifestyle,
        "Monitoring Schedule": monitoring,
        "Recommended Laboratory Tests": lab_tests,
        "Recommended Imaging (if applicable)": ["Ultrasound or CT as clinically indicated"],
        "Specialist Referral": ["Refer to specialist if symptoms worsen or risk remains high"],
        "Medication Considerations": medications,
        "Possible Complications": ["Disease progression", "Secondary organ damage"],
        "Preventive Measures": ["Adherence to prescribed therapy", "Risk factor modification"],
        "Emergency Warning Signs": ["Severe acute symptoms", "Sudden clinical deterioration"],
        "Patient Education": ["Educate patient on disease signs and lifestyle modifications"],
        "References": ["AASLD Clinical Practice Guidelines"]
    }
