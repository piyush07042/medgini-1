"""
Kidney Disease API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KidneyDiseasePredictionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=55)
    creatinine: float = Field(default=0.0, ge=0.0, description="Serum creatinine (sc)", example=1.2)
    blood_urea: float = Field(default=0.0, ge=0.0, description="Blood urea (bu)", example=30.0)
    sgpt: float = Field(default=0.0, ge=0.0, description="Serum glutamate pyruvate transaminase / ALT", example=25.0)
    albumin: float = Field(default=0.0, ge=0.0, description="Serum albumin (al)", example=4.2)
    name: str | None = Field(default=None, description="Patient name")


class KidneyDiseasePredictionResponse(BaseModel):
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
    "creatinine": 1.2,
    "blood_urea": 30.0,
    "sgpt": 25.0,
    "albumin": 4.2,
}
