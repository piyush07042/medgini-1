"""
Patient Intake Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.intake.patient_intake_agent import PatientIntakeAgent


@pytest.mark.asyncio
async def test_patient_intake_success():

    agent = PatientIntakeAgent()

    state = AgentState()

    state.patient_context = {
        "name": "John Doe",
        "age": 45,
        "gender": "Male",
    }

    result = await agent.run(state)

    assert result.success is True


@pytest.mark.asyncio
async def test_patient_intake_empty_context():

    agent = PatientIntakeAgent()

    state = AgentState()

    result = await agent.run(state)

    assert result is not None