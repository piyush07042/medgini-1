"""
Authentication API
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.models import User
from app.models.models import UserSession, LoginEvent
import uuid
from app.schemas.common import ApiResponse
from app.schemas.schemas import LoginResponse, Token, UserCreate, UserResponse, RefreshTokenRequest
from app.core.logging import get_logger

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

logger = get_logger("app.api.auth")


def _build_token_payload(user: User, access_token: str, refresh_token: str | None = None) -> Token:
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user,
    )


@router.post(
    "/register",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    logger.info("Step 1: Register endpoint entered for email=%s", user_in.email)
    logger.info("Step 2: Validate request data for email=%s", user_in.email)

    logger.info("Step 3: Check existing user for email=%s", user_in.email)
    existing_user = (
        db.query(User)
        .filter(User.email == user_in.email)
        .first()
    )
    logger.info("Step 4: Existing user lookup complete for email=%s: %s", user_in.email, bool(existing_user))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    logger.info("Step 5: Hash password start for email=%s", user_in.email)
    hashed_password = get_password_hash(user_in.password)
    logger.info("Step 6: Hash password complete for email=%s", user_in.email)

    logger.info("Step 7: Create User model for email=%s", user_in.email)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role,
    )

    logger.info("Step 8: Add User to DB session for email=%s", user_in.email)
    db.add(user)
    logger.info("Step 9: DB session add complete for user=%s", user)

    logger.info("Step 10: Commit DB transaction for user email=%s", user_in.email)
    db.commit()
    logger.info("Step 11: DB commit complete for user email=%s", user_in.email)

    logger.info("Step 12: Refresh user instance from DB for email=%s", user_in.email)
    db.refresh(user)
    logger.info("Step 13: DB refresh complete for user email=%s", user_in.email)

    logger.info("Step 14: Generate response for email=%s", user_in.email)
    response = ApiResponse(
        message="User registered successfully.",
        data=UserResponse.model_validate(user),
    )
    logger.info("Step 15: Returning response for email=%s", user_in.email)
    return response


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
):
    logger.info("Login attempt for username=%s", form_data.username)
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.hashed_password,
        )
    ):
        # record failed login event
        try:
            ip = None
            device = None
            if request is not None and request.client:
                ip = request.client.host
            device = request.headers.get("user-agent") if request is not None else None
            evt = LoginEvent(user_id=user.id if user else None or 0, ip_address=ip, device_info=device, successful=0)
            db.add(evt)
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    token = _build_token_payload(user, access_token, refresh_token)

    # record successful login and create session
    try:
        ip = None
        device = None
        if request is not None and request.client:
            ip = request.client.host
        device = request.headers.get("user-agent") if request is not None else None
        evt = LoginEvent(user_id=user.id, ip_address=ip, device_info=device, successful=1)
        db.add(evt)
        session = UserSession(user_id=user.id, session_token=access_token, device_info=device, ip_address=ip)
        db.add(session)
        db.commit()
    except Exception:
        db.rollback()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        message="Login successful.",
        data=token,
    )


@router.post(
    "/refresh",
    response_model=LoginResponse,
)
def refresh_token_endpoint(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    try:
        data = decode_refresh_token(payload.refresh_token)
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )

        new_access_token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role.value,
            }
        )
        new_refresh_token = create_refresh_token(
            {
                "sub": str(user.id),
                "role": user.role.value,
            }
        )
        token_data = _build_token_payload(user, new_access_token, new_refresh_token)

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            message="Token refreshed successfully.",
            data=token_data,
        )
    except Exception as e:
        logger.warning("Token refresh failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh access token. Please log in again.",
        )


@router.post(
    "/login-json",
    response_model=ApiResponse,
)
def login_json(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
):
    logger.info("JSON login attempt for username=%s", form_data.username)
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.hashed_password,
        )
    ):
        # record failed login event
        try:
            ip = None
            device = None
            if request is not None and request.client:
                ip = request.client.host
            device = request.headers.get("user-agent") if request is not None else None
            evt = LoginEvent(user_id=user.id if user else None or 0, ip_address=ip, device_info=device, successful=0)
            db.add(evt)
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    token = _build_token_payload(user, access_token)

    # record successful login and create session
    try:
        ip = None
        device = None
        if request is not None and request.client:
            ip = request.client.host
        device = request.headers.get("user-agent") if request is not None else None
        evt = LoginEvent(user_id=user.id, ip_address=ip, device_info=device, successful=1)
        db.add(evt)
        session = UserSession(user_id=user.id, session_token=access_token, device_info=device, ip_address=ip)
        db.add(session)
        db.commit()
    except Exception:
        db.rollback()

    return ApiResponse(
        message="Login successful.",
        data=token,
    )