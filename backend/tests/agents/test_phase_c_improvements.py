"""
Tests for improved Phase C agent capabilities.
Covers: Supervisor orchestrator logging, Recommendation Agent CI injection,
Report Agent 9-section guarantee, Drug Safety severity scoring + alternatives.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.base.agent_state import AgentState
from app.agents.base.agent_result import AgentResult


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_state(**kwargs) -> AgentState:
    state = AgentState()
    for k, v in kwargs.items():
        setattr(state, k, v)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 1. Supervisor – execution_log is populated
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_supervisor_execution_log_populated():
    """After executing an agent, the state metadata should contain an execution_log entry."""
    from app.agents.supervisor.orchestrator import WorkflowOrchestrator
    from app.agents.supervisor.metrics import WorkflowMetrics

    orchestrator = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
    orchestrator.logger = MagicMock()
    orchestrator.max_retries = 0
    orchestrator.fallback_agents = {}
    orchestrator.critical_agents = set()

    mock_agent = MagicMock()
    mock_agent.agent_name = "TestAgent"

    good_result = AgentResult(agent="TestAgent", status="SUCCESS", confidence=0.9, result={"ok": True})
    mock_agent.execute = AsyncMock(return_value=good_result)

    state = _make_state()
    metrics = WorkflowMetrics()

    result = await orchestrator._execute_agent(mock_agent, state, metrics)

    assert result.success
    assert "execution_log" in state.metadata
    log = state.metadata["execution_log"]
    assert len(log) == 1
    entry = log[0]
    assert entry["agent"] == "TestAgent"
    assert entry["success"] is True
    assert entry["duration_ms"] >= 0
    assert entry["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_supervisor_execution_log_on_failure():
    """A failed agent should produce an execution_log entry with success=False and an error message."""
    from app.agents.supervisor.orchestrator import WorkflowOrchestrator
    from app.agents.supervisor.metrics import WorkflowMetrics

    orchestrator = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
    orchestrator.logger = MagicMock()
    orchestrator.max_retries = 0
    orchestrator.fallback_agents = {}
    orchestrator.critical_agents = set()

    mock_agent = MagicMock()
    mock_agent.agent_name = "FailingAgent"
    mock_agent.execute = AsyncMock(side_effect=RuntimeError("deliberate test failure"))

    state = _make_state()
    metrics = WorkflowMetrics()

    result = await orchestrator._execute_agent(mock_agent, state, metrics)

    assert not result.success
    log = state.metadata.get("execution_log", [])
    assert len(log) == 1
    entry = log[0]
    assert entry["success"] is False
    assert "deliberate test failure" in (entry.get("error") or "")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Recommendation Agent – Clinical Intelligence is injected
# ─────────────────────────────────────────────────────────────────────────────

def test_recommendation_service_injects_clinical_intelligence():
    """generate_recommendation should detect CI from state metadata and inject guideline actions."""
    from app.services.recommendation.recommendation_service import generate_recommendation

    state = _make_state(
        patient={"name": "Jane", "age": 55, "gender": "Female"},
        disease_risk={"risk_category": "high", "probability": 0.82, "disease": "diabetes"},
        knowledge_results=[],
        drug_analysis={},
        extracted_metrics={"glucose": 140, "bmi": 31},
    )
    state.metadata = {
        "clinical_intelligence": {
            "Guideline": "ADA 2025",
            "Recommended Next Steps": ["Start metformin therapy", "HbA1c every 3 months"],
            "Monitoring Schedule": "Monthly follow-up until stable",
        }
    }
    state.final_report = None

    result = generate_recommendation(state)

    assert "clinical_intelligence" in result
    assert result["clinical_intelligence"]["Guideline"] == "ADA 2025"
    assert result["guideline_reference"] == "ADA 2025"
    assert len(result["guideline_actions"]) > 0
    # A CI-driven recommendation entry should be included
    ci_recs = [r for r in result["recommendations"] if r.get("category") == "Clinical Intelligence"]
    assert len(ci_recs) == 1
    assert "ADA 2025" in ci_recs[0]["recommendation"]


def test_recommendation_service_enriches_lab_values():
    """generate_recommendation should include lab_values extracted from metrics."""
    from app.services.recommendation.recommendation_service import generate_recommendation

    state = _make_state(
        patient={},
        disease_risk={},
        knowledge_results=[],
        drug_analysis={},
        extracted_metrics={"glucose": 200, "hba1c": 9.1, "bmi": 29},
    )
    state.metadata = {}
    state.final_report = None

    result = generate_recommendation(state)

    assert "lab_values" in result
    assert result["lab_values"]["glucose"] == 200
    assert result["lab_values"]["hba1c"] == 9.1
    assert result["lab_values"]["bmi"] == 29


# ─────────────────────────────────────────────────────────────────────────────
# 3. Report Service – all 9 sections are present
# ─────────────────────────────────────────────────────────────────────────────

def test_report_service_guarantees_all_9_sections():
    """build_final_report must always include all 9 mandatory sections."""
    from app.services.report.report_service import build_final_report

    REQUIRED_SECTIONS = [
        "patient_information", "prediction_results", "clinical_intelligence",
        "guideline_recommendations", "drug_safety", "risk_assessment",
        "ai_summary", "follow_up_plan", "references",
    ]

    state = _make_state(
        patient={"name": "John Doe", "age": 60, "gender": "Male"},
        disease_risk={"risk_category": "high", "probability": 0.78},
        knowledge_results=[],
        drug_analysis={},
        extracted_metrics={},
    )
    state.recommendations = []
    state.final_report = None

    report = build_final_report(state)

    for section in REQUIRED_SECTIONS:
        assert section in report, f"Missing section: {section}"
    assert "sections" in report
    assert set(REQUIRED_SECTIONS).issubset(set(report["sections"]))


def test_report_service_references_from_knowledge():
    """References section should be built from knowledge_results."""
    from app.services.report.report_service import build_final_report

    state = _make_state(
        patient={"name": "Alice"},
        disease_risk={},
        knowledge_results=[
            {
                "document": "Blood pressure targets should be below 130/80.",
                "metadata": {"source": "JNC 8 Guidelines"},
                "similarity_score": 0.91,
            }
        ],
        drug_analysis={},
        extracted_metrics={},
    )
    state.recommendations = []
    state.final_report = None

    report = build_final_report(state)

    refs = report.get("references", [])
    assert any(r.get("source") == "JNC 8 Guidelines" for r in refs)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Drug Safety – severity score and alternative medications
# ─────────────────────────────────────────────────────────────────────────────

def test_drug_safety_severity_score_major():
    """A Major interaction should contribute 3 points to severity score."""
    from app.services.drug_safety_service import DrugSafetyService

    service = DrugSafetyService()
    score = service._calculate_severity_score(
        interactions=[{"severity": "Major"}],
        contraindications=[],
        allergies=[],
    )
    assert score == 3


def test_drug_safety_severity_score_capped_at_10():
    """Severity score is capped at 10 regardless of total."""
    from app.services.drug_safety_service import DrugSafetyService

    service = DrugSafetyService()
    many_majors = [{"severity": "Major"}] * 10
    score = service._calculate_severity_score(many_majors, many_majors, many_majors)
    assert score == 10


def test_drug_safety_alternative_medication_suggested():
    """Warfarin in an interaction should trigger a DOAC alternative suggestion."""
    from app.services.drug_safety_service import DrugSafetyService

    service = DrugSafetyService()
    interactions = [{"drugs_involved": ["Aspirin", "Warfarin"], "severity": "Major"}]
    alts = service._suggest_alternatives(
        medications=["aspirin", "warfarin"],
        interactions=interactions,
        contraindications=[],
        conditions=set(),
    )
    assert len(alts) >= 1
    assert any("apixaban" in a.get("suggested_alternative", "").lower() or "doac" in a.get("suggested_alternative", "").lower() for a in alts)


def test_drug_safety_full_assessment_includes_severity_and_alternatives():
    """Full analyze() result should include severity_score and alternative_medications."""
    from app.services.drug_safety_service import DrugSafetyService

    service = DrugSafetyService()
    result = service.analyze(
        medications=["aspirin", "warfarin"],
        patient_allergies=[],
        patient_context={"age": 65, "medical_history": "heart disease"},
    )
    assessment = result.get("drug_safety_assessment", {})
    assert "severity_score" in assessment
    assert isinstance(assessment["severity_score"], int)
    assert "alternative_medications" in assessment


# ─────────────────────────────────────────────────────────────────────────────
# 5. Chat Agent – follow-up suggestions generated
# ─────────────────────────────────────────────────────────────────────────────

def test_chat_follow_up_suggestions_high_risk():
    """High-risk patients should receive urgent follow-up suggestions."""
    from app.api.chat import _build_follow_up_suggestions

    state = _make_state(
        disease_risk={"risk_category": "high", "disease": "Diabetes"},
        drug_analysis={"status": "PASS"},
    )
    suggestions = _build_follow_up_suggestions(state, "what should I do?")
    assert len(suggestions) > 0
    assert any("urgent" in s.lower() or "high-risk" in s.lower() or "warning" in s.lower() for s in suggestions)


def test_chat_rag_sources_extracted():
    """RAG sources should be extracted from knowledge_results."""
    from app.api.chat import _build_rag_sources

    state = _make_state(
        knowledge_results=[
            {"document": "Some doc", "metadata": {"source": "ADA 2025"}, "similarity_score": 0.9},
            {"document": "Another doc", "metadata": {"source": "AHA/ACC"}, "similarity_score": 0.85},
        ],
    )
    state.final_report = None
    sources = _build_rag_sources(state)
    assert "ADA 2025" in sources
    assert "AHA/ACC" in sources
