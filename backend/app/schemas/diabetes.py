"""
Diabetes API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DiabetesPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=55)
    time_in_hospital: int = Field(..., ge=1, le=14, description="Time in hospital (days)", example=3)
    num_medications: int = Field(..., ge=1, le=81, description="Number of medications", example=15)
    name: str | None = Field(default=None, description="Patient name")


class DiabetesPredictionResponse(BaseModel):
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
    "age": 55,
    "time_in_hospital": 3,
    "num_medications": 15,
}
