"""
Report Generation Agent

Collects outputs from every previous agent
and prepares the final structured report.

This agent DOES NOT generate new medical claims.
It only summarizes validated outputs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.services.report.report_service import build_final_report


class ReportGenerationAgent(BaseAgent):

    agent_name = "ReportGenerationAgent"

    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:

        report = build_final_report(state)

        state.final_report = report

        state.set_agent_output(self.agent_name, report, confidence=1.0)

        return AgentResult(agent=self.agent_name, status="SUCCESS", confidence=1.0, result=report, metadata={"sections": len(report)})
