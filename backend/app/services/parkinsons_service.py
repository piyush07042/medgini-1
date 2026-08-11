"""
Parkinson's Disease prediction service.
"""

from __future__ import annotations

import logging
import platform
from pathlib import Path
from typing import Any, List

import numpy as np
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

    fallback = resolve_model_directory("parkinsons_model")
    if fallback.exists() and fallback.is_dir():
        return fallback
    return candidate


class ParkinsonsService:
    """Thin service wrapper around the shared predictor."""

    def __init__(self, model_directory: str | Path) -> None:
        self.model_directory = _resolve_model_directory(model_directory)
        self.predictor = Predictor(PredictorConfig(model_directory=self.model_directory))
        self._initialized = False
        try:
            self.predictor.initialize()
            self._initialized = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Parkinson's predictor initialization failed: %s", exc)
            self._initialized = False

    def predict(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        if self.predictor is None or not self._initialized:
            raise RuntimeError("Predictor not initialized.")

        result = self.predictor.predict(patient_data)

        conf_label = "Medium"
        try:
            if result.confidence >= settings.PARKINSONS_CONFIDENCE_HIGH:
                conf_label = "High"
            elif result.confidence >= settings.PARKINSONS_CONFIDENCE_MEDIUM:
                conf_label = "Medium"
            else:
                conf_label = "Low"
        except Exception:
            conf_label = "Unknown"

        explanations: List[dict[str, float]] = []
        try:
            df = self.predictor.create_dataframe(patient_data)
            transformed = self.predictor.preprocess(df)

            feature_names = None
            if getattr(self.predictor, "feature_names", None):
                feature_names = list(self.predictor.feature_names)
            else:
                try:
                    feature_names = list(df.columns)
                except Exception:
                    feature_names = None

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
                    for i in idxs:
                        explanations.append({
                            "feature": feature_names[i] if i < len(feature_names) else str(i),
                            "importance": float(abs_vals[i]),
                        })
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
                else:
                    coef = getattr(model, "coef_", None)
                    if coef is not None and feature_names is not None:
                        arr = np.array(coef)
                        if arr.ndim == 1:
                            importances = np.abs(arr)
                        else:
                            importances = np.sum(np.abs(arr), axis=0)
                        idxs = np.argsort(importances)[::-1][:4]
                        explanations = [
                            {"feature": feature_names[i] if i < len(feature_names) else str(i), "importance": float(importances[i])}
                            for i in idxs
                        ]
        except Exception:
            explanations = []

        return {
            "success": True,
            "disease": "parkinsons",
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
            "service": "parkinsons",
            "model_loaded": self._initialized,
            "model_directory": str(self.model_directory),
        }


_service: dict[str, ParkinsonsService] = {}


def get_parkinsons_service(model_directory: str | Path) -> ParkinsonsService:
    from app.core.startup import app_state

    resolved_model_dir = str(_resolve_model_directory(model_directory))

    if resolved_model_dir in _service:
        return _service[resolved_model_dir]

    if getattr(app_state, "parkinsons_service", None) is not None:
        try:
            cached_dir = str(app_state.parkinsons_service.model_directory)
        except Exception:
            cached_dir = None
        if cached_dir == resolved_model_dir:
            _service[resolved_model_dir] = app_state.parkinsons_service
            return app_state.parkinsons_service

    service = ParkinsonsService(model_directory)
    _service[resolved_model_dir] = service

    try:
        if getattr(app_state, "parkinsons_service", None) is None:
            app_state.parkinsons_service = service
    except Exception:
        pass

    return service
