"""
Authentication API tests.
"""

from fastapi import status


def test_register_user(client):

    payload = {
        "email": "doctor@test.com",
        "password": "Doctor123",
        "full_name": "Test Doctor",
        "role": "doctor",
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    )

    body = response.json()

    assert body["success"] is True


def test_duplicate_registration(client):

    payload = {
        "email": "doctor@test.com",
        "password": "Doctor123",
        "full_name": "Duplicate",
        "role": "doctor",
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_returns_oauth2_token_shape(client):

    register_payload = {
        "email": "oauth2@test.com",
        "password": "Doctor123",
        "full_name": "OAuth2 User",
        "role": "doctor",
    }

    client.post(
        "/api/v1/auth/register",
        json=register_payload,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": register_payload["email"],
            "password": register_payload["password"],
        },
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["data"]["access_token"] == body["access_token"]


def test_invalid_login(client):

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "doctor@test.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED