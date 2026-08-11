import pytest
from app.core.multi_disease_engine import (
    calculate_combined_disease_risk,
    calculate_overall_health_score,
    detect_comorbidities,
    analyze_disease_interactions,
    build_unified_patient_summary
)

def test_combined_disease_risk():
    predictions_map = {
        "heart_disease": {"probability": 0.85},
        "diabetes": {"probability": 0.70},
        "kidney_disease": {"probability": 0.60}
    }
    patient = {"age": 55, "glucose": 145, "bmi": 32}
    result = calculate_combined_disease_risk(predictions_map, patient)
    
    assert result["combined_risk_percent"] > 50
    assert result["risk_category"] in ["High", "Critical"]
    assert "cardiovascular" in result["organ_scores"]

def test_overall_health_score():
    health = calculate_overall_health_score(combined_risk_percent=40.0, patient_age=50, lab_abnormalities_count=2)
    assert 0 <= health["health_score"] <= 100
    assert health["status"] in ["Optimal", "Fair", "Guarded", "Critical"]

def test_comorbidity_detection():
    patient = {"glucose": 150, "systolic_bp": 145, "bmi": 31, "egfr": 50}
    predictions = {
        "diabetes": {"probability": 0.8},
        "heart_disease": {"probability": 0.7},
        "kidney_disease": {"probability": 0.6}
    }
    clusters = detect_comorbidities(patient, predictions)
    cluster_names = [c["name"] for c in clusters]
    assert "Metabolic Syndrome" in cluster_names or "Cardiorenal-Metabolic (CKM) Syndrome" in cluster_names

def test_disease_interactions():
    predictions = {
        "diabetes": {"probability": 0.8},
        "kidney_disease": {"probability": 0.7}
    }
    interactions = analyze_disease_interactions(predictions)
    assert len(interactions) >= 1
    assert interactions[0]["primary_disease"] == "Diabetes"

def test_unified_patient_summary():
    patient = {"age": 60, "glucose": 140, "systolic_bp": 140, "bmi": 30}
    predictions = {"diabetes": {"probability": 0.75}}
    summary = build_unified_patient_summary(patient, predictions)
    
    assert "combined_risk" in summary
    assert "health_index" in summary
    assert "comorbidities" in summary
    assert "disease_interactions" in summary
