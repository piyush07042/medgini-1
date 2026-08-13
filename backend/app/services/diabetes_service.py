"""
Diabetes prediction service.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List

import numpy as np
import platform

from app.core.config import settings
from ml.inference.predictor import Predictor, PredictorConfig
from ml.registry import resolve_model_directory

try:
    import shap
except Exception:  # pragma: no cover - optional
    shap = None

SHAP_ENABLED = shap is not None and platform.system().lower() != "windows"

logger = logging.getLogger(__name__)


def _resolve_model_directory(model_directory: str | Path) -> Path:
    candidate = Path(model_directory).expanduser()
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()

    if not candidate.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        candidate = (repo_root / candidate).resolve()
        if candidate.exists() and candidate.is_dir():
            return candidate

    fallback = resolve_model_directory("diabetes_model")
    if fallback.exists() and fallback.is_dir():
        return fallback
    return candidate


class DiabetesService:
    def __init__(self, model_directory: str | Path) -> None:
        self.model_directory = _resolve_model_directory(model_directory)
        self.predictor = Predictor(PredictorConfig(model_directory=self.model_directory))
        self._initialized = False
        try:
            self.predictor.initialize()
            self._initialized = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Diabetes predictor initialization failed: %s", exc)
            self._initialized = False

    def _normalize_patient_data(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(patient_data or {})
        if "name" in normalized and not normalized.get("name"):
            normalized.pop("name")

        for field, default_value in {
            "age": 0,
            "time_in_hospital": 0.0,
            "num_medications": 0.0,
        }.items():
            if field not in normalized or normalized.get(field) is None:
                normalized[field] = default_value

        return normalized

    def _build_fallback_result(self, patient_data: dict[str, Any], error: Exception | None = None) -> dict[str, Any]:
        age = float(patient_data.get("age", 0) or 0)
        time_in_hospital = float(patient_data.get("time_in_hospital", 0) or 0)
        num_medications = float(patient_data.get("num_medications", 0) or 0)

        score = 0.0
        if age >= 60:
            score += 0.3
        if time_in_hospital >= 5:
            score += 0.3
        if num_medications >= 15:
            score += 0.3

        score = min(score, 1.0)
        prediction = 1 if score >= 0.5 else 0
        probability = round(score, 3)
        confidence = round(max(probability, 0.5 if prediction == 1 else 0.3), 3)

        return {
            "success": True,
            "disease": "diabetes_readmission_risk",
            "prediction": int(prediction),
            "probability": float(probability),
            "confidence": float(confidence),
            "confidence_label": "High" if confidence >= 0.8 else "Medium" if confidence >= 0.5 else "Low",
            "class_probabilities": {
                "0": round(max(0.0, 1.0 - probability), 3),
                "1": round(min(1.0, probability), 3),
            },
            "explanations": [],
            "fallback_reason": str(error) if error else None,
        }

    def predict(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        if self.predictor is None or not self._initialized:
            raise RuntimeError("Predictor not initialized.")

        normalized_input = self._normalize_patient_data(patient_data)
        try:
            result = self.predictor.predict(normalized_input)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Diabetes predictor failed; using heuristic fallback: %s", exc)
            return self._build_fallback_result(normalized_input, exc)

        conf_label = "Medium"
        try:
            if result.confidence >= settings.HEART_CONFIDENCE_HIGH:
                conf_label = "High"
            elif result.confidence >= settings.HEART_CONFIDENCE_MEDIUM:
                conf_label = "Medium"
            else:
                conf_label = "Low"
        except Exception:
            conf_label = "Unknown"

        explanations: List[dict[str, float]] = []
        try:
            df = self.predictor.create_dataframe(normalized_input)
            feature_names = None
            if getattr(self.predictor, "feature_names", None):
                feature_names = list(self.predictor.feature_names)
            else:
                feature_names = list(df.columns)
            if SHAP_ENABLED and feature_names is not None:
                try:
                    explainer = shap.Explainer(self.predictor.model, df)
                    sv = explainer(df)
                    vals = sv.values
                    if np.asarray(vals).ndim == 3:
                        vals = vals[0, result.prediction, :]
                    else:
                        vals = vals[0]
                    abs_vals = np.abs(vals)
                    idxs = np.argsort(abs_vals)[::-1][:4]
                    explanations = [
                        {"feature": feature_names[i] if i < len(feature_names) else str(i), "importance": float(abs_vals[i])}
                        for i in idxs
                    ]
                except Exception:
                    explanations = []
            if not explanations:
                model = self.predictor.model
                importances = getattr(model, "feature_importances_", None)
                if importances is not None and feature_names is not None:
                    idxs = np.argsort(np.abs(importances))[::-1][:4]
                    explanations = [
                        {"feature": feature_names[i] if i < len(feature_names) else str(i), "importance": float(abs(importances[i]))}
                        for i in idxs
                    ]
        except Exception:
            explanations = []

        return {
            "success": True,
            "disease": "diabetes_readmission_risk",
            "prediction": int(result.prediction),
            "probability": float(result.probability),
            "confidence": float(result.confidence),
            "confidence_label": conf_label,
            "class_probabilities": result.class_probabilities,
            "explanations": explanations,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy" if self._initialized else "degraded",
            "service": "diabetes",
            "model_loaded": self._initialized,
            "model_directory": str(self.model_directory),
        }


_service: dict[str, DiabetesService] = {}


def get_diabetes_service(model_directory: str | Path) -> DiabetesService:
    from app.core.startup import app_state

    resolved_model_dir = str(_resolve_model_directory(model_directory))
    if resolved_model_dir in _service:
        return _service[resolved_model_dir]

    if getattr(app_state, "diabetes_service", None) is not None:
        try:
            cached_dir = str(app_state.diabetes_service.model_directory)
        except Exception:
            cached_dir = None
        if cached_dir == resolved_model_dir:
            _service[resolved_model_dir] = app_state.diabetes_service
            return app_state.diabetes_service

    service = DiabetesService(model_directory)
    _service[resolved_model_dir] = service
    try:
        if getattr(app_state, "diabetes_service", None) is None:
            app_state.diabetes_service = service
    except Exception:
        pass
    return service
