import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    ADMIN = "admin"
    RESEARCHER = "researcher"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DOCTOR, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patients = relationship("Patient", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    medical_history = Column(JSON, default={})
    allergies = Column(JSON, default=[])
    current_medications = Column(JSON, default=[])
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("User", back_populates="patients")
    medical_reports = relationship("MedicalReport", back_populates="patient")
    ai_reports = relationship("AIReport", back_populates="patient")

class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_reports")

class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    risk_assessment = Column(JSON, nullable=False)
    rag_evidence = Column(JSON, nullable=False)
    drug_safety_alerts = Column(JSON, nullable=False)
    clinical_summary = Column(Text, nullable=False)
    clinical_intelligence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="ai_reports")


class DrugSafetyAssessment(Base):
    __tablename__ = "drug_safety_assessments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    medications = Column(JSON, nullable=False)
    allergies = Column(JSON, nullable=True)
    assessment = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    title = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")
    messages = relationship("ChatMessage", back_populates="conversation")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, nullable=False, unique=True)
    device_info = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Integer, default=0)

    user = relationship("User")


class LoginEvent(Base):
    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String, nullable=True)
    device_info = Column(String, nullable=True)
    successful = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")