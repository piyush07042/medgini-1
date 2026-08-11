import pytest
from app.clinical_intelligence.hepatitis import generate_guidance

def test_hepatitis_generate_guidance_high_risk():
    prediction = {"risk_level": "high", "probability": 0.85}
    patient = {"age": 60, "gender": "male"}
    
    result = generate_guidance(prediction, patient)
    
    assert "Guideline" in result
    assert "Immediate specialist consultation required" in result["Recommended Next Steps"]
    assert "Monthly follow-up until stable" in result["Monitoring Schedule"]

def test_hepatitis_generate_guidance_low_risk():
    prediction = {"risk_level": "low", "probability": 0.15}
    patient = {"age": 40, "gender": "female"}
    
    result = generate_guidance(prediction, patient)
    
    assert "Guideline" in result
    assert "Evaluate current metabolic status" in result["Recommended Next Steps"]
    assert "Annual checkup" in result["Monitoring Schedule"]
