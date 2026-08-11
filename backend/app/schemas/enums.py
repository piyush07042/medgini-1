"""
Shared enums used across MediGenie.
"""

from enum import Enum


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class UserRole(str, Enum):
    DOCTOR = "doctor"
    ADMIN = "admin"
    NURSE = "nurse"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskCategory(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class ReportType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"