from __future__ import annotations

from app.agents.base.agent_state import AgentState
from app.services.recommendation.recommendation_service import generate_recommendations


def test_recommendations_attach_retrieved_evidence():
    state = AgentState()
    state.disease_risk = {
        "risk_category": "High",
        "risk_score": 0.82,
        "recommendations": ["Monitor blood pressure closely."],
    }
    state.knowledge_results = [
        {
            "document": "ACC/AHA Hypertension Guidelines recommend home BP monitoring and referral for persistent elevation.",
            "metadata": {"source": "ACC/AHA"},
        }
    ]

    recommendations = generate_recommendations(state)

    assert recommendations
    assert all("evidence" in rec for rec in recommendations)
    assert any(
        "ACC/AHA" in evidence.get("source", "") or "Hypertension Guidelines" in evidence.get("text", "")
        for rec in recommendations
        for evidence in rec["evidence"]
    )
