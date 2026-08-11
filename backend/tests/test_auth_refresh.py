"""
Unit tests for JWT Refresh Token functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)


class TestRefreshTokenCreation:
    """Test refresh token generation."""

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token({"sub": "1", "role": "doctor"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_refresh_type(self):
        token = create_refresh_token({"sub": "42", "role": "admin"})
        payload = decode_refresh_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "42"

    def test_create_refresh_token_with_custom_expiry(self):
        token = create_refresh_token(
            {"sub": "1", "role": "doctor"},
            expires_delta=timedelta(days=1),
        )
        payload = decode_refresh_token(token)
        assert payload["type"] == "refresh"

    def test_create_refresh_token_default_7_day_expiry(self):
        token = create_refresh_token({"sub": "1", "role": "doctor"})
        payload = decode_refresh_token(token)
        assert "exp" in payload


class TestRefreshTokenDecoding:
    """Test refresh token validation and decoding."""

    def test_decode_valid_refresh_token(self):
        token = create_refresh_token({"sub": "99", "role": "doctor"})
        payload = decode_refresh_token(token)
        assert payload["sub"] == "99"
        assert payload["role"] == "doctor"
        assert payload["type"] == "refresh"

    def test_decode_access_token_as_refresh_raises(self):
        access_token = create_access_token({"sub": "1", "role": "doctor"})
        with pytest.raises(ValueError, match="Invalid token type"):
            decode_refresh_token(access_token)

    def test_decode_garbage_token_raises(self):
        with pytest.raises(Exception):
            decode_refresh_token("not.a.valid.token")


class TestRefreshEndpoint:
    """Test the /auth/refresh API endpoint."""

    def test_refresh_endpoint_returns_new_tokens(self, client):
        """Test that /auth/refresh returns a new access_token and refresh_token."""
        # First, log in to get a refresh token
        register_payload = {
            "email": "refresh@test.com",
            "password": "testpassword",
            "full_name": "Test User",
            "role": "doctor",
        }
        client.post("/api/v1/auth/register", json=register_payload)

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": register_payload["email"], "password": register_payload["password"]},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data.get("refresh_token") or (login_data.get("data") or {}).get("refresh_token")
        assert refresh_token is not None, "Login should return a refresh_token"

        # Now use the refresh token to get new tokens
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data.get("message") == "Token refreshed successfully."

    def test_refresh_with_invalid_token_returns_401(self, client):
        """Test that invalid refresh token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    def test_refresh_with_access_token_returns_401(self, client):
        """Test that using an access token as refresh token fails."""
        register_payload = {
            "email": "refresh_access@test.com",
            "password": "testpassword",
            "full_name": "Test User",
            "role": "doctor",
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": register_payload["email"], "password": register_payload["password"]},
        )
        access_token = login_response.json().get("access_token")

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401
