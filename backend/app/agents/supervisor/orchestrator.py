"""
Workflow Orchestrator
=====================
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time

from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState
from app.agents.base.base_agent import BaseAgent
from app.agents.registry import get_workflow_agents
from app.agents.supervisor.executor import WorkflowExecutor
from app.agents.supervisor.metrics import WorkflowMetrics
from app.core.config import settings

# Phase 8 — Memory Manager
try:
    from app.workflow.memory_manager import memory_manager
    from app.workflow.agent_evaluator import agent_evaluator
    _MEMORY_ENABLED = True
except ImportError:
    _MEMORY_ENABLED = False


class WorkflowOrchestrator:
    """
    Main orchestrator responsible for executing the
    complete MediGenie multi-agent workflow.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.executor = WorkflowExecutor()
        self.agents = get_workflow_agents()
        self.max_retries = 1
        self.fallback_agents: dict[str, BaseAgent] = {}
        self.critical_agents: set[str] = {
            "PatientIntakeAgent",
            "ReportGenerationAgent",
        }

    async def execute(
        self,
        state: AgentState,
    ) -> tuple[
        AgentState,
        list[AgentResult],
        WorkflowMetrics,
    ]:
        """
        Execute the workflow using adaptive routing, retries,
        and failure handling.
        """
        self._load_configured_fallbacks()
        routing_plan = self._build_routing_plan(state)
        state.metadata["routing_plan"] = routing_plan
        state.metadata.setdefault("retries", {})
        state.metadata.setdefault("retry_delays", {})
        state.metadata.setdefault("skipped_agents", [])
        state.metadata.setdefault("timeouts", {})
        state.metadata.setdefault("fallback_mappings", settings.AGENT_FALLBACK_MAPPINGS)

        agents_to_run = [
            agent for agent in self.agents
            if agent.agent_name not in routing_plan["skipped_agents"]
        ]
        routing_plan["executed_agents"] = [
            agent.agent_name for agent in agents_to_run
        ]

        metrics = WorkflowMetrics()
        results: list[AgentResult] = []

        for group in self._build_execution_groups(agents_to_run, state):
            # Phase 8: Optimize memory before each group
            if _MEMORY_ENABLED:
                memory_manager.optimize(state)

            if len(group) == 1:
                result = await self._execute_agent(group[0], state, metrics)
                results.append(result)
                continue

            group_results = await self._execute_agents_parallel(group, state, metrics)
            results.extend(group_results)

        metrics.finish()

        state.metadata["agent_count"] = len(results)
        state.metadata["successful_agents"] = [
            result.agent for result in results if result.success
        ]
        state.metadata["failed_agents"] = [
            result.agent for result in results if not result.success
        ]
        state.metadata["workflow_completed"] = True
        status = "completed"
        if state.metadata.get("critical_failures"):
            status = "completed_with_critical_failures"
        elif any(result.metadata.get("fallback_used") for result in results):
            status = "completed_with_fallbacks"
        elif state.has_errors():
            status = "partial_success"

        state.metadata["workflow_status"] = status
        state.metadata["workflow_duration"] = round(metrics.total_execution_time, 4)
        state.metadata["workflow_metrics"] = metrics.to_dict()
        state.workflow_summary = {
            "agent_count": len(results),
            "successful_agents": state.metadata["successful_agents"],
            "failed_agents": state.metadata["failed_agents"],
            "status": state.metadata["workflow_status"],
            # Phase 8: quality telemetry
            "quality_scores": {
                r.agent: r.quality_score for r in results if r.quality_score > 0
            },
            "guardrail_violations": [
                {"agent": r.agent, "violations": r.guardrail_violations}
                for r in results if r.guardrail_violations
            ],
            "evaluation": {
                r.agent: r.evaluation for r in results if r.evaluation
            },
        }
        state.mark_workflow_completed(state.metadata["workflow_status"])

        return state, results, metrics

    def _build_routing_plan(self, state: AgentState) -> dict[str, object]:
        """Create an adaptive execution plan for the current state."""
        skipped_agents: list[str] = []
        reasons: dict[str, str] = {}

        has_patient_context = bool(state.patient) or bool(state.patient_context)
        has_report_context = bool(state.uploaded_reports) or bool(getattr(state, "raw_report_text", ""))
        has_medications = bool(state.medications)
        if not has_medications:
            patient_medications = []
            if state.patient:
                patient_medications = state.patient.get("current_medications") or patient_medications
            if state.patient_context:
                patient_medications = state.patient_context.get("current_medications") or patient_medications
            has_medications = bool(patient_medications)
        has_symptoms = bool(state.symptoms)

        patient_context = state.patient_context or {}
        demographic_only_context = False
        if patient_context:
            demographic_keys = {"name", "first_name", "last_name", "age", "gender", "sex"}
            additional_keys = [k for k in patient_context.keys() if k not in demographic_keys]
            demographic_only_context = bool(patient_context) and not bool(additional_keys)

        if not has_patient_context:
            skipped_agents.append("PatientIntakeAgent")
            reasons["PatientIntakeAgent"] = "No patient context available"

        if not has_report_context:
            skipped_agents.append("MedicalReportAnalysisAgent")
            reasons["MedicalReportAnalysisAgent"] = (
                "No report input available for OCR or parsing"
            )

        if not has_medications:
            skipped_agents.append("DrugSafetyAgent")
            reasons["DrugSafetyAgent"] = "No medications detected for safety checking"

        if demographic_only_context and not has_report_context and not has_symptoms:
            skipped_agents.append("DiseaseRiskAgent")
            reasons["DiseaseRiskAgent"] = "Only demographic patient context available; insufficient for risk analysis"

        if demographic_only_context and not has_report_context:
            skipped_agents.append("RecommendationAgent")
            reasons["RecommendationAgent"] = "Insufficient clinical context for recommendations"

        return {
            "mode": "adaptive",
            "executed_agents": [],
            "skipped_agents": skipped_agents,
            "reasons": reasons,
            "failure_policy": "retry_then_continue",
        }

    async def _execute_agent(
        self,
        agent: object,
        state: AgentState,
        metrics: WorkflowMetrics,
    ) -> AgentResult:
        """Execute one agent with configurable retry and backoff."""
        timeout_seconds = self._get_timeout_for_agent(state, agent.agent_name)
        result: AgentResult | None = None

        # ---- structured execution log: start ----
        start_ts = time.time()
        self.logger.info(
            "[AGENT START] agent=%s attempt=1/%s timeout=%s",
            agent.agent_name,
            self.max_retries + 1,
            timeout_seconds,
        )

        for attempt in range(self.max_retries + 1):
            attempt_start = time.time()
            try:
                result = await asyncio.wait_for(agent.execute(state), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                result = AgentResult(
                    agent=agent.agent_name,
                    status="FAILED",
                    confidence=0.0,
                    result={},
                    error=f"Timed out after {timeout_seconds}s",
                )
                self.logger.warning(
                    "[AGENT TIMEOUT] agent=%s timeout=%ss",
                    agent.agent_name,
                    timeout_seconds,
                )
            except Exception as exc:
                result = AgentResult(
                    agent=agent.agent_name,
                    status="FAILED",
                    confidence=0.0,
                    result={},
                    error=str(exc),
                )
                self.logger.error(
                    "[AGENT ERROR] agent=%s attempt=%s error=%s",
                    agent.agent_name,
                    attempt + 1,
                    exc,
                    exc_info=True,
                )

            attempt_duration_ms = round((time.time() - attempt_start) * 1000, 2)
            if result.success:
                self.logger.info(
                    "[AGENT SUCCESS] agent=%s attempt=%s duration_ms=%s confidence=%s",
                    agent.agent_name,
                    attempt + 1,
                    attempt_duration_ms,
                    result.confidence,
                )
                break

            if attempt < self.max_retries:
                delay = self._get_retry_backoff(state, agent.agent_name, attempt)
                state.metadata.setdefault("retries", {})[agent.agent_name] = (
                    state.metadata["retries"].get(agent.agent_name, 0) + 1
                )
                state.metadata.setdefault("retry_delays", {})[agent.agent_name] = delay
                if delay > 0:
                    await asyncio.sleep(delay)
                state.add_warning(
                    f"{agent.agent_name} failed; retrying ({attempt + 1}/{self.max_retries})"
                )
                self.logger.warning(
                    "[AGENT RETRY] agent=%s attempt=%s/%s delay=%ss error=%s",
                    agent.agent_name,
                    attempt + 1,
                    self.max_retries,
                    delay,
                    result.error if result else "unknown",
                )

        if result is None:
            result = AgentResult(agent=agent.agent_name, status="FAILED", confidence=0.0, result={})

        if not result.success and agent.agent_name in self.fallback_agents:
            fallback_agent = self.fallback_agents[agent.agent_name]
            fallback_result = await self._execute_agent(fallback_agent, state, metrics)
            if fallback_result.success:
                fallback_result.metadata["fallback_used"] = True
                fallback_result.metadata["replaced_agent"] = agent.agent_name
                result = fallback_result
            else:
                result = AgentResult(
                    agent=agent.agent_name,
                    status="FAILED",
                    confidence=0.0,
                    result={},
                    error=(
                        f"Fallback {fallback_agent.agent_name} also failed: "
                        f"{fallback_result.error or 'unknown'}"
                    ),
                    metadata={
                        "fallback_attempted": fallback_agent.agent_name,
                    },
                )

        if result.error and self._is_agent_critical(agent.agent_name, state):
            state.metadata.setdefault("critical_failures", []).append(agent.agent_name)

        # ---- structured execution log: finish ----
        total_duration_ms = round((time.time() - start_ts) * 1000, 2)
        log_entry = {
            "agent": agent.agent_name,
            "status": result.status if result else "FAILED",
            "success": result.success if result else False,
            "duration_ms": total_duration_ms,
            "confidence": result.confidence if result else 0.0,
            "error": result.error if result else None,
        }
        state.metadata.setdefault("execution_log", []).append(log_entry)

        if result and not result.success:
            self.logger.warning(
                "[AGENT FAILED] agent=%s duration_ms=%s error=%s",
                agent.agent_name,
                total_duration_ms,
                result.error,
            )
        else:
            self.logger.info(
                "[AGENT DONE] agent=%s duration_ms=%s",
                agent.agent_name,
                total_duration_ms,
            )

        metrics.record(result)
        state.record_agent_result(
            agent.agent_name,
            result.result,
            confidence=result.confidence,
            execution_time=result.processing_time,
        )

        state.add_trace(f"{agent.agent_name}: {result.status}")

        if result.error:
            state.add_error(f"{agent.agent_name}: {result.error}")

        if timeout_seconds is not None:
            state.metadata.setdefault("timeouts", {})[agent.agent_name] = timeout_seconds

        for warning in result.warnings:
            state.add_warning(f"{agent.agent_name}: {warning}")

        return result

    async def _execute_agents_parallel(
        self,
        agents: list[object],
        state: AgentState,
        metrics: WorkflowMetrics,
    ) -> list[AgentResult]:
        """Execute a group of compatible agents concurrently."""
        if not agents:
            return []

        agent_states = [copy.deepcopy(state) for _ in agents]
        tasks = [
            self._execute_agent(agent, agent_state, metrics)
            for agent, agent_state in zip(agents, agent_states)
        ]
        results = await asyncio.gather(*tasks)

        for agent, agent_state, result in zip(agents, agent_states, results):
            self._merge_parallel_agent_state(state, agent, agent_state, result)

        return list(results)

    def _build_execution_groups(
        self,
        agents: list[object],
        state: AgentState,
    ) -> list[list[object]]:
        """Group agents that can run in parallel while preserving order."""
        if not agents:
            return []

        explicit_groups = state.metadata.get("parallel_agent_groups")
        if explicit_groups:
            return [
                [agent for agent in agents if agent.agent_name in group]
                for group in explicit_groups
                if any(agent.agent_name in group for agent in agents)
            ]

        default_groups = [
            ["PatientIntakeAgent", "MedicalReportAnalysisAgent"],
            ["DiseaseRiskAgent", "MedicalKnowledgeAgent", "DrugSafetyAgent"],
        ]

        groups: list[list[object]] = []
        for group_names in default_groups:
            matching_agents = [
                agent for agent in agents if agent.agent_name in group_names
            ]
            if matching_agents:
                groups.append(matching_agents)

        remaining_agents = [
            agent for agent in agents
            if not any(agent.agent_name == existing.agent_name for group in groups for existing in group)
        ]
        if len(remaining_agents) == 2:
            groups.append(remaining_agents)
        elif remaining_agents:
            groups.extend([[agent] for agent in remaining_agents])

        return groups

    def _merge_parallel_agent_state(
        self,
        state: AgentState,
        agent: object,
        agent_state: AgentState,
        result: AgentResult,
    ) -> None:
        """Merge a parallel agent's output into the shared workflow state."""
        state.record_agent_result(
            agent.agent_name,
            result.result,
            confidence=result.confidence,
            execution_time=result.processing_time,
        )

        for field_name in (
            "patient",
            "patient_history",
            "symptoms",
            "medications",
            "allergies",
            "uploaded_reports",
            "report_text",
            "ocr_result",
            "extracted_metrics",
            "disease_risk",
            "knowledge_results",
            "drug_analysis",
            "recommendations",
            "final_report",
        ):
            if not hasattr(agent_state, field_name):
                continue

            value = getattr(agent_state, field_name)
            if value in (None, "", [], {}, set()):
                continue

            setattr(state, field_name, copy.deepcopy(value))

        for trace in agent_state.execution_trace:
            if trace not in state.execution_trace:
                state.add_trace(trace)

        for warning in agent_state.warnings:
            if warning not in state.warnings:
                state.add_warning(warning)

        for error in agent_state.errors:
            if error not in state.errors:
                state.add_error(error)

    def _get_timeout_for_agent(self, state: AgentState, agent_name: str) -> float | None:
        """Return a configured timeout for an agent if one is provided."""
        timeouts = state.metadata.get("agent_timeouts", {})
        timeout_value = timeouts.get(agent_name)
        if timeout_value is None:
            return None
        try:
            return float(timeout_value)
        except (TypeError, ValueError):
            return None

    def _get_retry_backoff(
        self,
        state: AgentState,
        agent_name: str,
        attempt: int,
    ) -> float:
        """Return the retry delay for an agent, using exponential backoff."""
        backoff = state.metadata.get("retry_backoff")
        if backoff is None:
            return 0.0

        try:
            backoff_value = float(backoff)
        except (TypeError, ValueError):
            return 0.0

        if backoff_value <= 0:
            return 0.0

        per_agent = state.metadata.get("retry_backoffs", {})
        if agent_name in per_agent:
            try:
                configured = float(per_agent[agent_name])
            except (TypeError, ValueError):
                configured = backoff_value
            return configured * (2**attempt)

        return backoff_value * (2**attempt)

    def _is_agent_critical(self, agent_name: str, state: AgentState) -> bool:
        configured = set(state.metadata.get("critical_agents", []))
        return agent_name in configured or agent_name in self.critical_agents

    def register_fallback(self, agent_name: str, fallback_agent: BaseAgent) -> None:
        """Register a fallback agent for a primary agent."""
        self.fallback_agents[agent_name] = fallback_agent

    def _load_configured_fallbacks(self) -> None:
        """Load fallback mappings from configuration into the orchestrator."""
        for primary_agent_name, fallback_value in settings.AGENT_FALLBACK_MAPPINGS.items():
            if primary_agent_name in self.fallback_agents:
                self.logger.debug(
                    "Skipping configured fallback for %s; manual fallback already registered.",
                    primary_agent_name,
                )
                continue

            primary_agent = next(
                (agent for agent in self.agents if agent.agent_name == primary_agent_name),
                None,
            )
            if primary_agent is None:
                self.logger.warning(
                    "Configured fallback ignored: primary agent '%s' not registered.",
                    primary_agent_name,
                )
                continue

            fallback_agent = self._resolve_fallback_agent(fallback_value)
            if fallback_agent is None:
                self.logger.warning(
                    "Configured fallback ignored: could not resolve fallback '%s' for primary '%s'.",
                    fallback_value,
                    primary_agent_name,
                )
                continue

            self.fallback_agents[primary_agent_name] = fallback_agent
            self.logger.info(
                "Configured fallback: %s -> %s",
                primary_agent_name,
                fallback_agent.agent_name,
            )

    def _resolve_fallback_agent(self, fallback_value: str) -> BaseAgent | None:
        if isinstance(fallback_value, BaseAgent):
            return fallback_value

        fallback_agent = next(
            (agent for agent in self.agents if agent.agent_name == fallback_value),
            None,
        )
        if fallback_agent is not None:
            return fallback_agent

        if isinstance(fallback_value, str) and "." in fallback_value:
            try:
                import importlib

                module_name, class_name = fallback_value.rsplit(".", 1)
                module = importlib.import_module(module_name)
                fallback_class = getattr(module, class_name)
                if isinstance(fallback_class, type) and issubclass(fallback_class, BaseAgent):
                    return fallback_class()
            except Exception as exc:
                self.logger.warning(
                    "Error importing fallback agent %s: %s",
                    fallback_value,
                    exc,
                )

        return None

    def get_pipeline(self) -> list[str]:
        """
        Return the ordered workflow pipeline.
        """
        return [
            agent.agent_name
            for agent in self.agents
        ]


# Alias `SupervisorOrchestrator` removed; use `WorkflowOrchestrator`.