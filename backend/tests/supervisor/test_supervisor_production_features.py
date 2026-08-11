from __future__ import annotations

import asyncio
import time

import pytest

from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState
from app.agents.base.base_agent import BaseAgent
from app.agents.supervisor.supervisor import Supervisor


class SlowAgent(BaseAgent):
    agent_name = "SlowAgent"

    async def run(self, state: AgentState) -> AgentResult:
        await asyncio.sleep(0.01)
        return AgentResult(agent=self.agent_name, status="SUCCESS", confidence=1.0, result={"slow": True})


class FailingAgent(BaseAgent):
    agent_name = "FailingAgent"

    async def run(self, state: AgentState) -> AgentState:
        raise RuntimeError("boom")


class BackoffAgent(BaseAgent):
    agent_name = "BackoffAgent"

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


class SlowParallelAgent(BaseAgent):
    agent_name = "SlowParallelAgent"

    async def run(self, state: AgentState) -> AgentResult:
        await asyncio.sleep(0.06)
        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=1.0,
            result={"done": True},
        )


@pytest.mark.asyncio
async def test_supervisor_respects_timeout_and_marks_failure(monkeypatch):
    supervisor = Supervisor()
    slow_agent = SlowAgent()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [slow_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}
    state.metadata["agent_timeouts"] = {slow_agent.agent_name: 0.001}

    final_state, results, _ = await supervisor.run(state)

    assert results[0].status == "FAILED"
    assert final_state.metadata["timeouts"][slow_agent.agent_name] == 0.001


@pytest.mark.asyncio
async def test_supervisor_records_execution_metrics(monkeypatch):
    supervisor = Supervisor()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [SlowAgent()])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, _, metrics = await supervisor.run(state)

    assert metrics.total_agents >= 1
    assert final_state.metadata["workflow_duration"] >= 0


@pytest.mark.asyncio
async def test_supervisor_applies_retry_backoff(monkeypatch):
    supervisor = Supervisor()
    backoff_agent = BackoffAgent()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [backoff_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}
    state.metadata["retry_backoff"] = 0.02

    started = time.perf_counter()
    final_state, results, _ = await supervisor.run(state)
    elapsed = time.perf_counter() - started

    assert backoff_agent.calls == 2
    assert results[0].success
    assert final_state.metadata["retry_delays"][backoff_agent.agent_name] == 0.02
    assert elapsed >= 0.02


@pytest.mark.asyncio
async def test_supervisor_executes_independent_agents_in_parallel(monkeypatch):
    supervisor = Supervisor()
    first_agent = SlowParallelAgent()
    second_agent = SlowParallelAgent()
    second_agent.agent_name = "SlowParallelAgentTwo"
    monkeypatch.setattr(supervisor.orchestrator, "agents", [first_agent, second_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    started = time.perf_counter()
    _, results, _ = await supervisor.run(state)
    elapsed = time.perf_counter() - started

    assert len(results) == 2
    assert all(result.success for result in results)
    assert elapsed < 0.12


@pytest.mark.asyncio
async def test_supervisor_dynamically_skips_agents_for_missing_context(monkeypatch):
    supervisor = Supervisor()
    monkeypatch.setattr(supervisor.orchestrator, "agents", supervisor.orchestrator.agents)

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}
    state.medications = []
    state.symptoms = []

    final_state, _, _ = await supervisor.run(state)

    skipped = set(final_state.metadata["routing_plan"]["skipped_agents"])
    assert "DrugSafetyAgent" in skipped
    assert "DiseaseRiskAgent" in skipped


@pytest.mark.asyncio
async def test_supervisor_runs_drug_safety_when_medications_in_patient_context(monkeypatch):
    supervisor = Supervisor()
    monkeypatch.setattr(supervisor.orchestrator, "agents", supervisor.orchestrator.agents)

    state = AgentState()
    state.patient_context = {
        "name": "Test",
        "age": 50,
        "gender": "Female",
        "current_medications": ["aspirin", "warfarin"],
    }
    state.symptoms = ["chest pain"]

    final_state, _, _ = await supervisor.run(state)

    skipped = set(final_state.metadata["routing_plan"]["skipped_agents"])
    assert "DrugSafetyAgent" not in skipped
    assert final_state.drug_analysis
    assert final_state.drug_analysis["overall_risk"] in {"High", "Medium", "Low"}


class FailingAgent(BaseAgent):
    agent_name = "FailingAgent"

    async def run(self, state: AgentState) -> AgentResult:
        raise RuntimeError("boom")


class FallbackSuccessAgent(BaseAgent):
    agent_name = "FallbackSuccessAgent"

    async def run(self, state: AgentState) -> AgentResult:
        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=0.9,
            result={"fallback": True},
        )


