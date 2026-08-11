"""
Patient API tests.
"""

from __future__ import annotations

from fastapi import status


def get_access_token(client):

    register_payload = {
        "email": "doctor@test.com",
        "password": "Doctor123",
        "full_name": "Doctor",
        "role": "doctor",
    }

    client.post(
        "/api/v1/auth/register",
        json=register_payload,
    )

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": register_payload["email"],
            "password": register_payload["password"],
        },
    )

    return login.json()["data"]["access_token"]


def test_create_patient(client):

    token = get_access_token(client)

    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "age": 42,
        "gender": "Male",
    }

    response = client.post(
        "/api/v1/patients/",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    )

    body = response.json()

    assert body["success"] is True


def test_list_patients(client):

    token = get_access_token(client)

    response = client.get(
        "/api/v1/patients/",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True

    assert isinstance(body["data"], list)


def _create_patient(client, token: str, email_suffix: str = "") -> dict:
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "age": 42,
        "gender": "Male",
        "allergies": ["Penicillin"],
        "current_medications": ["Aspirin"],
        "medical_history": {"notes": "Hypertension"},
    }

    response = client.post(
        "/api/v1/patients/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    return response.json()["data"]


def test_get_patient(client):
    token = get_access_token(client)
    created = _create_patient(client, token)

    response = client.get(
        f"/api/v1/patients/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["first_name"] == "John"


def test_update_patient(client):
    token = get_access_token(client)
    created = _create_patient(client, token)

    response = client.put(
        f"/api/v1/patients/{created['id']}",
        json={"first_name": "Jane", "age": 43},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["first_name"] == "Jane"
    assert body["data"]["age"] == 43
    assert body["data"]["last_name"] == "Doe"


def test_delete_patient(client):
    token = get_access_token(client)
    created = _create_patient(client, token)

    response = client.delete(
        f"/api/v1/patients/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    follow_up = client.get(
        f"/api/v1/patients/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


def test_update_patient_not_found(client):
    token = get_access_token(client)

    response = client.put(
        "/api/v1/patients/99999",
        json={"first_name": "Missing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND