"""
Heart Disease API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class HeartDiseasePredictionRequest(BaseModel):
    """
    Heart Disease prediction request.
    """

    model_config = ConfigDict(extra="forbid")

    age: int = Field(..., ge=1, le=120, description="Age in years", example=63)
    sex: int = Field(..., ge=0, le=1, description="0 = Female, 1 = Male", example=1)
    cp: int = Field(..., ge=1, le=4, description="Chest pain type", example=3)
    trestbps: float = Field(..., ge=50, le=300, description="Resting blood pressure", example=145)
    chol: float = Field(..., ge=50, le=700, description="Serum cholesterol", example=233)
    fbs: int = Field(..., ge=0, le=1, description="Fasting blood sugar >120 mg/dl", example=1)
    restecg: int = Field(..., ge=0, le=2, example=2)
    thalach: float = Field(..., ge=50, le=250, example=150)
    exang: int = Field(..., ge=0, le=1, example=0)
    oldpeak: float = Field(..., ge=0, le=10, example=2.3)
    slope: int = Field(..., ge=1, le=3, example=3)
    ca: int = Field(..., ge=0, le=4, example=0)
    thal: int = Field(..., ge=3, le=7, example=6)


class HeartDiseasePredictionResponse(BaseModel):
    """
    Prediction response.
    """

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


class ErrorResponse(BaseModel):
    """
    Generic API error response.
    """

    success: bool = False
    error: str
    detail: str | None = None


REQUEST_EXAMPLE = {
    "age": 63,
    "sex": 1,
    "cp": 1,
    "trestbps": 145,
    "chol": 233,
    "fbs": 1,
    "restecg": 2,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 2.3,
    "slope": 3,
    "ca": 0,
    "thal": 6,
}

RESPONSE_EXAMPLE = {
    "success": True,
    "disease": "heart_disease",
    "prediction": 1,
    "probability": 0.91,
    "confidence": 0.91,
    "class_probabilities": {
        "0": 0.09,
        "1": 0.91,
    },
}
