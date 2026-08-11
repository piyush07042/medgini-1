"""
Workflow Supervisor
===================
"""

from __future__ import annotations

import logging

from app.agents.base.agent_state import AgentState
from app.agents.base.agent_result import AgentResult

from app.agents.supervisor.metrics import WorkflowMetrics
from app.agents.supervisor.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)


class Supervisor:

    def __init__(self):

        self.orchestrator = WorkflowOrchestrator()

    async def run(
        self,
        state: AgentState,
    ) -> tuple[
        AgentState,
        list[AgentResult],
        WorkflowMetrics,
    ]:

        logger.info("Starting MediGenie workflow")

        return await self.orchestrator.execute(state)