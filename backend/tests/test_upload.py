"""
Upload API tests.
"""

from __future__ import annotations

import io

from fastapi import status

from app.agents.base.agent_state import AgentState
from app.api.upload import normalize_workflow_state


def test_invalid_extension(client):

    response = client.post(
        "/api/v1/upload/report",
        files={
            "file": (
                "malware.exe",
                io.BytesIO(b"fake"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_empty_pdf(client):

    response = client.post(
        "/api/v1/upload/report",
        files={
            "file": (
                "report.pdf",
                io.BytesIO(b""),
                "application/pdf",
            )
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_normalize_workflow_state_adds_preview_metadata():
    state = AgentState()
    state.metadata["workflow_status"] = "completed_with_critical_failures"
    state.report_text = ""
    state.ocr_result = []
    state.extracted_metrics = {}
    state.warnings = ["OCR returned no extractable text for the provided report."]

    payload = normalize_workflow_state(state, "report.pdf")

    assert payload["metadata"]["file_name"] == "report.pdf"
    assert payload["metadata"]["workflow_status"] == "completed_with_critical_failures"
    assert payload["metadata"]["processing_notes"]
    assert payload["report_text"]


def test_normalize_workflow_state_fallbacks_for_preview():
    state = AgentState()
    state.ocr_result = [{"metrics": {"glucose": 130, "systolic_bp": 140}}]
    state.extracted_metrics = {}
    state.recommendations = [{"risk_summary": {"condition": "Diabetes Risk", "prediction": "High Risk", "probability": 0.85}}]
    state.patient = {}

    payload = normalize_workflow_state(state, "report.pdf")

    assert payload["extracted_metrics"] == {"glucose": 130, "systolic_bp": 140}
    assert payload["disease_risk"]["condition"] == "Diabetes Risk"
    assert payload["disease_risk"]["prediction"] == "High Risk"
    assert payload["patient"]["glucose"] == 130
    assert payload["patient"]["systolic_bp"] == 140