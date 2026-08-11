"""
Drug Safety Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.drug_safety.drug_safety_agent import (
    DrugSafetyAgent,
)


@pytest.mark.asyncio
async def test_drug_safety():

    state = AgentState()

    state.patient_context = {
        "current_medications": [
            "Metformin",
            "Lisinopril",
        ],
        "allergies": [
            "penicillin",
        ],
    }

    agent = DrugSafetyAgent()

    result = await agent.run(state)

    assert result.success
    assert state.drug_analysis["status"] == "PASS"
    assert state.drug_analysis["overall_risk"] == "Low"
    assert result.metadata["medications_checked"] == 2


def test_drug_safety_service_interaction_and_allergy():
    from app.services.drug_safety_service import get_drug_safety_service

    service = get_drug_safety_service()
    assessment = service.analyze(
        medications=["aspirin", "warfarin", "amoxicillin"],
        patient_allergies=["penicillin"],
        patient_context={"age": 45},
    )["drug_safety_assessment"]

    assert any(item["severity"] == "Major" for item in assessment["interactions"])
    assert any(item["severity"] == "Major" for item in assessment["allergies"])
    assert assessment["overall_risk"] == "High"


def test_drug_safety_service_pregnancy_and_renal_liver():
    from app.services.drug_safety_service import get_drug_safety_service

    service = get_drug_safety_service()
    assessment = service.analyze(
        medications=["lisinopril", "acetaminophen", "statin"],
        patient_allergies=["sulfa"],
        patient_context={
            "age": 32,
            "gender": "female",
            "pregnancy": True,
            "eGFR": 28,
            "ALT": 120,
            "AST": 110,
            "bilirubin": 1.4,
            "medical_history": ["hypertension", "gestational diabetes"],
        },
    )["drug_safety_assessment"]

    assert assessment["pregnancy"]["category"] in {"Contraindicated", "Use with caution", "Safe"}
    assert assessment["renal_adjustment"]["ckd_stage"] in {3, 4}
    assert assessment["liver_adjustment"]["avoid_drugs"]
    assert assessment["overall_risk"] == "High"
