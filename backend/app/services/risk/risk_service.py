"""
Risk service facade: single entrypoint for disease risk prediction.
"""
from __future__ import annotations

from typing import Any

from app.core.risk_assessment import RiskAssessmentEngine


_engine = RiskAssessmentEngine()


class RiskService:
    """Simple facade around RiskAssessmentEngine for DI and reuse."""

    def __init__(self) -> None:
        self._engine = _engine

    def predict(self, patient: dict[str, Any] | None = None, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._engine.predict(patient=patient, metrics=metrics)


def get_risk_service() -> RiskService:
    return RiskService()
