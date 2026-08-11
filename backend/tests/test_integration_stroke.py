import pytest

from app.agents.base.agent_state import AgentState
from app.schemas.stroke import StrokePredictionRequest, REQUEST_EXAMPLE


def test_stroke_service_predicts_and_returns_explanations():
    from app.services.stroke_service import get_stroke_service

    service = get_stroke_service("models/stroke_model")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "stroke"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_stroke_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/stroke/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "stroke"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_supervisor_stroke_workflow():
    from app.agents.supervisor.supervisor import Supervisor

    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Stroke Patient")
    state.symptoms = ["sudden weakness", "speech difficulty"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert dr["disease"] == "stroke"
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"
