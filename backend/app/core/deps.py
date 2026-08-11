from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.startup import app_state
from app.db.session import get_db
from app.models.models import User
from app.models.models import UserSession


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Return the authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise credentials_exception

    # Check for session revocation: if a session exists for this token and is revoked, deny access
    session = (
        db.query(UserSession)
        .filter(UserSession.session_token == token)
        .first()
    )
    if session and getattr(session, "revoked", 0):
        raise credentials_exception

    return user


# ---------------------------------------------------------------------
# Supervisor Dependency
# ---------------------------------------------------------------------

def get_supervisor():
    """
    Return the shared supervisor instance for the workflow.
    """

    if app_state.supervisor is None:
        from app.agents.supervisor.supervisor import Supervisor

        app_state.supervisor = Supervisor()

    return app_state.supervisor