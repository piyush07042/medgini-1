"""
Medical Knowledge Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.knowledge.medical_knowledge_agent import (
    MedicalKnowledgeAgent,
)


@pytest.mark.asyncio
async def test_medical_knowledge():

    state = AgentState()

    state.diagnosis = "Type 2 Diabetes"

    agent = MedicalKnowledgeAgent()

    result = await agent.run(state)

    assert result.success