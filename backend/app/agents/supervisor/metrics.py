"""
Workflow Metrics
================

Collects execution metrics for the MediGenie multi-agent workflow.

Responsibilities
----------------
- Workflow timing
- Per-agent execution timing
- Success / failure counts
- Warning & error counts
- Execution summary

This module contains NO business logic.
"""

from __future__ import annotations

import time

from dataclasses import dataclass, field
from typing import Any

from app.agents.base.agent_result import AgentResult


@dataclass
class AgentExecutionMetric:
    """
    Metrics for one agent execution.
    """

    agent: str
    status: str
    processing_time: float
    confidence: float = 0.0
    warnings: int = 0
    error: str | None = None


@dataclass
class WorkflowMetrics:
    """
    Stores metrics for an entire workflow execution.
    """

    started_at: float = field(default_factory=time.perf_counter)
    finished_at: float | None = None

    agents: list[AgentExecutionMetric] = field(default_factory=list)

    total_agents: int = 0
    successful_agents: int = 0
    failed_agents: int = 0
    warning_count: int = 0
    error_count: int = 0

    def record(self, result: AgentResult) -> None:
        """
        Record metrics from a completed agent.
        """

        metric = AgentExecutionMetric(
            agent=result.agent,
            status=result.status,
            processing_time=result.processing_time,
            confidence=result.confidence,
            warnings=len(result.warnings),
            error=result.error,
        )

        self.agents.append(metric)

        self.total_agents += 1

        if result.success:
            self.successful_agents += 1
        else:
            self.failed_agents += 1

        self.warning_count += len(result.warnings)

        if result.error:
            self.error_count += 1

    def finish(self) -> None:
        """
        Mark workflow completion.
        """
        self.finished_at = time.perf_counter()

    @property
    def total_execution_time(self) -> float:
        """
        Total workflow execution time.
        """
        end = self.finished_at or time.perf_counter()
        return round(end - self.started_at, 4)

    @property
    def success_rate(self) -> float:
        """
        Percentage of successful agents.
        """
        if self.total_agents == 0:
            return 0.0

        return round(
            (self.successful_agents / self.total_agents) * 100,
            2,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize workflow metrics.
        """

        return {
            "total_execution_time": self.total_execution_time,
            "total_agents": self.total_agents,
            "successful_agents": self.successful_agents,
            "failed_agents": self.failed_agents,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "agents": [
                {
                    "agent": metric.agent,
                    "status": metric.status,
                    "processing_time": metric.processing_time,
                    "confidence": metric.confidence,
                    "warnings": metric.warnings,
                    "error": metric.error,
                }
                for metric in self.agents
            ],
        }