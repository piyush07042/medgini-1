from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import UserRole

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.DOCTOR

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    success: bool = True
    message: str
    data: Token | None = None

# Patient Schemas
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int
    gender: str
    medical_history: Optional[Dict[str, Any]] = {}
    allergies: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []
    avatar_url: Optional[str] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    avatar_url: Optional[str] = None


class MedicalHistoryEntryCreate(BaseModel):
    title: str
    description: str = ""
    event_type: str = "note"
    date: Optional[str] = None


class TimelineEventSchema(BaseModel):
    id: str
    title: str
    description: str
    event_type: str
    date: str
    source: str


class VisitRecordSchema(BaseModel):
    id: str
    date: str
    visit_type: str
    summary: str
    status: str


class PatientResponse(PatientCreate):
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedPatientsSchema(BaseModel):
    items: list[PatientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int