from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

pwd_context = CryptContext(
    # Use a pure-Python backend by default to avoid native bcrypt
    # runtime issues in test/CI environments. bcrypt remains supported
    # if installed on the system.
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def get_password_hash(
    password: str,
) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = data.copy()

    payload.update(
        {
            "exp": expire,
            "type": "access",
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[
            settings.ALGORITHM,
        ],
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default refresh token expiry: 7 days
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    payload = data.copy()
    payload.update(
        {
            "exp": expire,
            "type": "refresh",
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_refresh_token(
    token: str,
) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type for refresh operation")
    return payload