from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrokePredictionRequest(BaseModel):
    age: Optional[float] = Field(default=None, description="Patient age")
    hypertension: Optional[int] = Field(default=None, description="Hypertension flag")
    heart_disease: Optional[int] = Field(default=None, description="Heart disease flag")
    avg_glucose_level: Optional[float] = Field(default=None, description="Average glucose level")
    bmi: Optional[float] = Field(default=None, description="BMI")
    smoking_status: Optional[str] = Field(default=None, description="Smoking status")
    name: Optional[str] = Field(default=None, description="Patient name")


class StrokePredictionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool
    disease: str
    prediction: int
    probability: float
    confidence: float
    confidence_label: str
    class_probabilities: Dict[str, float]
    explanations: List[Dict[str, Any]]
    fallback_reason: Optional[str] = None
    recommendations: List[Dict[str, Any]] | None = None
    report: Optional[Dict[str, Any]] = None


class StrokeHealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
    model_directory: str


REQUEST_EXAMPLE = {
    "age": 67,
    "hypertension": 1,
    "heart_disease": 1,
    "avg_glucose_level": 228.69,
    "bmi": 36.6,
    "smoking_status": "formerly smoked",
    "name": "Sample Patient",
}


class StrokePredictionExample:
    request = StrokePredictionRequest(**REQUEST_EXAMPLE)
