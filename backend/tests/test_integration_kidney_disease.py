import pytest

from app.agents.base.agent_state import AgentState
from app.schemas.kidney_disease import KidneyDiseasePredictionRequest

REQUEST_EXAMPLE = {
    "age": 65,
    "creatinine": 1.7,
    "blood_urea": 45.0,
    "sgpt": 40.0,
    "albumin": 3.5,
    "name": "Test Kidney Patient",
}


def test_kidney_service_predicts_and_returns_explanations():
    from app.services.kidney_disease_service import get_kidney_disease_service

    service = get_kidney_disease_service("models/kidney_disease_model")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "kidney_disease"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_kidney_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/kidney-disease/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "kidney_disease"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_api_kidney_predict_full_response():
    from app.api.v1.kidney_disease import predict

    request_model = KidneyDiseasePredictionRequest(**REQUEST_EXAMPLE)
    data = await predict(request_model)
    data = data.model_dump()

    assert data.get("success") is True
    assert data.get("disease") == "kidney_disease"
    assert "probability" in data
    assert "confidence_label" in data
    assert "recommendations" in data
    assert "final_report" in data


@pytest.mark.asyncio
async def test_supervisor_kidney_workflow():
    from app.agents.supervisor.supervisor import Supervisor

    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Kidney Patient")
    state.symptoms = ["fatigue"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert dr["disease"] == "kidney_disease"
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"
