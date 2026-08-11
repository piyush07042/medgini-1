"""
Chat API tests.
"""

from __future__ import annotations

from fastapi import status


def test_chat(client):

    payload = {

        "message": "Summarize the patient's condition.",

        "patient_context": {

            "name": "John",

            "age": 55,

        },

    }

    response = client.post(
        "/api/v1/chat/",
        json=payload,
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert body["data"]["reply"] != "This is a simulated response."
    assert body["data"]["reply"]