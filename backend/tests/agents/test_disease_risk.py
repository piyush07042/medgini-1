"""
Disease Risk Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.risk.disease_risk_agent import DiseaseRiskAgent


def test_prepare_heart_model_input_creates_heart_fields():
    agent = DiseaseRiskAgent()
    assessment_input = {
        "gender": "Male",
        "blood_pressure": "150/92",
        "cholesterol": "245",
        "glucose": "130",
    }

    heart_input = agent._prepare_heart_model_input(assessment_input)

    assert heart_input["sex"] == 1
    assert heart_input["trestbps"] == 150.0
    assert heart_input["chol"] == 245.0
    assert heart_input["fbs"] == 1


@pytest.mark.asyncio
async def test_disease_risk():

    state = AgentState()

    state.patient_context = {
        "age": 58,
        "glucose": 175,
        "bmi": 31,
    }

    agent = DiseaseRiskAgent()

    result = await agent.run(state)

    assert result.success
    assert state.disease_risk.get("risk_level") in {"low", "moderate", "high"}
    assert "risk_score" in state.disease_risk


@pytest.mark.asyncio
async def test_disease_risk_uses_diabetes_model_when_diagnosis_is_diabetes():

    state = AgentState()

    state.patient_context = {
        "age": 55,
        "bmi": 32,
        "glucose": 150,
        "systolic_bp": 140,
        "cholesterol": 220,
        "diagnosis": "Type 2 Diabetes",
    }

    agent = DiseaseRiskAgent()

    result = await agent.run(state)

    assert result.success
    assert state.disease_risk.get("model_used") == "diabetes_model"
    assert state.disease_risk.get("condition") == "Diabetes Risk"
    assert state.disease_risk.get("risk_category") == "high"
    assert state.metadata.get("risk_source") == "model"


@pytest.mark.asyncio
async def test_disease_risk_uses_kidney_model_when_diagnosis_is_kidney():
    state = AgentState()
    state.patient_context = {
        "age": 65,
        "creatinine": 2.0,
        "blood_urea": 45.0,
        "sgpt": 45.0,
        "albumin": 3.4,
        "diagnosis": "Chronic Kidney Disease",
    }

    agent = DiseaseRiskAgent()
    result = await agent.run(state)

    assert result.success
    assert state.disease_risk.get("model_used") == "kidney_disease_model"
    assert state.disease_risk.get("condition") == "Kidney Disease Risk"
    assert state.disease_risk.get("risk_source") == "model"
