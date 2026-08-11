"""
Recommendation Agent tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.recommendation.recommendation_agent import (
    RecommendationAgent,
)


@pytest.mark.asyncio
async def test_recommendation():

    state = AgentState()

    state.diagnosis = "Hypertension"

    agent = RecommendationAgent()

    result = await agent.run(state)

    assert result.success