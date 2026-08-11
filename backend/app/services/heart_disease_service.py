"""
heart_disease_service.py

Heart Disease prediction service.

Responsibilities
----------------
✓ Load predictor once
✓ Validate requests
✓ Execute prediction
✓ Return API-friendly response
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ml.inference.predictor import Predictor
from ml.inference.predictor import PredictorConfig
from ml.registry import resolve_model_directory
from app.core.config import settings
from typing import List
import numpy as _np
import platform

try:
    import shap
except Exception:  # pragma: no cover - optional
    shap = None

# SHAP can be unstable on Windows or when C++ runtime mismatch occurs.
SHAP_ENABLED = shap is not None and platform.system().lower() != "windows"


def _resolve_model_directory(model_directory: str | Path) -> Path:
    """Resolve the best available heart-disease model directory."""
    candidate = Path(model_directory).expanduser()
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()

    if not candidate.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        candidate = (repo_root / candidate).resolve()
        if candidate.exists() and candidate.is_dir():
            return candidate

    fallback = resolve_model_directory("heart_disease")
    if fallback.exists() and fallback.is_dir():
        return fallback

    return candidate

logger = logging.getLogger(__name__)


class HeartDiseaseService:
    """Thin service wrapper around the shared predictor."""

    def __init__(self, model_directory: str | Path) -> None:

        self.model_directory = _resolve_model_directory(model_directory)
        self.predictor = Predictor(
            PredictorConfig(model_directory=self.model_directory)
        )
        self._initialized = False
        try:
            self.predictor.initialize()
            self._initialized = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Heart disease predictor initialization failed: %s", exc)
            self._initialized = False

    def predict(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Execute disease prediction."""

        if self.predictor is None or not self._initialized:
            raise RuntimeError("Predictor not initialized.")

        # Use the predictor for numeric results
        result = self.predictor.predict(patient_data)

        # Determine qualitative confidence label using config thresholds
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

        # Explainability: SHAP preferred, fallback to feature importance / coefficients
        explanations: List[dict[str, float]] = []

        try:
            # Prepare dataframe and transformed features
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
                    if _np.asarray(vals).ndim == 3:
                        # multiclass: take the chosen class contributions
                        vals = vals[0, result.prediction, :]
                    else:
                        vals = vals[0]

                    abs_vals = _np.abs(vals)
                    idxs = _np.argsort(abs_vals)[::-1][:4]
                    for i in idxs:
                        explanations.append({
                            "feature": feature_names[i] if i < len(feature_names) else str(i),
                            "importance": float(abs_vals[i]),
                        })
                except Exception:
                    explanations = []

            if not explanations:
                model = self.predictor.model
                # Tree-based feature importances
                importances = getattr(model, "feature_importances_", None)
                if importances is not None and feature_names is not None:
                    idxs = _np.argsort(_np.abs(importances))[::-1][:4]
                    explanations = [
                        {"feature": feature_names[i] if i < len(feature_names) else str(i), "importance": float(abs(importances[i]))}
                        for i in idxs
                    ]
                else:
                    # Linear model coefficients
                    coef = getattr(model, "coef_", None)
                    if coef is not None and feature_names is not None:
                        arr = _np.array(coef)
                        if arr.ndim == 1:
                            importances = _np.abs(arr)
                        else:
                            importances = _np.sum(_np.abs(arr), axis=0)
                        idxs = _np.argsort(importances)[::-1][:4]
                        explanations = [
                            {"feature": feature_names[i] if i < len(feature_names) else str(i), "importance": float(importances[i])}
                            for i in idxs
                        ]
        except Exception:
            explanations = []

        return {
            "success": True,
            "disease": "heart_disease",
            "prediction": int(result.prediction),
            "probability": float(result.probability),
            "confidence": float(result.confidence),
            "confidence_label": conf_label,
            "class_probabilities": result.class_probabilities,
            "explanations": explanations,
        }

    def health(self) -> dict[str, Any]:
        """Service health status."""

        return {
            "status": "healthy" if self._initialized else "degraded",
            "service": "heart_disease",
            "model_loaded": self._initialized,
            "model_directory": str(self.model_directory),
        }


_service: dict[str, HeartDiseaseService] = {}


def get_heart_disease_service(model_directory: str | Path) -> HeartDiseaseService:
    """Return singleton service instance."""

    from app.core.startup import app_state

    resolved_model_dir = str(_resolve_model_directory(model_directory))

    if resolved_model_dir in _service:
        return _service[resolved_model_dir]

    if app_state.heart_disease_service is not None:
        try:
            cached_dir = str(app_state.heart_disease_service.model_directory)
        except Exception:
            cached_dir = None

        if cached_dir == resolved_model_dir:
            _service[resolved_model_dir] = app_state.heart_disease_service
            return app_state.heart_disease_service

    service = HeartDiseaseService(model_directory)
    _service[resolved_model_dir] = service

    try:
        if app_state.heart_disease_service is None:
            app_state.heart_disease_service = service
    except Exception:
        pass

    return service
