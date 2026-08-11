import pytest

from app.agents.base.agent_state import AgentState
from app.schemas.breast_cancer import BreastCancerPredictionRequest

REQUEST_EXAMPLE = {
    "radius_mean": 17.99,
    "texture_mean": 10.38,
    "perimeter_mean": 122.8,
    "area_mean": 1001.0,
    "smoothness_mean": 0.1184,
    "name": "Test Breast Cancer Patient",
}


def test_breast_cancer_service_predicts_and_returns_explanations():
    from app.services.breast_cancer_service import get_breast_cancer_service

    service = get_breast_cancer_service("models/breast_cancer_model")
    result = service.predict(REQUEST_EXAMPLE)

    assert result["success"] is True
    assert result["disease"] == "breast_cancer"
    assert result["prediction"] in {0, 1}
    assert result["probability"] >= 0.0
    assert result["confidence"] >= 0.0
    assert isinstance(result.get("explanations", []), list)


def test_breast_cancer_api_predict_endpoint(client):
    response = client.post(
        "/api/v1/breast-cancer/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["disease"] == "breast_cancer"
    assert "probability" in body
    assert "confidence_label" in body
    assert isinstance(body.get("recommendations", []), list)


@pytest.mark.asyncio
async def test_api_breast_cancer_predict_full_response():
    from app.api.v1.breast_cancer import predict

    request_model = BreastCancerPredictionRequest(**REQUEST_EXAMPLE)
    data = await predict(request_model)
    data = data.model_dump()

    assert data.get("success") is True
    assert data.get("disease") == "breast_cancer"
    assert "probability" in data
    assert "confidence_label" in data
    assert "recommendations" in data
    assert "final_report" in data


@pytest.mark.asyncio
async def test_supervisor_breast_cancer_workflow():
    from app.agents.supervisor.supervisor import Supervisor

    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Breast Cancer Patient")
    state.symptoms = ["breast pain"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert dr["disease"] == "breast_cancer"
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"
