"""
Report Generation Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.report_generation.report_generation_agent import ReportGenerationAgent
from app.core.pdf_generator import generate_clinical_pdf_report
from app.services.report.report_service import build_final_report, build_report_from_storage


@pytest.mark.asyncio
async def test_report_generation_agent_builds_structured_report():
    state = AgentState()
    state.patient_context = {
        "name": "John Doe",
        "age": 45,
        "gender": "Female",
    }
    state.symptoms = ["fatigue"]
    state.medications = ["aspirin"]
    state.allergies = ["penicillin"]
    state.disease_risk = {
        "risk_category": "Moderate",
        "probability": 0.42,
        "confidence_label": "Medium",
        "explanations": [{"feature": "age", "value": 45}],
    }
    state.knowledge_results = [
        {"source": "Clinical Guidelines", "text": "Follow-up within 3 months."},
    ]
    state.drug_analysis = {"status": "PASS", "overall_risk": "Low"}
    state.recommendations = [
        {"title": "Lifestyle", "recommendation": "Exercise regularly.", "follow_up_plan": ["Repeat labs in 2 weeks."]},
    ]

    agent = ReportGenerationAgent()
    result = await agent.run(state)

    assert result.success
    report = state.final_report
    assert report["patient_summary"]["name"] == "John Doe"
    assert report["prediction"]["risk_category"] == "Moderate"
    assert report["confidence"] == 0.42
    assert report["explainability"]["top_factors"]
    assert report["retrieved_evidence"]["knowledge_results"][0]["source"] == "Clinical Guidelines"
    assert report["drug_safety"]["status"] == "PASS"
    assert report["recommendations"]
    assert report["follow_up"] == ["Repeat labs in 2 weeks."]
    assert "Clinical Summary for John Doe" in report["clinical_summary"]


def test_generate_clinical_pdf_report_includes_sections():
    report = {
        "generated_at": "2026-08-04T12:00:00Z",
        "patient": {"name": "Jane Doe", "id": 1, "age": 32, "gender": "Female"},
        "patient_summary": {"name": "Jane Doe", "age": 32, "gender": "Female", "summary_text": "Jane Doe Age 32 Gender Female.", "history": {}, "symptoms": [], "medications": [], "allergies": []},
        "symptoms": [],
        "medications": ["metformin"],
        "allergies": ["penicillin"],
        "ocr_findings": {"raw_report_text": "Chest pain noted.", "ocr_result": [], "extracted_metrics": {"glucose": 98}},
        "prediction": {"risk_category": "Low", "probability": 0.12, "confidence": 0.12, "confidence_label": "Low"},
        "probability": 0.12,
        "confidence": 0.12,
        "explainability": {"top_factors": ["Age 32", "BMI 24"], "explanations": []},
        "retrieved_evidence": {"knowledge_results": [{"source": "Journal A", "text": "Heart disease risk is low."}], "evidence_summary": "Journal A: Heart disease risk is low."},
        "drug_safety": {"status": "PASS", "overall_risk": "Low"},
        "recommendations": [{"title": "Preventive Care", "recommendation": "Maintain exercise routine."}],
        "follow_up": ["Reassess in 6 months."],
        "clinical_summary": "Sample summary." ,
    }

    pdf_bytes = generate_clinical_pdf_report(report)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0


def test_build_final_report_includes_required_sections():
    state = AgentState()
    state.patient = {"name": "Alex", "age": 60, "gender": "Male"}
    state.disease_risk = {"risk_category": "High", "probability": 0.87, "confidence_label": "High", "explanations": [{"feature": "smoking", "value": "Current"}]}
    state.knowledge_results = [{"source": "PubMed", "text": "Efficacy data available."}]
    state.drug_analysis = {"status": "FLAGGED", "overall_risk": "High"}
    state.recommendations = [{"title": "Intervention", "recommendation": "Refer to cardiology.", "follow_up_plan": ["Schedule appointment within 2 weeks."]}]

    report = build_final_report(state)

    assert report["patient_summary"]
    assert report["ocr_findings"]["raw_report_text"] == ""
    assert report["prediction"]["risk_category"] == "High"
    assert report["confidence_label"] == "High"
    assert report["retrieved_evidence"]["knowledge_results"]
    assert report["drug_safety"]["status"] == "FLAGGED"
    assert report["recommendations"]
    assert report["follow_up"] == ["Schedule appointment within 2 weeks."]


def test_build_report_from_storage_uses_persisted_ai_report():
    patient = {
        "name": "Alice Smith",
        "id": 77,
        "age": 54,
        "gender": "Female",
        "current_medications": ["lisinopril"],
        "allergies": ["aspirin"],
    }
    summary = {
        "risk_assessment": {"risk_category": "Elevated", "probability": 0.65, "confidence": 0.70, "confidence_label": "Medium"},
        "rag_evidence": [{"source": "Clinical Guidelines", "text": "Control blood pressure."}],
        "drug_safety_alerts": {"status": "PASS", "overall_risk": "Low"},
        "clinical_summary": "Patient at elevated risk.",
        "recommendations": [{"title": "Blood Pressure", "recommendation": "Optimize antihypertensive therapy.", "follow_up_plan": ["Recheck BP in 4 weeks."]}],
        "created_at": "2026-08-04T12:00:00Z",
    }

    report = build_report_from_storage(patient=patient, summary=summary)

    assert report["patient"]["name"] == "Alice Smith"
    assert report["prediction"]["risk_category"] == "Elevated"
    assert report["probability"] == 0.65
    assert report["confidence"] == 0.7
    assert report["retrieved_evidence"]["knowledge_results"][0]["source"] == "Clinical Guidelines"
    assert report["drug_safety"]["status"] == "PASS"
    assert report["recommendations"]
    assert report["follow_up"] == ["Recheck BP in 4 weeks."]
    assert report["generated_at"] == "2026-08-04T12:00:00Z"


def test_generate_clinical_pdf_report_from_storage_report():
    patient = {
        "name": "Alice Smith",
        "id": 77,
        "age": 54,
        "gender": "Female",
        "current_medications": ["lisinopril"],
        "allergies": ["aspirin"],
    }
    summary = {
        "risk_assessment": {"risk_category": "Elevated", "probability": 0.65, "confidence": 0.70, "confidence_label": "Medium"},
        "rag_evidence": [{"source": "Clinical Guidelines", "text": "Control blood pressure."}],
        "drug_safety_alerts": {"status": "PASS", "overall_risk": "Low"},
        "clinical_summary": "Patient at elevated risk.",
        "recommendations": [{"title": "Blood Pressure", "recommendation": "Optimize antihypertensive therapy."}],
        "created_at": "2026-08-04T12:00:00Z",
    }

    report = build_report_from_storage(patient=patient, summary=summary)
    pdf_bytes = generate_clinical_pdf_report(report)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
