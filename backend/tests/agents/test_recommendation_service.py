"""
Recommendation Service regression tests.
"""

from __future__ import annotations

from app.agents.base.agent_state import AgentState
from app.services.recommendation.recommendation_service import generate_recommendation


def test_generate_recommendation_combines_all_sources():
    state = AgentState()
    state.patient = {
        "name": "Jane Doe",
        "age": 58,
        "gender": "female",
        "smoking": True,
        "bmi": 32,
        "cholesterol": 280,
        "glucose": 130,
    }
    state.disease_risk = {
        "risk_category": "High",
        "probability": 0.85,
        "confidence_label": "High",
        "top_factors": [
            {"feature": "cholesterol", "importance": 0.75},
            {"feature": "systolic_bp", "importance": 0.64},
        ],
    }
    state.knowledge_results = [
        {
            "document": "ACC/AHA guidelines recommend statin initiation for high-risk adults.",
            "metadata": {"source": "ACC/AHA"},
            "similarity_score": 0.92,
        }
    ]
    state.drug_analysis = {
        "status": "FLAGGED",
        "overall_risk": "Medium",
        "interactions": [],
        "allergies": [],
        "contraindications": [],
        "renal_adjustment": {"recommendations": []},
        "liver_adjustment": {"recommendations": []},
        "pregnancy": {"category": "Not Applicable", "explanation": ""},
    }
    state.extracted_metrics = {
        "systolic_bp": 150,
        "heart_rate": 88,
    }

    output = generate_recommendation(state)

    assert output["clinical_summary"]
    assert output["risk_summary"]["prediction"] == "High"
    assert output["risk_summary"]["probability"] == 0.85
    assert output["risk_summary"]["confidence"] == "High"
    assert output["medical_evidence"]
    assert output["drug_safety"]["risk_level"] == "Medium"
    assert all(isinstance(rec, dict) for rec in output["recommendations"])
    assert "Provide smoking cessation support and counseling." in " ".join(
        rec.get("recommendation", "") for rec in output["recommendations"]
    )
    assert output["follow_up"]
    assert output["supporting_factors"]
