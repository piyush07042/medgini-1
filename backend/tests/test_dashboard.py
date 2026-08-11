"""
Dashboard endpoint tests.
"""

from datetime import datetime

from fastapi import status

from app.models.models import AIReport, UserRole


def _register_and_login(client, email: str = "dash@test.com"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Dashboard Doctor",
            "role": UserRole.DOCTOR.value,
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123!"},
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_requires_auth(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_dashboard_returns_empty_state(client):
    headers = _register_and_login(client, "dash-empty@test.com")

    response = client.get("/api/v1/dashboard", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert len(data["stats"]) == 6
    assert data["stats"][0]["title"] == "Total Patients"
    assert data["stats"][0]["value"] == "0"
    assert data["recent_patients"] == []
    assert data["recent_reports"] == []
    assert data["recent_predictions"] == []
    assert len(data["system_status"]) >= 5
    assert "pending_reports" in data["summary"]


def test_dashboard_aggregates_patient_data(client):
    headers = _register_and_login(client, "dash-data@test.com")

    patient_response = client.post(
        "/api/v1/patients/",
        headers=headers,
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "age": 45,
            "gender": "Female",
        },
    )
    patient_id = patient_response.json()["data"]["id"]

    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        db.add(
            AIReport(
                patient_id=patient_id,
                risk_assessment={
                    "disease": "Diabetes",
                    "risk_category": "high",
                    "confidence": 0.92,
                },
                rag_evidence=[],
                drug_safety_alerts={},
                clinical_summary="High risk diabetes case.",
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert data["stats"][0]["value"] == "1"
    assert len(data["recent_patients"]) == 1
    assert data["recent_patients"][0]["name"] == "Jane Doe"
    assert len(data["recent_predictions"]) == 1
    assert data["recent_predictions"][0]["disease"] == "Diabetes"
    assert data["recent_predictions"][0]["risk"] == "High"
    assert data["summary"]["high_risk_patients"] >= 1


def test_dashboard_prediction_save_and_refresh(client):
    headers = _register_and_login(client, "dash-prediction@test.com")

    patient_response = client.post(
        "/api/v1/patients/",
        headers=headers,
        json={
            "first_name": "Alex",
            "last_name": "Smith",
            "age": 55,
            "gender": "Male",
        },
    )
    patient_id = patient_response.json()["data"]["id"]

    response = client.post(
        "/api/v1/dashboard/prediction",
        headers=headers,
        json={
            "patient_id": patient_id,
            "risk_assessment": {
                "disease": "Heart Disease",
                "risk_category": "high",
                "confidence": 0.95,
            },
            "rag_evidence": [],
            "drug_safety_alerts": {},
            "clinical_summary": "Automated prediction save test.",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] is not None

    dashboard_response = client.get("/api/v1/dashboard", headers=headers)
    assert dashboard_response.status_code == status.HTTP_200_OK
    data = dashboard_response.json()["data"]
    assert data["stats"][1]["title"] == "AI Reports Generated"
    assert int(data["stats"][1]["value"]) >= 1
    assert len(data["recent_predictions"]) == 1
    assert data["recent_predictions"][0]["patient"] == "Alex Smith"
    assert data["recent_predictions"][0]["risk"] == "High"
