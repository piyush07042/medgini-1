"""
WorkflowExecutor tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.supervisor.executor import WorkflowExecutor
from app.agents.workflow import WorkflowOrchestrator


@pytest.mark.asyncio
async def test_executor_executes_pipeline():

    orchestrator = WorkflowOrchestrator()

    executor = WorkflowExecutor()

    state = AgentState()

    state.patient_context = {
        "name": "John",
    }

    state.raw_report_text = "Test report"

    final_state, results, metrics = (
        await executor.execute(
            agents=orchestrator.agents,
            state=state,
        )
    )

    assert final_state is not None

    assert isinstance(results, list)

    assert metrics is not None