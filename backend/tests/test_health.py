"""
Health endpoint tests.
"""

from fastapi import status


def test_health(client):

    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Application health status retrieved successfully."
    assert isinstance(body["data"], dict)
    assert body["data"]["application"] == "MediGenie"
    assert body["data"]["status"] in ("healthy", "degraded")
    assert "services" in body["data"]


def test_readiness(client):

    response = client.get("/api/v1/health/ready")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Application is ready."
    assert body["data"]["ready"] is True