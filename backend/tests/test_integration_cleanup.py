from __future__ import annotations

from app.core import risk_assessment
from app.db import session as db_session
from app.services.ocr import ocr_service



def test_ocr_service_extract_text_uses_process_medical_report(monkeypatch):
    captured = {}

    def fake_process(path: str) -> str:
        captured["path"] = path
        return "clinical text"

    monkeypatch.setattr(ocr_service, "process_medical_report", fake_process)

    result = ocr_service.extract_text("report.pdf")

    assert result == "clinical text"
    assert captured["path"] == "report.pdf"




def test_session_uses_sqlite_fallback_for_local_postgres(monkeypatch):
    monkeypatch.setattr(db_session.settings, "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/medigenie")

    engine = db_session._build_engine()

    assert str(engine.url) == "sqlite:///./medigenie_cdss.db"
