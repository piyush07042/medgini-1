import pytest

from app.agents.base.agent_state import AgentState
from app.schemas.parkinsons import ParkinsonsPredictionRequest, REQUEST_EXAMPLE


def test_parkinsons_service_predicts_and_returns_explanations():
    from app.services.parkinsons_service import get_parkinsons_service

    service = get_parkinsons_service("models/parkinsons_model")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "parkinsons"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_parkinsons_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/parkinsons/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "parkinsons"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_api_parkinsons_predict_full_response():
    from app.api.v1.parkinsons import predict

    request_model = ParkinsonsPredictionRequest(**REQUEST_EXAMPLE)
    data = await predict(request_model)
    data = data.model_dump()

    assert data.get("success") is True
    assert data.get("disease") == "parkinsons"
    assert "probability" in data
    assert "confidence_label" in data
    assert "recommendations" in data
    assert "final_report" in data


@pytest.mark.asyncio
async def test_supervisor_parkinsons_workflow():
    from app.agents.supervisor.supervisor import Supervisor

    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Parkinson's Patient")
    state.symptoms = ["tremor"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert dr["disease"] == "parkinsons"
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"
