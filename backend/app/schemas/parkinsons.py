"""
Parkinson's Disease API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ParkinsonsPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: float = Field(default=0.0, ge=0.0, le=120.0, description="Subject age", json_schema_extra={"example": 55.0})
    motor_UPDRS: float = Field(default=0.0, ge=0.0, description="Motor UPDRS score", json_schema_extra={"example": 21.0})
    total_UPDRS: float = Field(default=0.0, ge=0.0, description="Total UPDRS score", json_schema_extra={"example": 28.0})
    Jitter_local: float = Field(default=0.0, ge=0.0, description="Jitter (local)", json_schema_extra={"example": 0.005})
    Shimmer_local: float = Field(default=0.0, ge=0.0, description="Shimmer (local)", json_schema_extra={"example": 0.02})
    name: str | None = Field(default=None, description="Patient name")


class ParkinsonsPredictionResponse(BaseModel):
    success: bool = True
    disease: str
    prediction: int
    probability: float
    confidence: float
    confidence_label: str | None = None
    explanations: list[dict] | None = None
    recommendations: list[dict] | None = None
    structured_recommendation: dict | None = None
    final_report: dict | None = None
    evidence: list[dict] | None = None
    citations: list[dict] | None = None
    similarity_scores: list[float] | None = None
    evidence_summary: str | None = None
    class_probabilities: dict[str, float]
    drug_safety: dict | None = None


REQUEST_EXAMPLE = {
    "age": 55.0,
    "motor_UPDRS": 21.0,
    "total_UPDRS": 28.0,
    "Jitter_local": 0.005,
    "Shimmer_local": 0.02,
    "name": "Test Parkinson's Patient",
}
