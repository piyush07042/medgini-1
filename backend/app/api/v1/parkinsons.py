"""
Parkinson's Disease Prediction API
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.agents.base.agent_state import AgentState
from app.core.deps import get_supervisor
from app.schemas.parkinsons import (
    ParkinsonsPredictionRequest,
    ParkinsonsPredictionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parkinsons", tags=["Parkinson's Disease"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "healthy", "service": "parkinsons"}


@router.post(
    "/predict",
    response_model=ParkinsonsPredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def predict(request: ParkinsonsPredictionRequest):
    try:
        supervisor = get_supervisor()
        state = AgentState()
        patient_data = request.model_dump()
        patient_data.setdefault("name", "Parkinson's Disease Patient")
        # Map frontend field names → MDVP model feature names used during training
        jitter = patient_data.get("Jitter_local", 0.005)
        shimmer = patient_data.get("Shimmer_local", 0.02)
        patient_data.setdefault("MDVP:Fo(Hz)", 150.0)   # fundamental frequency default
        patient_data.setdefault("MDVP:Fhi(Hz)", 160.0)
        patient_data.setdefault("MDVP:Flo(Hz)", 140.0)
        patient_data.setdefault("MDVP:Jitter(%)", jitter)
        patient_data.setdefault("MDVP:Jitter(Abs)", jitter * 0.00006)
        patient_data.setdefault("MDVP:RAP", jitter * 0.5)
        patient_data.setdefault("MDVP:PPQ", jitter * 0.5)
        patient_data.setdefault("Jitter:DDP", jitter * 1.5)
        patient_data.setdefault("MDVP:Shimmer", shimmer)
        patient_data.setdefault("MDVP:Shimmer(dB)", shimmer * 10)
        patient_data.setdefault("Shimmer:APQ3", shimmer * 0.5)
        patient_data.setdefault("Shimmer:APQ5", shimmer * 0.6)
        patient_data.setdefault("MDVP:APQ", shimmer * 0.7)
        patient_data.setdefault("Shimmer:DDA", shimmer * 1.5)
        patient_data.setdefault("NHR", 0.02)
        patient_data.setdefault("HNR", 21.0)
        patient_data.setdefault("RPDE", 0.4)
        patient_data.setdefault("DFA", 0.7)
        patient_data.setdefault("spread1", -6.0)
        patient_data.setdefault("spread2", 0.2)
        patient_data.setdefault("D2", 2.3)
        patient_data.setdefault("PPE", 0.2)
        state.patient = patient_data
        logger.info("Parkinsons API request received; patient keys=%s", list(patient_data.keys()))

        final_state, results, metrics = await supervisor.run(state)
        prediction = final_state.disease_risk or {}
        if not prediction:
            raise RuntimeError("Disease risk not produced by workflow")

        response = dict(prediction)
        response["recommendations"] = final_state.recommendations or []
        response["structured_recommendation"] = final_state.recommendations[0] if final_state.recommendations else None
        response.setdefault("final_report", final_state.final_report)
        response.setdefault("evidence", [])
        response.setdefault("citations", [])
        response.setdefault("similarity_scores", [])
        response.setdefault("evidence_summary", None)
        response.setdefault(
            "disease",
            response.get("disease")
            or response.get("condition")
            or response.get("evaluated_condition")
            or "parkinsons",
        )
        response.setdefault("prediction", int(response.get("prediction", 1 if float(response.get("risk_score", 0.0)) >= 0.5 else 0)))
        response.setdefault("probability", float(response.get("probability", response.get("confidence", response.get("risk_score", 0.0)))))
        response.setdefault("confidence", float(response.get("confidence", response["probability"])))
        response.setdefault("confidence_label", response.get("confidence_label") or response.get("risk_level") or None)
        response.setdefault("drug_safety", final_state.drug_analysis or {})

        if not isinstance(response.get("class_probabilities"), dict):
            probability_value = float(response.get("probability", 0.0))
            response["class_probabilities"] = {
                "0": round(max(0.0, 1.0 - probability_value), 3),
                "1": round(min(1.0, probability_value), 3),
            }

        if isinstance(response["recommendations"], list):
            normalized = []
            for item in response["recommendations"]:
                if isinstance(item, dict):
                    normalized.append(item)
                else:
                    normalized.append({
                        "priority": "Medium",
                        "title": "Clinical Recommendation",
                        "recommendation": str(item),
                        "evidence": response.get("evidence", []),
                        "citations": response.get("citations", []),
                        "similarity_scores": response.get("similarity_scores", []),
                        "evidence_summary": response.get("evidence_summary"),
                    })
            response["recommendations"] = normalized

        return ParkinsonsPredictionResponse(**response)
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/", status_code=status.HTTP_200_OK)
async def info():
    return {"model": "Parkinson's Disease", "version": "1.0.0", "status": "ready"}
