"""
Liver Disease API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LiverDiseasePredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=55)
    bilirubin: float = Field(..., ge=0.0, le=50.0, description="Serum bilirubin", example=1.2)
    alk_phosphatase: float = Field(..., ge=0.0, le=1000.0, description="Alkaline phosphatase", example=120.0)
    sgpt: float = Field(..., ge=0.0, le=1000.0, description="SGPT / ALT", example=35.0)
    sgot: float = Field(..., ge=0.0, le=1000.0, description="SGOT / AST", example=40.0)
    name: str | None = Field(default=None, description="Patient name")


class LiverDiseasePredictionResponse(BaseModel):
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
    "bilirubin": 1.2,
    "alk_phosphatase": 120.0,
    "sgpt": 35.0,
    "sgot": 40.0,
}
