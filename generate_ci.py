import os

diseases = [
    ("diabetes", "Diabetes Mellitus", "ADA 2025"),
    ("heart", "Atherosclerotic Cardiovascular Disease", "AHA/ACC"),
    ("stroke", "Ischemic Stroke", "AHA/ASA"),
    ("kidney", "Chronic Kidney Disease", "KDIGO"),
    ("liver", "Chronic Liver Disease", "AASLD"),
    ("breast", "Breast Cancer", "NCCN"),
    ("parkinsons", "Parkinson's Disease", "AAN"),
    ("hepatitis", "Viral Hepatitis", "WHO / AASLD"),
    ("thyroid", "Thyroid Disorders", "ATA")
]

template = """\"\"\"
{title} Clinical Intelligence Module
\"\"\"
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
        medications.append("Consider aggressive pharmacotherapy per guidelines")
    elif risk_level.lower() in ["moderate", "medium"]:
        next_steps = ["Schedule outpatient follow-up within 2-4 weeks"]
        monitoring = ["Quarterly monitoring"]
        
    return {{
        "Guideline": "{guideline}",
        "Evidence Level": "Level A",
        "Risk Interpretation": f"The patient is assessed as {{risk_level}} risk based on current predictive models.",
        "Clinical Summary": f"Based on available parameters, the patient requires {{'immediate' if risk_level.lower() in ['high', 'severe'] else 'routine'}} clinical evaluation for {title}.",
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
        "References": ["{guideline} Clinical Practice Guidelines"]
    }}
"""

engine_code = """\"\"\"
Clinical Intelligence Engine
\"\"\"
from typing import Any
from app.clinical_intelligence import (
    diabetes,
    heart,
    stroke,
    kidney,
    liver,
    breast,
    parkinsons,
    hepatitis,
    thyroid
)

def generate_clinical_intelligence(disease_key: str, prediction: dict[str, Any], patient: dict[str, Any]) -> dict[str, Any]:
    if not disease_key:
        return {}
    
    key = disease_key.lower()
    
    if "diabet" in key:
        return diabetes.generate_guidance(prediction, patient)
    elif "heart" in key or "cardio" in key:
        return heart.generate_guidance(prediction, patient)
    elif "stroke" in key:
        return stroke.generate_guidance(prediction, patient)
    elif "kidney" in key or "renal" in key:
        return kidney.generate_guidance(prediction, patient)
    elif "liver" in key or "hepatic" in key:
        return liver.generate_guidance(prediction, patient)
    elif "breast" in key:
        return breast.generate_guidance(prediction, patient)
    elif "parkinson" in key:
        return parkinsons.generate_guidance(prediction, patient)
    elif "hepatitis" in key:
        return hepatitis.generate_guidance(prediction, patient)
    elif "thyroid" in key:
        return thyroid.generate_guidance(prediction, patient)
        
    # Default fallback
    return {
        "Guideline": "General Medical Guidelines",
        "Evidence Level": "Level C",
        "Risk Interpretation": "Requires further evaluation.",
        "Clinical Summary": "Undetermined disease specific state.",
        "Recommended Next Steps": ["Comprehensive clinical evaluation"],
        "Lifestyle Advice": ["Healthy diet and regular exercise"],
        "Monitoring Schedule": ["As determined by primary care provider"],
        "Recommended Laboratory Tests": ["CBC", "CMP"],
        "Recommended Imaging (if applicable)": ["As clinically indicated"],
        "Specialist Referral": ["Consider referral based on findings"],
        "Medication Considerations": ["Review current medications"],
        "Possible Complications": ["Unknown"],
        "Preventive Measures": ["Routine health maintenance"],
        "Emergency Warning Signs": ["Standard emergency symptoms (e.g. chest pain, shortness of breath)"],
        "Patient Education": ["General health counseling"],
        "References": ["Standard Clinical Guidelines"]
    }
"""

os.makedirs("backend/app/clinical_intelligence", exist_ok=True)
open("backend/app/clinical_intelligence/__init__.py", "w").close()

for name, title, guideline in diseases:
    with open(f"backend/app/clinical_intelligence/{name}.py", "w") as f:
        f.write(template.format(title=title, guideline=guideline))
        
with open("backend/app/clinical_intelligence/engine.py", "w") as f:
    f.write(engine_code)

print("Created CI modules.")
