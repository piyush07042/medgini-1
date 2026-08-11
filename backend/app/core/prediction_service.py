"""
Prediction Service

Lightweight service to load packaged models and delegate inference to
the existing ML inference `Predictor` implementation in `ml.inference`.

This keeps model-loading and caching centralized for the backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

try:
    from ml.inference.predictor import load_predictor, Predictor
except Exception:  # pragma: no cover - fail gracefully in editors
    # If the ml package isn't importable in some contexts, provide stubs
    def load_predictor(path):
        raise RuntimeError("ml.inference.predictor not available")

    class Predictor:  # type: ignore
        def predict_json(self, _):
            raise RuntimeError("Predictor stub")


@dataclass
class PredictionService:
    model_root: Path

    def __post_init__(self) -> None:
        self._cache: Dict[str, Predictor] = {}

    def _resolve_model_dir(self, model_name: str) -> Path:
        return (self.model_root / model_name).resolve()

    def has_model(self, model_name: str) -> bool:
        p = self._resolve_model_dir(model_name)
        return p.exists() and any(p.glob("model.*")) or (p / "model.joblib").exists()

    def get_predictor(self, model_name: str) -> Optional[Predictor]:
        if model_name in self._cache:
            return self._cache[model_name]

        model_dir = self._resolve_model_dir(model_name)
        if not model_dir.exists():
            return None

        try:
            predictor = load_predictor(model_dir)
            self._cache[model_name] = predictor
            return predictor
        except Exception:
            return None

    def get_model_schema(self, model_name: str) -> dict[str, Any] | None:
        model_dir = self._resolve_model_dir(model_name)
        schema_path = model_dir / "schema.json"
        if not schema_path.exists():
            return None

        try:
            with open(schema_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def get_model_required_features(self, model_name: str) -> list[str]:
        schema = self.get_model_schema(model_name)
        if not schema:
            return []

        required = schema.get("required_columns", [])
        target = schema.get("target_column")
        return [column for column in required if column != target]

    def predict(self, model_name: str, patient_data: dict[str, Any]) -> Optional[dict]:
        predictor = self.get_predictor(model_name)
        if predictor is None:
            return None
        base = predictor.predict_json(patient_data)

        # Explainability: prefer SHAP per-prediction attributions when
        # available, otherwise fall back to model importances/coefficients.
        top_factors: list[dict[str, Any]] = []

        try:
            model = getattr(predictor, "model", None)
            feature_names = getattr(predictor, "feature_names", None) or []

            # Try SHAP-based local explanations first (fast for small models).
            try:
                import pandas as _pd
                import shap

                if model is not None and feature_names:
                    df = _pd.DataFrame([patient_data])
                    # Ensure columns match expected feature ordering when possible
                    try:
                        df = df[feature_names]
                    except Exception:
                        pass

                    # Model function: raw inputs -> positive-class probability
                    def _model_fn(x):
                        x_df = _pd.DataFrame(x, columns=df.columns)
                        # apply predictor preprocessor if available
                        try:
                            transformed = predictor.pipeline.transform(x_df)
                        except Exception:
                            transformed = x_df.values
                        probs = model.predict_proba(transformed)
                        return probs[:, 1]

                    masker = None
                    try:
                        masker = shap.maskers.Independent(df)
                    except Exception:
                        masker = None

                    explainer = shap.Explainer(_model_fn, masker)
                    sv = explainer(df)
                    # shap values shape: (n_samples, n_features) or (n_samples, n_outputs, n_features)
                    vals = sv.values
                    if hasattr(vals, "ndim") and vals.ndim == 3:
                        # choose positive-class if present
                        vals = vals[0, -1, :]
                    else:
                        vals = vals[0]

                    pairs = sorted(
                        zip(list(df.columns), list(map(float, vals))),
                        key=lambda x: abs(x[1]),
                        reverse=True,
                    )

                    for name, val in pairs[:3]:
                        top_factors.append({
                            "feature": name,
                            "importance": round(float(val), 6),
                            "value": patient_data.get(name),
                        })
            except Exception:
                # SHAP not available or failed; fall back to importance/coef
                importances = None
                if model is not None:
                    importances = getattr(model, "feature_importances_", None)

                # Fallback to linear model coefficients
                if importances is None and model is not None:
                    coef = getattr(model, "coef_", None)
                    if coef is not None:
                        try:
                            import numpy as _np

                            arr = _np.array(coef)
                            if arr.ndim == 1:
                                importances = _np.abs(arr)
                            else:
                                importances = _np.sum(_np.abs(arr), axis=0)
                        except Exception:
                            importances = None

                if importances is not None and len(feature_names) == len(importances):
                    pairs = sorted(
                        zip(feature_names, list(map(float, importances))),
                        key=lambda x: x[1],
                        reverse=True,
                    )

                    for name, imp in pairs[:3]:
                        top_factors.append(
                            {
                                "feature": name,
                                "importance": round(float(imp), 6),
                                "value": patient_data.get(name),
                            }
                        )
        except Exception:
            # Never raise from explainability extraction; degrade gracefully.
            top_factors = []

        # Normalize keys into a consistent prediction envelope that agents expect.
        out = dict(base)
        out.setdefault("drivers", [f.get("feature") for f in top_factors])
        out.setdefault("top_factors", top_factors)
        out.setdefault("explainable_ai_factors", [f.get("feature") for f in top_factors])

        return out
