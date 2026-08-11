"""
Application configuration.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = "MediGenie"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # ==========================================================
    # API
    # ==========================================================

    API_V1_PREFIX: str = "/api/v1"

    # ==========================================================
    # Security
    # ==========================================================

    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = "sqlite:///./medigenie_cdss.db"

    # ==========================================================
    # CORS
    # ==========================================================

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
        ]
    )

    ALLOW_CREDENTIALS: bool = True

    ALLOW_METHODS: list[str] = Field(
        default_factory=lambda: [
            "*",
        ]
    )

    ALLOW_HEADERS: list[str] = Field(
        default_factory=lambda: [
            "*",
        ]
    )

    # ==========================================================
    # Uploads
    # ==========================================================

    UPLOAD_DIRECTORY: str = "uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"
    LOG_DIRECTORY: str = "logs"

    # ==========================================================
    # AI Providers
    # ==========================================================

    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    LANGCHAIN_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # ==========================================================
    # Model Paths
    # ==========================================================

    MODEL_ROOT: str = "models"
    HEART_DISEASE_MODEL_DIRECTORY: str = "models/heart_disease"
    HEART_FAILURE_MODEL_DIRECTORY: str = "models/heart_failure_model"
    STROKE_MODEL_DIRECTORY: str = "models/stroke_model"
    DIABETES_MODEL_DIRECTORY: str = "models/diabetes"
    KIDNEY_DISEASE_MODEL_DIRECTORY: str = "models/kidney_disease_model"
    LIVER_DISEASE_MODEL_DIRECTORY: str = "models/liver_disease_model"
    BREAST_CANCER_MODEL_DIRECTORY: str = "models/breast_cancer_model"
    PARKINSONS_MODEL_DIRECTORY: str = "models/parkinsons_model"
    HEPATITIS_MODEL_DIRECTORY: str = "models/hepatitis_model"
    RAG_DB_DIRECTORY: str = "medigenie_rag_db"
    # ==========================================================
    # Parkinson's Disease Confidence Thresholds (configurable)
    PARKINSONS_CONFIDENCE_HIGH: float = 0.85
    PARKINSONS_CONFIDENCE_MEDIUM: float = 0.65
    # ==========================================================
    # Heart Disease Confidence Thresholds (configurable)
    # ==========================================================
    HEART_CONFIDENCE_HIGH: float = 0.85
    HEART_CONFIDENCE_MEDIUM: float = 0.65
    HEART_FAILURE_CONFIDENCE_HIGH: float = 0.85
    HEART_FAILURE_CONFIDENCE_MEDIUM: float = 0.65
    # ==========================================================
    # Kidney Disease Confidence Thresholds (configurable)
    # ==========================================================
    KIDNEY_CONFIDENCE_HIGH: float = 0.85
    KIDNEY_CONFIDENCE_MEDIUM: float = 0.65
    # ==========================================================
    # Liver Disease Confidence Thresholds (configurable)
    # ==========================================================
    LIVER_CONFIDENCE_HIGH: float = 0.85
    LIVER_CONFIDENCE_MEDIUM: float = 0.65
    # ==========================================================
    # Breast Cancer Confidence Thresholds (configurable)
    # ==========================================================
    BREAST_CANCER_CONFIDENCE_HIGH: float = 0.85
    BREAST_CANCER_CONFIDENCE_MEDIUM: float = 0.65
    # ==========================================================
    # Hepatitis Confidence Thresholds (configurable)
    HEPATITIS_CONFIDENCE_HIGH: float = 0.85
    HEPATITIS_CONFIDENCE_MEDIUM: float = 0.65
    STROKE_CONFIDENCE_HIGH: float = 0.85
    STROKE_CONFIDENCE_MEDIUM: float = 0.65

    # ==========================================================
    # OCR
    # ==========================================================

    TESSERACT_CMD: str | None = None
    POPPLER_PATH: str | None = None

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_URL: str | None = None

    # ==========================================================
    # Notifications
    # ==========================================================

    DRUG_SAFETY_WEBHOOK_URL: str | None = None

    # ==========================================================
    # Scheduler
    # ==========================================================

    SCHEDULER_ENABLED: bool = False
    SCHEDULER_INTERVAL_SECONDS: int = 0
    SCHEDULER_PATIENT_ID: int | None = None
    SCHEDULER_OUT_DIR: str = "temp_reports"
    SCHEDULER_DRY_RUN: bool = True

    AGENT_FALLBACK_MAPPINGS: dict[str, str] = Field(default_factory=dict)

    @field_validator("DEBUG", "ALLOW_CREDENTIALS", mode="before")
    @classmethod
    def parse_bool_fields(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "debug", "release"}:
                return lowered in {"1", "true", "yes", "on", "debug"}
            if lowered in {"0", "false", "no", "off", "none", "null", ""}:
                return False
        return value

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def parse_environment(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("AGENT_FALLBACK_MAPPINGS", mode="before")
    @classmethod
    def parse_fallback_mappings(cls, value):
        if isinstance(value, str) and value.strip():
            try:
                import json

                return json.loads(value)
            except ValueError:
                return {}
        return value or {}

    @field_validator("RAG_DB_DIRECTORY", mode="before")
    @classmethod
    def parse_rag_db_directory(cls, value):
        if value:
            return value
        return os.getenv("CHROMA_DB_DIRECTORY", "medigenie_rag_db")


settings = Settings()