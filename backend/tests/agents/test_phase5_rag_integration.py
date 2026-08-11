from __future__ import annotations

import pytest

from app.agents.supervisor.supervisor import Supervisor
from app.agents.base.agent_state import AgentState
from app.schemas.heart_disease import REQUEST_EXAMPLE


@pytest.mark.asyncio
async def test_phase5_rag_integration_flow():
    supervisor = Supervisor()
    state = AgentState()
    state.patient = REQUEST_EXAMPLE.copy()
    state.patient.setdefault("name", "Test Patient")
    state.patient.setdefault("gender", "unknown")
    state.symptoms = ["chest pain", "shortness of breath"]

    final_state, results, metrics = await supervisor.run(state)

    assert final_state.disease_risk, "Disease risk should be present"
    assert isinstance(final_state.knowledge_results, list)
    assert final_state.knowledge_results, "Knowledge results should be retrieved"
    assert isinstance(final_state.recommendations, list)
    assert final_state.recommendations, "Recommendations should be generated"

    evidence_payloads = [rec.get("evidence") for rec in final_state.recommendations if isinstance(rec, dict)]
    assert any(evidence_payloads), "At least one recommendation should carry evidence"

    citation_lists = [rec.get("citations") for rec in final_state.recommendations if isinstance(rec, dict)]
    assert any(citation_lists), "At least one recommendation should carry citations"

    assert all(isinstance(score, (int, float)) for rec in final_state.recommendations if isinstance(rec, dict) for score in (rec.get("similarity_scores") or []))
    assert any(rec.get("evidence_summary") for rec in final_state.recommendations if isinstance(rec, dict))


def test_http_phase5_response_includes_evidence(client):
    response = client.post(
        "/api/v1/heart-disease/predict",
        json=REQUEST_EXAMPLE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "recommendations" in body
    assert "evidence" in body
    assert "citations" in body
    assert "similarity_scores" in body
    assert "evidence_summary" in body
    assert isinstance(body["evidence"], list)
    assert isinstance(body["citations"], list)
    assert isinstance(body["similarity_scores"], list)
    assert body["evidence_summary"] is None or isinstance(body["evidence_summary"], str)
