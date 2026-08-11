from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PatientContextSchema(BaseModel):
    id: Optional[int] = Field(default=None, example=1)
    patient_id: Optional[int] = Field(default=None, example=1)
    age: Optional[int] = Field(default=None, example=52)
    bmi: Optional[float] = Field(default=None, example=31.5)
    glucose: Optional[float] = Field(default=None, example=145.0)
    systolic_bp: Optional[float] = Field(default=None, example=138.0)
    cholesterol: Optional[float] = Field(default=None, example=210.0)
    diagnosis: Optional[str] = Field(default=None, example="Type 2 Diabetes")
    current_medications: Optional[List[str]] = Field(default_factory=list, example=["Lisinopril", "Metformin"])
    allergies: Optional[List[str]] = Field(default_factory=list, example=["Penicillin"])

class AnalysisRequestSchema(BaseModel):
    patient_context: PatientContextSchema
    raw_report_text: Optional[str] = Field(default="", example="Patient has history of uncontrolled hypertension and morning fatigue.")

class AnalysisResponseSchema(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]