"""
Breast Cancer API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BreastCancerPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    radius_mean: float = Field(
        ..., ge=0.0, le=100.0, description="Mean radius",
        json_schema_extra={"example": 17.99},
    )
    texture_mean: float = Field(
        ..., ge=0.0, le=100.0, description="Mean texture",
        json_schema_extra={"example": 10.38},
    )
    perimeter_mean: float = Field(
        ..., ge=0.0, le=300.0, description="Mean perimeter",
        json_schema_extra={"example": 122.8},
    )
    area_mean: float = Field(
        ..., ge=0.0, le=2500.0, description="Mean area",
        json_schema_extra={"example": 1001.0},
    )
    smoothness_mean: float = Field(
        ..., ge=0.0, le=1.0, description="Mean smoothness",
        json_schema_extra={"example": 0.1184},
    )
    name: str | None = Field(default=None, description="Patient name")


class BreastCancerPredictionResponse(BaseModel):
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
    "radius_mean": 17.99,
    "texture_mean": 10.38,
    "perimeter_mean": 122.8,
    "area_mean": 1001.0,
    "smoothness_mean": 0.1184,
}
