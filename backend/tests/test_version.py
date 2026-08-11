"""
Version endpoint tests.
"""

from fastapi import status


def test_version(client):

    response = client.get("/api/v1/version")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True

    assert body["data"]["application"] == "MediGenie"

    assert "version" in body["data"]

    assert "api_version" in body["data"]