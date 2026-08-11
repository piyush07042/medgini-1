"""
Base Agent for MediGenie

Every AI agent in the system must inherit from BaseAgent.

Responsibilities
----------------
- Standard execution lifecycle
- Logging
- Error handling
- Timing
- Validation
- Standard AgentResult generation
"""

from __future__ import annotations

import logging
import time

from abc import ABC, abstractmethod

from .agent_result import AgentResult
from .agent_state import AgentState

# Phase 8 — AI Workflow Improvements
try:
    from app.workflow.guardrails import guardrails
    from app.workflow.quality_scorer import quality_scorer
    from app.workflow.agent_evaluator import agent_evaluator
    _WORKFLOW_ENABLED = True
except ImportError:
    _WORKFLOW_ENABLED = False


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all MediGenie agents.
    """

    agent_name: str = "BaseAgent"

    def __init__(self):
        self.logger = logging.getLogger(self.agent_name)

    async def execute(self, state: AgentState) -> AgentResult:
        """
        Main execution wrapper.

        Handles:

        • timing
        • logging
        • exception handling
        • standard response
        """

        start = time.perf_counter()

        self.logger.info("%s started.", self.agent_name)

        try:

            self.validate(state)

            result = await self.run(state)

            elapsed = time.perf_counter() - start

            result.processing_time = round(elapsed, 4)

            state.add_trace(
                f"{self.agent_name} completed in {elapsed:.3f}s"
            )

            # --- Phase 8: Safety Guardrails ---
            if _WORKFLOW_ENABLED:
                guard_result = guardrails.validate(
                    self.agent_name, result.result, result.confidence
                )
                if not guard_result.passed:
                    result.guardrail_violations = guard_result.violation_summary
                    if guard_result.critical:
                        result.status = "GUARDRAIL_FAILED"
                        result.warnings.append(
                            f"Critical guardrail violation: {guard_result.violation_summary[0]}"
                        )
                    else:
                        for v in guard_result.violation_summary:
                            result.warnings.append(f"Guardrail: {v}")

                # --- Phase 8: Quality Scoring ---
                quality_report = quality_scorer.score_response(
                    self.agent_name, result.result, result.confidence
                )
                result.quality_score = quality_report.overall_score

                # --- Phase 8: Agent Evaluation ---
                snap = agent_evaluator.evaluate(
                    agent_name=self.agent_name,
                    output=result.result,
                    confidence=result.confidence,
                    latency=elapsed,
                    success=result.success,
                    guardrail_passed=guard_result.passed,
                )
                result.evaluation = {
                    "composite_score": snap.composite_score,
                    "grade": snap.grade,
                    "latency_percentile": snap.latency_percentile,
                    "confidence_drift": snap.confidence_drift,
                }

            self.logger.info(
                "%s completed in %.3fs",
                self.agent_name,
                elapsed,
            )

            return result

        except Exception as exc:

            elapsed = time.perf_counter() - start

            state.add_error(str(exc))

            self.logger.exception(
                "%s failed: %s",
                self.agent_name,
                exc,
            )

            return AgentResult(
                agent=self.agent_name,
                status="FAILED",
                confidence=0.0,
                result=None,
                error=str(exc),
                processing_time=round(elapsed, 4),
            )

    @abstractmethod
    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:
        """
        Business logic.

        Every child agent must implement this.
        """
        raise NotImplementedError

    def validate(self, state: AgentState):
        """
        Optional validation hook.

        Child agents may override.
        """
        return

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)