"""
Diabetes API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DiabetesPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=55)
    bmi: float = Field(default=0.0, ge=0.0, description="Body Mass Index", example=28.5)
    glucose: float = Field(default=0.0, ge=0.0, description="Plasma glucose concentration", example=120.0)
    systolic_bp: float = Field(default=0.0, ge=0.0, description="Systolic blood pressure", example=130.0)
    insulin: float = Field(default=0.0, ge=0.0, description="2-hour serum insulin", example=80.0)
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
    "bmi": 28.5,
    "glucose": 120.0,
    "systolic_bp": 130.0,
    "insulin": 80.0,
}
