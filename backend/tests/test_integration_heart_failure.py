import pytest

from app.agents.base.agent_state import AgentState
from app.schemas.heart_failure import HeartFailurePredictionRequest, REQUEST_EXAMPLE


def test_heart_failure_service_predicts_and_returns_explanations():
    from app.services.heart_failure_service import get_heart_failure_service

    service = get_heart_failure_service("models/heart_failure_model")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "heart_failure"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_heart_failure_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/heart-failure/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "heart_failure"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_api_heart_failure_predict_full_response():
    from app.api.v1.heart_failure import predict

    request_model = HeartFailurePredictionRequest(**REQUEST_EXAMPLE)
    data = await predict(request_model)
    data = data.model_dump()

    assert data.get("success") is True
    assert data.get("disease") == "heart_failure"
    assert "probability" in data
    assert "confidence_label" in data
    assert "recommendations" in data
    assert "final_report" in data


@pytest.mark.asyncio
async def test_supervisor_heart_failure_workflow():
    from app.agents.supervisor.supervisor import Supervisor

    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Heart Failure Patient")
    state.symptoms = ["shortness of breath", "swelling"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert dr["disease"] == "heart_failure"
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"
