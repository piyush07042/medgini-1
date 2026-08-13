"""FeatureBuilder

Centralized feature engineering utilities used before prediction.
Keep this lightweight: it normalizes keys, fills missing values, and
emits the canonical feature dict expected by models under `ml/models/*`.
"""
from __future__ import annotations

from typing import Any


class FeatureBuilder:
    REQUIRED_FEATURES: list[str] = []

    @classmethod
    def build(
        cls,
        patient: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        required_features: list[str] | None = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}

        if patient:
            out.update(patient)

        if metrics:
            out.update(metrics)

        # Normalize common aliases
        if out.get("blood_pressure") and not out.get("systolic_bp"):
            out["systolic_bp"] = out.get("blood_pressure")

        if out.get("fasting_blood_sugar") and not out.get("glucose"):
            out["glucose"] = out.get("fasting_blood_sugar")

        features = required_features or cls.REQUIRED_FEATURES

        for feature in features:
            if feature not in out or out[feature] is None:
                out[feature] = 0.0
                continue

            value = out[feature]
            if isinstance(value, bool):
                continue

            try:
                out[feature] = float(value)
            except Exception:
                out[feature] = value

        return out
