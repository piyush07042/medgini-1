"""
Workflow response schemas.
"""

from typing import Any

from pydantic import BaseModel


class WorkflowResponse(BaseModel):

    workflow_status: str

    patient_context: dict[str, Any]

    agent_results: list[Any]

    metrics: dict[str, Any]

    report: dict[str, Any] | None = None