"""
Risk assessment utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.prediction_service import PredictionService
from app.core.feature_builder import FeatureBuilder

_DEFAULT_MODEL_ROOT = Path(__file__).resolve().parents[2] / "models"

_prediction_service = PredictionService(model_root=_DEFAULT_MODEL_ROOT)


def get_prediction_service() -> PredictionService:
    """Return the shared prediction service, preferring the startup-initialized one."""
    from app.core.startup import app_state

    return app_state.prediction_service or _prediction_service


# Backwards-compatible constant for tests that expect MODEL_PATHS
MODEL_PATHS: list[str] = []


def _normalize_diagnosis(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().lower()


def _select_model_candidates(patient_metrics: dict[str, Any]) -> list[str]:
    candidates: list[str] = []

    if "glucose" in patient_metrics and "bmi" in patient_metrics:
        if "diabetes_model" not in candidates:
            candidates.append("diabetes_model")

    return candidates


def _build_model_input(
    patient: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    model_name: str,
) -> dict[str, Any]:
    prediction_service = get_prediction_service()
    required_features = prediction_service.get_model_required_features(model_name)
    if required_features:
        return FeatureBuilder.build(
            patient=patient,
            metrics=metrics,
            required_features=required_features,
        )
    return FeatureBuilder.build(patient=patient, metrics=metrics)


def _display_condition_for_model(model_name: str, diagnosis: str | None = None) -> str:
    if model_name == "diabetes_model":
        return "Diabetes Risk"
    if model_name == "heart_failure_model":
        return "Heart Failure Risk"
    if model_name == "stroke_model":
        return "Stroke Risk"
    if model_name == "kidney_disease_model":
        return "Kidney Disease Risk"
    if model_name == "liver_disease_model":
        return "Liver Disease Risk"
    if model_name == "hepatitis_model":
        return "Hepatitis Risk"
    if model_name == "parkinsons_model":
        return "Parkinson's Disease Risk"
    if model_name == "breast_cancer_model":
        return "Breast Cancer Risk"
    if diagnosis:
        return str(diagnosis).title()
    return "Cardiometabolic Risk"


def predict_disease_risk(patient_metrics: dict[str, Any]) -> dict[str, Any]:
    """Evaluate disease risk using the trained model when available."""
    # Try PredictionService-backed predictor next
    candidate_models = _select_model_candidates(patient_metrics)
    diagnosis = _normalize_diagnosis(
        patient_metrics.get("diagnosis")
        or patient_metrics.get("condition")
        or patient_metrics.get("evaluated_condition")
    )

    prediction_service = get_prediction_service()
    for model_name in candidate_models:
        if not prediction_service.has_model(model_name):
            continue

        features = _build_model_input(None, patient_metrics, model_name)
        result = prediction_service.predict(model_name, features)

        if result is None:
            continue

        prob = float(result.get("probability", 0.0))
        conf = float(result.get("confidence", prob))

        if prob >= 0.70:
            risk_level = "high"
        elif prob >= 0.40:
            risk_level = "moderate"
        else:
            risk_level = "low"

        condition = _display_condition_for_model(model_name, diagnosis)
        top_factors = result.get("top_factors") or []
        feature_drivers = [
            factor.get("feature")
            for factor in top_factors
            if isinstance(factor, dict) and factor.get("feature")
        ]

        if not feature_drivers:
            feature_drivers = list(result.get("class_probabilities", {}).keys())

        return {
            "condition": condition,
            "evaluated_condition": "Model-backed Disease Risk",
            "risk_score": round(prob, 3),
            "risk_source": "model",
            "estimated_risk_score_percent": round(prob * 100, 1),
            "risk_level": risk_level,
            "risk_category": risk_level,
            "drivers": feature_drivers,
            "explainable_ai_factors": feature_drivers,
            "recommendations": [
                "Consult clinician for further assessment.",
            ],
            "confidence": round(conf, 3),
            "model_used": model_name,
        }

    return evaluate_disease_risk_heuristic(patient_metrics)


def evaluate_disease_risk_heuristic(patient_metrics: dict[str, Any]) -> dict[str, Any]:
    """Fallback heuristic evaluation used when no trained model is available."""
    score = 0.0
    factors: list[str] = []

    # -------------------------------
    # Age
    # -------------------------------
    age = patient_metrics.get("age")
    if isinstance(age, (int, float)) and age >= 60:
        score += 0.20
        factors.append("age")

    # -------------------------------
    # Blood Pressure
    # -------------------------------
    systolic_bp = patient_metrics.get("systolic_bp")
    if isinstance(systolic_bp, (int, float)) and systolic_bp >= 140:
        score += 0.25
        factors.append("blood_pressure")

    # -------------------------------
    # Cholesterol
    # -------------------------------
    cholesterol = patient_metrics.get("cholesterol")
    if isinstance(cholesterol, (int, float)) and cholesterol >= 240:
        score += 0.25
        factors.append("cholesterol")

    # -------------------------------
    # Blood Sugar
    # -------------------------------
    glucose = (
        patient_metrics.get("fasting_blood_sugar")
        or patient_metrics.get("glucose")
    )

    if isinstance(glucose, (int, float)) and glucose >= 126:
        score += 0.15
        factors.append("blood_glucose")

    # -------------------------------
    # BMI
    # -------------------------------
    bmi = patient_metrics.get("bmi")
    if isinstance(bmi, (int, float)) and bmi >= 30:
        score += 0.15
        factors.append("bmi")

    # -------------------------------
    # Final Risk
    # -------------------------------
    score = min(score, 1.0)

    if score >= 0.70:
        risk_level = "high"
    elif score >= 0.40:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "condition": "Cardiometabolic Risk",
        "evaluated_condition": "Metabolic & Cardiovascular Risk Profile",
        "risk_score": round(score, 3),
        "risk_source": "heuristic",
        "estimated_risk_score_percent": round(score * 100, 1),
        "risk_level": risk_level,
        "risk_category": risk_level,
        "drivers": factors,
        "explainable_ai_factors": factors,
        "recommendations": [
            "Review modifiable cardiovascular risk factors.",
            "Maintain a healthy diet and regular physical activity.",
            "Monitor blood pressure, cholesterol, and blood glucose regularly.",
            "Consult a clinician if symptoms are present.",
        ],
    }


def evaluate_disease_risk(patient_metrics: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible alias to the model-aware risk predictor."""
    return predict_disease_risk(patient_metrics)


@dataclass
class RiskAssessmentEngine:
    """
    Compatibility wrapper for the DiseaseRiskAgent.
    """

    def predict(
        self,
        patient: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Predict disease risk from patient information.
        """

        assessment_input: dict[str, Any] = {}

        if patient:
            assessment_input.update(patient)

        if metrics:
            assessment_input.update(metrics)

        return predict_disease_risk(assessment_input)