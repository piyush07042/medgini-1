"""
Parkinson's Disease API Schemas
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ParkinsonsPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mdvp_fo: float = Field(..., ge=50.0, le=300.0, description="Average vocal fundamental frequency", json_schema_extra={"example": 150.0})
    mdvp_jitter: float = Field(..., ge=0.0, le=0.1, description="MDVP:Jitter(%)", json_schema_extra={"example": 0.005})
    mdvp_shimmer: float = Field(..., ge=0.0, le=0.2, description="MDVP:Shimmer", json_schema_extra={"example": 0.02})
    hnr: float = Field(..., ge=0.0, le=40.0, description="Harmonics to Noise Ratio", json_schema_extra={"example": 20.0})
    rpde: float = Field(..., ge=0.0, le=1.0, description="Recurrence Period Density Entropy", json_schema_extra={"example": 0.4})
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
    "mdvp_fo": 150.0,
    "mdvp_jitter": 0.005,
    "mdvp_shimmer": 0.02,
    "hnr": 20.0,
    "rpde": 0.4,
    "name": "Test Parkinson's Patient",
}
