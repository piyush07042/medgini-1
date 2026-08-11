"""
Recommendation Agent

Combines outputs from:

- Disease Risk Agent
- Medical Knowledge Agent
- Drug Safety Agent

Generates evidence-based clinical considerations.
"""

from __future__ import annotations

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.services.recommendation.recommendation_service import generate_recommendations


class RecommendationAgent(BaseAgent):

    agent_name = "RecommendationAgent"

    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:
        recommendations = generate_recommendations(state)

        # minimal evidence and warnings propagation is handled by the service
        state.recommendations = recommendations

        state.set_agent_output(
            self.agent_name,
            recommendations,
            confidence=0.95,
        )

        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=0.95,
            result=recommendations,
            metadata={
                "recommendation_count": len(recommendations)
            },
        )