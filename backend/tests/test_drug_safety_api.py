"""Drug Safety API tests."""

from __future__ import annotations

from fastapi import status


def test_drug_safety_analyze_store_and_get_patient(client):
    response = client.post(
        "/api/v1/drug-safety/analyze",
        json={
            "medications": ["aspirin", "warfarin"],
            "allergies": ["penicillin"],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["drug_safety_assessment"]["status"] in {"PASS", "FLAGGED"}
    assert "interactions" in body["data"]["drug_safety_assessment"]
    assert "contraindications" in body["data"]["drug_safety_assessment"]
    assert "allergies" in body["data"]["drug_safety_assessment"]
    assert "overall_risk" in body["data"]["drug_safety_assessment"]
    assert "interactions" in body["data"]["drug_safety_assessment"]
    assert "contraindications" in body["data"]["drug_safety_assessment"]
    assert "allergies" in body["data"]["drug_safety_assessment"]
    assert "overall_risk" in body["data"]["drug_safety_assessment"]

    store_response = client.post(
        "/api/v1/drug-safety/store",
        json={
            "patient_id": None,
            "medications": ["aspirin", "warfarin"],
            "allergies": ["penicillin"],
        },
    )

    assert store_response.status_code == status.HTTP_200_OK
    store_body = store_response.json()
    assert store_body["success"] is True
    assert "id" in store_body["data"]

    assessment_id = store_body["data"]["id"]
    get_response = client.get(f"/api/v1/drug-safety/assessment/{assessment_id}")

    assert get_response.status_code == status.HTTP_200_OK
    get_body = get_response.json()
    assert get_body["success"] is True
    assert get_body["data"]["id"] == assessment_id
    assert get_body["data"]["assessment"]["drug_safety_assessment"]["status"] in {"PASS", "FLAGGED"}


def test_drug_safety_two_medications_aspirin_ibuprofen(client):
    response = client.post(
        "/api/v1/drug-safety/analyze",
        json={
            "medications": ["Aspirin", "Ibuprofen"],
            "allergies": ["Penicillin"],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assessment = body["data"]["drug_safety_assessment"]

    # 1. 2 medications parsed and returned
    assert len(assessment["medications_checked"]) == 2
    assert "Aspirin" in assessment["medications_checked"]
    assert "Ibuprofen" in assessment["medications_checked"]

    # 2. Overall risk calculated and NOT "Pending"
    assert assessment["overall_risk"] in {"Medium", "High"}

    # 3. Interactions detected for Aspirin + Ibuprofen
    assert len(assessment["interactions"]) >= 1
    interaction_drugs = [item["drugs_involved"] for item in assessment["interactions"]]
    assert any("Aspirin" in pair and "Ibuprofen" in pair for pair in interaction_drugs)


def test_drug_safety_single_medication_no_interaction(client):
    response = client.post(
        "/api/v1/drug-safety/analyze",
        json={
            "medications": ["Acetaminophen"],
            "allergies": [],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assessment = body["data"]["drug_safety_assessment"]

    assert len(assessment["medications_checked"]) == 1
    assert assessment["overall_risk"] == "Low"
    assert len(assessment["interactions"]) == 0


def test_drug_safety_multiple_medications_with_allergy(client):
    response = client.post(
        "/api/v1/drug-safety/analyze",
        json={
            "medications": ["Amoxicillin", "Metformin", "Lisinopril"],
            "allergies": ["Penicillin"],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assessment = body["data"]["drug_safety_assessment"]

    assert len(assessment["medications_checked"]) == 3
    assert len(assessment["allergies"]) >= 1
    assert assessment["overall_risk"] == "High"


def test_drug_safety_empty_medication_list(client):
    response = client.post(
        "/api/v1/drug-safety/analyze",
        json={
            "medications": [],
            "allergies": [],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assessment = body["data"]["drug_safety_assessment"]

    assert len(assessment["medications_checked"]) == 0
    assert assessment["overall_risk"] == "Low"
    assert len(assessment["interactions"]) == 0


def test_drug_safety_api_failure_validation(client):
    # Missing required 'medications' body
    response = client.post("/api/v1/drug-safety/analyze", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
