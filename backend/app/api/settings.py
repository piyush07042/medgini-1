from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Any
import os

from app.core.deps import get_current_user, get_db
from app.schemas.common import ApiResponse
from app.models.models import User, UserSession, LoginEvent
from app.core.security import verify_password, get_password_hash

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/profile", response_model=ApiResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return ApiResponse(message="Profile retrieved", data={
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value if current_user.role else None,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    })


@router.put("/profile", response_model=ApiResponse)
def update_profile(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    email = payload.get("email")
    full_name = payload.get("full_name")
    if email:
        current_user.email = email
    if full_name:
        current_user.full_name = full_name
    db.add(current_user)
    db.commit()
    return ApiResponse(message="Profile updated", data={"email": current_user.email, "full_name": current_user.full_name})


@router.post("/change-password", response_model=ApiResponse)
def change_password(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current = payload.get("current_password")
    new = payload.get("new_password")
    if not current or not new:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing password fields")
    if not verify_password(current, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password incorrect")
    current_user.hashed_password = get_password_hash(new)
    db.add(current_user)
    db.commit()
    return ApiResponse(message="Password changed")


@router.post("/avatar", response_model=ApiResponse)
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dest_dir = os.path.join(os.getcwd(), "uploads", "avatars")
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"user-{current_user.id}-{file.filename}"
    dest_path = os.path.join(dest_dir, filename)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())
    url = f"/uploads/avatars/{filename}"
    # Persist the avatar URL to the user record
    current_user.avatar_url = url
    db.add(current_user)
    db.commit()
    return ApiResponse(message="Avatar uploaded", data={"url": url})


@router.get("/login-history", response_model=ApiResponse)
def login_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    events = db.query(LoginEvent).filter(LoginEvent.user_id == current_user.id).order_by(LoginEvent.created_at.desc()).limit(50).all()
    data = [{"id": e.id, "ip": e.ip_address, "device": e.device_info, "successful": bool(e.successful), "created_at": e.created_at.isoformat()} for e in events]
    return ApiResponse(message="Login history", data=data)


@router.get("/sessions", response_model=ApiResponse)
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.revoked == 0).order_by(UserSession.last_seen.desc()).all()
    data = [{"id": s.id, "device": s.device_info, "ip": s.ip_address, "created_at": s.created_at.isoformat(), "last_seen": s.last_seen.isoformat()} for s in sessions]
    return ApiResponse(message="Active sessions", data=data)


@router.post("/sessions/{session_id}/revoke", response_model=ApiResponse)
def revoke_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(UserSession).filter(UserSession.id == session_id, UserSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.revoked = 1
    db.add(session)
    db.commit()
    return ApiResponse(message="Session revoked")


@router.get("/devices", response_model=ApiResponse)
def list_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(UserSession).filter(UserSession.user_id == current_user.id).order_by(UserSession.last_seen.desc()).all()
    devices = []
    for s in sessions:
        devices.append({"session_id": s.id, "device": s.device_info or "Unknown", "ip": s.ip_address, "last_seen": s.last_seen.isoformat()})
    return ApiResponse(message="Devices", data=devices)
