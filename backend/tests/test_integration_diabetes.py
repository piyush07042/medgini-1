import pytest

from app.agents.base.agent_state import AgentState
from app.agents.risk.disease_risk_agent import DiseaseRiskAgent
from app.schemas.diabetes import DiabetesPredictionRequest


REQUEST_EXAMPLE = {
    "age": 55,
    "bmi": 32.5,
    "glucose": 160,
    "systolic_bp": 140,
    "insulin": 85,
    "name": "Test Diabetes Patient",
}


def test_diabetes_service_predicts_and_returns_explanations():
    from app.services.diabetes_service import get_diabetes_service

    service = get_diabetes_service("models/diabetes")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "diabetes"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_diabetes_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/diabetes/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "diabetes"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_disease_risk_agent_uses_diabetes_service_for_diabetes_context():
    state = AgentState()
    state.patient_context = {
        "age": 55,
        "bmi": 32,
        "glucose": 150,
        "systolic_bp": 140,
        "insulin": 80,
        "diagnosis": "Type 2 Diabetes",
    }

    agent = DiseaseRiskAgent()
    result = await agent.run(state)

    assert result.success
    assert state.disease_risk.get("disease") == "diabetes"
    assert state.disease_risk.get("condition") == "Diabetes Risk"


def test_diabetes_service_handles_missing_values():
    from app.services.diabetes_service import get_diabetes_service

    service = get_diabetes_service("models/diabetes")
    result = service.predict({"age": 45, "bmi": None, "glucose": None, "systolic_bp": None, "insulin": None})

    assert result["success"] is True
    assert result["prediction"] in {0, 1}
