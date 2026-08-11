"""
Medical Report Analysis Agent tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.report_analysis.report_analysis_agent import (
    MedicalReportAnalysisAgent,
)
from app.agents.supervisor.supervisor import Supervisor
from app.services.ocr.parser import Parser


@pytest.mark.asyncio
async def test_report_analysis():

    agent = MedicalReportAnalysisAgent()

    state = AgentState()

    state.raw_report_text = (
        "HbA1c 8.1%. Glucose elevated."
    )

    result = await agent.run(state)

    assert result.success is True


def test_parser_extracts_structured_metrics():
    report_text = """
    Patient ID: P12345
    Age/Sex: 58 / Male
    BP: 140/90
    BMI: 29.4
    Cholesterol: 220
    Glucose: 98
    ECG: ST-T changes noted
    Heart Rate: 78
    """

    result = Parser.parse(report_text)

    assert result["patient_id"] == "P12345"
    assert result["age"] == 58
    assert result["sex"] == "Male"
    assert result["gender"] == "Male"
    assert result["systolic_bp"] == 140.0
    assert result["diastolic_bp"] == 90.0
    assert result["blood_pressure"] == "140/90"
    assert result["bmi"] == 29.4
    assert result["cholesterol"] == 220.0
    assert result["glucose"] == 98.0
    assert result["heart_rate"] == 78.0
    assert result["ecg"] == "ST-T changes noted"


def test_parser_handles_abbreviations_units_and_reference_ranges():
    report_text = """
    Lab Report
    Patient ID: P9988
    Age: 63 years
    Sex: Female
    FBS: 112 mg/dL (Ref: 70-100 mg/dL)
    HbA1c: 6.8 %
    BP: 128/82 mmHg
    HR: 72 bpm
    ECG: Sinus rhythm
    """

    result = Parser.parse(report_text)

    assert result["patient_id"] == "P9988"
    assert result["age"] == 63
    assert result["sex"] == "Female"
    assert result["glucose"] == 112.0
    assert result["glucose_unit"] == "mg/dL"
    assert result["reference_ranges"]["glucose"]["text"] == "70-100 mg/dL"
    assert result["systolic_bp"] == 128.0
    assert result["diastolic_bp"] == 82.0
    assert result["blood_pressure_unit"] == "mmHg"
    assert result["heart_rate"] == 72.0
    assert result["heart_rate_unit"] == "bpm"
    assert result["ecg"] == "Sinus rhythm"


def test_parser_handles_alternate_label_formats_and_missing_values():
    report_text = """
    Patient Age: 57, Sex: M
    Systolic BP: 132
    Diastolic BP: 86
    Fasting Blood Sugar: 128 mg/dL
    Reference Range: 70-100 mg/dL
    HbA1c: 6.9%
    Cholesterol Total: 210 mg/dL
    Heart Rate: 74 bpm
    ECG: Normal sinus rhythm
    BMI = 30.2
    """

    result = Parser.parse(report_text)

    assert result["age"] == 57
    assert result["sex"] == "Male"
    assert result["systolic_bp"] == 132.0
    assert result["diastolic_bp"] == 86.0
    assert result["glucose"] == 128.0
    assert result["glucose_unit"] == "mg/dL"
    assert result["hba1c"] == 6.9
    assert result["cholesterol"] == 210.0
    assert result["heart_rate"] == 74.0
    assert result["ecg"] == "Normal sinus rhythm"


def test_parser_ignores_invalid_or_missing_values():
    report_text = """
    Patient Age: unknown
    BP: not available
    FBS: N/A
    HbA1c: invalid
    ECG: pending review
    """

    result = Parser.parse(report_text)

    assert "age" not in result
    assert "systolic_bp" not in result
    assert "glucose" not in result
    assert "hba1c" not in result
    assert result["ecg"] == "pending review"


@pytest.mark.asyncio
async def test_supervisor_pipeline_with_uploaded_pdf_and_image(monkeypatch, tmp_path):
    pdf_path = tmp_path / "report.pdf"
    image_path = tmp_path / "report.png"
    pdf_path.write_bytes(b"pdf")
    image_path.write_bytes(b"png")

    def fake_extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            return "Patient ID: P7777\nAge/Sex: 58 / Male\nBP: 140/90 mmHg\nFBS: 98 mg/dL\nHR: 78 bpm\nECG: ST-T changes noted"
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            return "Patient ID: P8888\nAge/Sex: 62 / Female\nBP: 130/84 mmHg\nFBS: 105 mg/dL\nHR: 74 bpm\nECG: Normal sinus rhythm"
        return ""

    monkeypatch.setattr(
        "app.agents.report_analysis.medical_report_analysis_agent.OCRService.extract_text",
        fake_extract_text,
    )

    state = AgentState(uploaded_reports=[str(pdf_path), str(image_path)])
    medical_agent = MedicalReportAnalysisAgent()
    result = await medical_agent.run(state)

    assert result.success is True
    assert state.patient["patient_id"] == "P7777"
    assert state.patient["blood_pressure"] == "140/90"
    assert state.extracted_metrics["age"] == 58
    assert state.extracted_metrics["glucose"] == 98.0

    supervisor = Supervisor()
    updated_state, workflow_results, _ = await supervisor.run(state)

    assert updated_state.patient["patient_id"] == "P7777"
    assert updated_state.extracted_metrics["glucose"] == 98.0
    assert any(result.agent == "MedicalReportAnalysisAgent" for result in workflow_results)


@pytest.mark.asyncio
async def test_supervisor_routes_parsed_metrics_to_disease_risk(monkeypatch, tmp_path):
    report_path = tmp_path / "risk_report.pdf"
    report_path.write_bytes(b"pdf")

    def fake_extract_text(self, file_path: str) -> str:
        return "Patient ID: P2222\nAge: 60 years\nSex: Male\nBP: 145/95 mmHg\nFBS: 132 mg/dL\nCholesterol: 240\nBMI: 31\nECG: ST-T changes noted"

    monkeypatch.setattr(
        "app.agents.report_analysis.medical_report_analysis_agent.OCRService.extract_text",
        fake_extract_text,
    )

    state = AgentState(uploaded_reports=[str(report_path)])
    supervisor = Supervisor()
    updated_state, workflow_results, _ = await supervisor.run(state)

    assert updated_state.extracted_metrics["glucose"] == 132.0
    assert updated_state.patient["age"] == 60
    assert updated_state.disease_risk.get("risk_level") in {"low", "moderate", "high"}
    assert any(result.agent == "MedicalReportAnalysisAgent" for result in workflow_results)
    assert any(result.agent == "DiseaseRiskAgent" for result in workflow_results)


@pytest.mark.asyncio
async def test_supervisor_handles_ocr_failure_gracefully(monkeypatch, tmp_path):
    report_path = tmp_path / "failed.pdf"
    report_path.write_bytes(b"pdf")

    def fake_extract_text(self, file_path: str) -> str:
        return ""

    monkeypatch.setattr(
        "app.agents.report_analysis.medical_report_analysis_agent.OCRService.extract_text",
        fake_extract_text,
    )

    state = AgentState(uploaded_reports=[str(report_path)])
    medical_agent = MedicalReportAnalysisAgent()
    result = await medical_agent.run(state)

    print("DEBUG_TEST_WARNINGS", result.warnings, state.extracted_metrics)
    assert result.success is True
    assert state.extracted_metrics == {}
    assert isinstance(result.warnings, list)
    assert any(isinstance(warning, str) and "ocr" in warning.lower() for warning in result.warnings)