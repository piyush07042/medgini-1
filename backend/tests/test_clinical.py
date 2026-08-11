"""
Clinical workflow API tests.
"""

from __future__ import annotations

from fastapi import status


def test_clinical_analysis(client):

    payload = {

        "patient_context": {

            "name": "John Doe",

            "age": 45,

            "gender": "Male",

            "medical_history": "Hypertension",

        },

        "raw_report_text": "HbA1c 7.5%, Glucose 165 mg/dL",

    }

    response = client.post(
        "/api/v1/clinical/analyze",
        json=payload,
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True

    assert "data" in body