class SuccessAgent(BaseAgent):
    agent_name = "SuccessAgent"

    async def run(self, state: AgentState) -> AgentResult:
        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=1.0,
            result={"ok": True},
        )


@pytest.mark.asyncio
async def test_supervisor_uses_fallback_agent_on_primary_failure(monkeypatch):
    supervisor = Supervisor()
    failing_agent = FailingAgent()
    fallback_agent = FallbackSuccessAgent()
    supervisor.orchestrator.register_fallback(failing_agent.agent_name, fallback_agent)
    monkeypatch.setattr(supervisor.orchestrator, "agents", [failing_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, results, _ = await supervisor.run(state)

    assert len(results) == 1
    assert results[0].success
    assert results[0].metadata["fallback_used"] is True
    assert results[0].metadata["replaced_agent"] == failing_agent.agent_name
    assert final_state.metadata["workflow_status"] == "completed_with_fallbacks"


@pytest.mark.asyncio
async def test_supervisor_loads_fallback_config_from_settings(monkeypatch):
    supervisor = Supervisor()
    failing_agent = FailingAgent()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [failing_agent])
    monkeypatch.setattr(
        "app.core.config.settings.AGENT_FALLBACK_MAPPINGS",
        {
            failing_agent.agent_name:
            "tests.supervisor.test_supervisor_production_features.FallbackSuccessAgent",
        },
    )

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, results, _ = await supervisor.run(state)

    assert len(results) == 1
    assert results[0].success
    assert results[0].metadata["fallback_used"] is True
    assert results[0].metadata["replaced_agent"] == failing_agent.agent_name
    assert final_state.metadata["workflow_status"] == "completed_with_fallbacks"
    assert final_state.metadata["fallback_mappings"] == {
        failing_agent.agent_name:
        "tests.supervisor.test_supervisor_production_features.FallbackSuccessAgent",
    }


@pytest.mark.asyncio
async def test_supervisor_manual_fallback_registration_overrides_config(monkeypatch):
    supervisor = Supervisor()
    failing_agent = FailingAgent()
    fallback_agent = FallbackSuccessAgent()
    alternate_fallback = SuccessAgent()
    supervisor.orchestrator.register_fallback(failing_agent.agent_name, fallback_agent)
    monkeypatch.setattr(supervisor.orchestrator, "agents", [failing_agent])
    monkeypatch.setattr(
        "app.core.config.settings.AGENT_FALLBACK_MAPPINGS",
        {failing_agent.agent_name: alternate_fallback.agent_name},
    )

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, results, _ = await supervisor.run(state)

    assert len(results) == 1
    assert results[0].success
    assert results[0].metadata["fallback_used"] is True
    assert results[0].metadata["replaced_agent"] == failing_agent.agent_name
    assert results[0].agent == fallback_agent.agent_name
    assert final_state.metadata["workflow_status"] == "completed_with_fallbacks"


@pytest.mark.asyncio
async def test_supervisor_continues_after_noncritical_failure(monkeypatch):
    supervisor = Supervisor()
    failing_agent = FailingAgent()
    success_agent = SuccessAgent()
    monkeypatch.setattr(supervisor.orchestrator, "agents", [failing_agent, success_agent])

    state = AgentState()
    state.patient_context = {"name": "Test", "age": 48, "gender": "Female"}

    final_state, results, _ = await supervisor.run(state)

    assert len(results) == 2
    assert not results[0].success
    assert results[1].success
    assert final_state.metadata["workflow_status"] == "partial_success"
