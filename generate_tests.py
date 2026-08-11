import os

diseases = [
    ("diabetes", "Diabetes Mellitus"),
    ("heart", "Atherosclerotic Cardiovascular Disease"),
    ("stroke", "Ischemic Stroke"),
    ("kidney", "Chronic Kidney Disease"),
    ("liver", "Chronic Liver Disease"),
    ("breast", "Breast Cancer"),
    ("parkinsons", "Parkinson's Disease"),
    ("hepatitis", "Viral Hepatitis"),
    ("thyroid", "Thyroid Disorders")
]

test_template = """import pytest
from app.clinical_intelligence.{module} import generate_guidance

def test_{module}_generate_guidance_high_risk():
    prediction = {{"risk_level": "high", "probability": 0.85}}
    patient = {{"age": 60, "gender": "male"}}
    
    result = generate_guidance(prediction, patient)
    
    assert "Guideline" in result
    assert "Immediate specialist consultation required" in result["Recommended Next Steps"]
    assert "Monthly follow-up until stable" in result["Monitoring Schedule"]

def test_{module}_generate_guidance_low_risk():
    prediction = {{"risk_level": "low", "probability": 0.15}}
    patient = {{"age": 40, "gender": "female"}}
    
    result = generate_guidance(prediction, patient)
    
    assert "Guideline" in result
    assert "Evaluate current metabolic status" in result["Recommended Next Steps"]
    assert "Annual checkup" in result["Monitoring Schedule"]
"""

engine_test_template = """import pytest
from app.clinical_intelligence.engine import generate_clinical_intelligence

def test_engine_routes_to_diabetes():
    prediction = {"risk_level": "high"}
    patient = {}
    result = generate_clinical_intelligence("diabetes", prediction, patient)
    assert result["Guideline"] == "ADA 2025"

def test_engine_routes_to_heart():
    prediction = {"risk_level": "high"}
    patient = {}
    result = generate_clinical_intelligence("heart_disease", prediction, patient)
    assert result["Guideline"] == "AHA/ACC"

def test_engine_fallback():
    prediction = {"risk_level": "low"}
    patient = {}
    result = generate_clinical_intelligence("unknown_disease", prediction, patient)
    assert result["Guideline"] == "General Medical Guidelines"
"""

for module, title in diseases:
    with open(f"backend/tests/clinical_intelligence/test_{module}.py", "w") as f:
        f.write(test_template.format(module=module))

with open("backend/tests/clinical_intelligence/test_engine.py", "w") as f:
    f.write(engine_test_template)

print("Created CI unit tests.")
