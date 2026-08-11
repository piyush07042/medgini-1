from __future__ import annotations

from app.core import risk_assessment
from app.db import session as db_session
from app.services.ocr import ocr_service


class FakeModel:
    def predict_proba(self, X):
        return [[0.1, 0.9]]

    def predict(self, X):
        return [1]


def test_ocr_service_extract_text_uses_process_medical_report(monkeypatch):
    captured = {}

    def fake_process(path: str) -> str:
        captured["path"] = path
        return "clinical text"

    monkeypatch.setattr(ocr_service, "process_medical_report", fake_process)

    result = ocr_service.extract_text("report.pdf")

    assert result == "clinical text"
    assert captured["path"] == "report.pdf"


def test_predict_disease_risk_prefers_trained_model(monkeypatch):
    fake_artifact = {
        "model": FakeModel(),
        "feature_names": ["age", "glucose", "bmi", "systolic_bp", "cholesterol"],
        "version": "1.0.0",
    }

    monkeypatch.setattr(risk_assessment, "_load_model_artifact", lambda path=None: fake_artifact)
    monkeypatch.setattr(risk_assessment, "MODEL_PATHS", ["/tmp/disease_risk_model.pkl"])

    prediction = risk_assessment.predict_disease_risk(
        {
            "age": 65,
            "glucose": 135,
            "bmi": 31,
            "systolic_bp": 140,
            "cholesterol": 245,
        }
    )

    assert prediction["risk_level"] == "high"
    assert prediction["risk_score"] >= 0.8


def test_session_uses_sqlite_fallback_for_local_postgres(monkeypatch):
    monkeypatch.setattr(db_session.settings, "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/medigenie")

    engine = db_session._build_engine()

    assert str(engine.url) == "sqlite:///./medigenie_cdss.db"
