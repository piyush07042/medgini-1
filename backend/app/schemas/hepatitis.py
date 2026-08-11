from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from typing import Optional, List


class HepatitisPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: float = Field(..., description="Age in years", example=45)
    bilirubin: float = Field(..., description="Bilirubin level", example=1.2)
    alk_phosphatase: float = Field(..., description="Alkaline phosphatase", example=85)
    sgpt: float = Field(..., description="SGPT / ALT", example=30)
    sgot: float = Field(..., description="SGOT / AST", example=40)
    name: Optional[str] = None


class HepatitisPredictionResponse(BaseModel):
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
    class_probabilities: dict | None = None
    drug_safety: dict | None = None


REQUEST_EXAMPLE = {
    "age": 45,
    "bilirubin": 1.2,
    "alk_phosphatase": 85,
    "sgpt": 30,
    "sgot": 40,
}

