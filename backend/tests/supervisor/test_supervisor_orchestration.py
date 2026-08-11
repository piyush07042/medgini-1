from __future__ import annotations

import pytest

from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState
from app.agents.base.base_agent import BaseAgent
from app.agents.supervisor.supervisor import Supervisor


class FlakyAgent(BaseAgent):
    agent_name = "FlakyAgent"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def run(self, state: AgentState) -> AgentResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")
        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=1.0,
            result={"recovered": True},
        )


@pytest.mark.asyncio
async def test_supervisor_retries_failed_agent_once(monkeypatch):
    supervisor = Supervisor()
    flaky_agent = FlakyAgent()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [flaky_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, results, _ = await supervisor.run(state)

    assert flaky_agent.calls == 2
    assert results[0].success
    assert final_state.metadata["retries"][flaky_agent.agent_name] == 1


@pytest.mark.asyncio
async def test_supervisor_skips_report_analysis_when_no_reports_exist(monkeypatch):
    supervisor = Supervisor()
    monkeypatch.setattr(
        supervisor.orchestrator,
        "agents",
        supervisor.orchestrator.agents,
    )

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 54, "gender": "Male"}

    final_state, _, _ = await supervisor.run(state)

    skipped_agents = final_state.metadata["routing_plan"]["skipped_agents"]

    assert "MedicalReportAnalysisAgent" not in final_state.metadata["routing_plan"]["executed_agents"]
    assert "MedicalReportAnalysisAgent" in skipped_agents
    assert final_state.metadata["routing_plan"]
