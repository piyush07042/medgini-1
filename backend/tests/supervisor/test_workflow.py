"""
Workflow tests.
"""

from __future__ import annotations

import pytest

from app.agents.base.agent_state import AgentState
from app.agents.workflow import WorkflowOrchestrator


@pytest.mark.asyncio
async def test_workflow_pipeline():

    workflow = WorkflowOrchestrator()

    state = AgentState()

    state.patient_context = {
        "name": "John Doe",
        "age": 60,
        "gender": "Male",
    }

    state.raw_report_text = (
        "Patient has elevated glucose."
    )

    final_state, results, metrics = (
        await workflow.execute(state)
    )

    assert final_state is not None

    assert isinstance(results, list)

    assert metrics is not None


def test_workflow_import_exposes_concrete_orchestrator():

    workflow = WorkflowOrchestrator()

    assert workflow.__class__.__name__ == "WorkflowOrchestrator"
    assert isinstance(workflow, WorkflowOrchestrator)


@pytest.mark.asyncio
async def test_pipeline_contains_agents():

    workflow = WorkflowOrchestrator()

    pipeline = workflow.get_pipeline()

    assert len(pipeline) == 7

    assert isinstance(pipeline, list)