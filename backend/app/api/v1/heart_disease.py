"""
Heart Disease Prediction API
"""

from __future__ import annotations

import logging

import copy

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from app.schemas.heart_disease import HeartDiseasePredictionRequest
from app.schemas.heart_disease import HeartDiseasePredictionResponse
from app.core.deps import get_supervisor
from app.agents.base.agent_state import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/heart-disease", tags=["Heart Disease"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {
        "status": "healthy",
        "service": "heart_disease",
    }


@router.post(
    "/predict",
    response_model=HeartDiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def predict(request: HeartDiseasePredictionRequest):

    try:
        supervisor = get_supervisor()
        state = AgentState()
        patient_data = request.model_dump()
        patient_data.setdefault("name", "Heart Disease Patient")
        patient_data.setdefault("gender", "Unknown")
        state.patient = patient_data
        logger.info("HeartDisease API request received; patient keys=%s", list(patient_data.keys()))

        final_state, results, metrics = await supervisor.run(state)
        logger.info(
            "Workflow finished; disease_risk present=%s, agent_results=%s, errors=%s, warnings=%s",
            bool(final_state.disease_risk),
            [result.agent for result in results],
            final_state.errors,
            final_state.warnings,
        )

        prediction = final_state.disease_risk or {}
        if not prediction:
            raise RuntimeError("Disease risk not produced by workflow")

        # Merge recommendations, evidence, citations, and final report from workflow into response
        response = dict(prediction)
        response["recommendations"] = final_state.recommendations or []
        response["structured_recommendation"] = final_state.recommendations[0] if final_state.recommendations else None
        response.setdefault("final_report", final_state.final_report)
        response.setdefault("evidence", [])
        response.setdefault("citations", [])
        response.setdefault("similarity_scores", [])
        response.setdefault("evidence_summary", None)

        if final_state.recommendations:
            first_recommendation = final_state.recommendations[0]
            if isinstance(first_recommendation, dict):
                response["evidence"] = first_recommendation.get("evidence", response["evidence"])
                response["citations"] = first_recommendation.get("citations", response["citations"])
                response["similarity_scores"] = first_recommendation.get("similarity_scores", response["similarity_scores"])
                response["evidence_summary"] = first_recommendation.get("evidence_summary", response["evidence_summary"])

        response.setdefault("disease", response.get("disease") or response.get("condition") or response.get("evaluated_condition") or "heart_disease")
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

        return HeartDiseasePredictionResponse(**response)
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def info():
    return {
        "model": "Heart Disease",
        "version": "1.0.0",
        "status": "ready",
    }
