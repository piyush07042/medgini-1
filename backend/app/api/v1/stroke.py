from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents.base.agent_state import AgentState
from app.core.deps import get_supervisor
from app.core.startup import app_state
from app.schemas.stroke import StrokeHealthResponse, StrokePredictionRequest, StrokePredictionResponse
from app.services.stroke_service import get_stroke_service

router = APIRouter(prefix="/stroke", tags=["stroke"])


@router.post("/predict", response_model=StrokePredictionResponse, status_code=status.HTTP_200_OK)
async def predict_stroke(request: StrokePredictionRequest):
    try:
        service = get_stroke_service(app_state.stroke_model_directory or "models/stroke_model")
        patient_data = request.model_dump(exclude_none=True)
        patient_data.setdefault("name", "Stroke Patient")
        result = service.predict(patient_data)

        supervisor = get_supervisor()
        state = AgentState()
        state.patient = patient_data
        state.symptoms = [
            symptom for symptom in [patient_data.get("symptom"), "sudden weakness", "speech difficulty"] if symptom
        ]
        final_state, _, _ = await supervisor.run(state)
        workflow_prediction = final_state.disease_risk or {}
        if workflow_prediction:
            result.setdefault("recommendations", final_state.recommendations or [])
            if final_state.final_report:
                result.setdefault("report", final_state.final_report)
            if workflow_prediction.get("disease"):
                result["disease"] = workflow_prediction["disease"]
            if workflow_prediction.get("probability") is not None:
                result["probability"] = float(workflow_prediction["probability"])
            if workflow_prediction.get("confidence") is not None:
                result["confidence"] = float(workflow_prediction["confidence"])

        return result
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/health", response_model=StrokeHealthResponse)
async def stroke_health():
    service = get_stroke_service(app_state.stroke_model_directory or "models/stroke_model")
    return service.health()
