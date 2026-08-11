import pytest

from app.agents.supervisor.supervisor import Supervisor
from app.agents.base.agent_state import AgentState
from app.schemas.heart_disease import REQUEST_EXAMPLE


@pytest.mark.asyncio
async def test_supervisor_heart_workflow():
    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    # Ensure required intake fields exist so PatientIntakeAgent doesn't fail
    state.patient.setdefault("name", "Test Patient")
    state.patient.setdefault("gender", "unknown")

    # Ensure DiseaseRiskAgent is executed by providing symptom context
    state.symptoms = ["chest pain"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk must be produced"
    dr = final_state.disease_risk
    assert "probability" in dr and dr["probability"] is not None
    assert "confidence" in dr and dr["confidence"] is not None
    # our HeartDiseaseService adds a confidence_label when available
    assert "confidence_label" in dr or dr.get("risk_level")
    # Explainability
    assert "explanations" in dr

    # Recommendations and final report populated by later agents
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations must be provided"
    assert isinstance(final_state.final_report, dict)
    assert final_state.final_report, "Final report must be generated"


def test_http_heart_disease_predict_endpoint(client):
    response = client.post(
        "/api/v1/heart-disease/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "probability" in body
    assert "confidence_label" in body
    assert "explanations" in body
    assert "recommendations" in body
    assert "final_report" in body


@pytest.mark.asyncio
async def test_api_heart_predict_full_response():
    # Call the endpoint handler directly to avoid ASGI client compatibility
    from app.api.v1.heart_disease import predict
    from app.schemas.heart_disease import HeartDiseasePredictionRequest

    request_model = HeartDiseasePredictionRequest(**REQUEST_EXAMPLE)
    data = await predict(request_model)
    # `predict` returns a Pydantic model instance; convert to dict for assertions
    data = data.model_dump()
    assert data.get("success") is True
    assert "probability" in data
    assert "confidence_label" in data
    assert "explanations" in data
    assert "recommendations" in data
    assert "final_report" in data
