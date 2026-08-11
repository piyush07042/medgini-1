"""
Heart Failure API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HeartFailurePredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=65)
    ejection_fraction: float = Field(..., ge=5, le=80, description="Ejection fraction (%)", example=35)
    serum_creatinine: float = Field(..., ge=0.2, le=10.0, description="Serum creatinine", example=1.2)
    serum_sodium: float = Field(..., ge=100, le=150, description="Serum sodium", example=137)
    time: int = Field(..., ge=0, le=500, description="Follow-up time in days", example=130)
    name: str | None = Field(default=None, description="Patient name")


class HeartFailurePredictionResponse(BaseModel):
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
    "age": 65,
    "ejection_fraction": 35,
    "serum_creatinine": 1.2,
    "serum_sodium": 137,
    "time": 130,
    "name": "Test Heart Failure Patient",
}
