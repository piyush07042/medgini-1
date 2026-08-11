"""
Clinical Analysis API
"""

from __future__ import annotations

import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.agents.base.agent_state import AgentState
from app.core.deps import get_supervisor
from app.core.deps import get_db
from app.schemas.cdss import (
    AnalysisRequestSchema,
)
from app.schemas.common import ApiResponse
from app.services.report.report_service import get_patient_id_from_context, save_ai_report

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clinical",
    tags=["Clinical Decision Support"],
)


@router.post(
    "/analyze",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_clinical_case(
    request: AnalysisRequestSchema,
    supervisor=Depends(get_supervisor),
    db: Session = Depends(get_db),
):
    """
    Execute the complete MediGenie Supervisor workflow.
    """

    try:

        state = AgentState()

        state.patient = request.patient_context.model_dump()
        state.patient["name"] = state.patient.get("name", "")
        state.patient["age"] = state.patient.get("age", 0)
        state.patient["gender"] = state.patient.get("gender", "")

        if request.raw_report_text:
            state.raw_report_text = request.raw_report_text
            state.report_text = request.raw_report_text

        final_state, results, metrics = (
            await supervisor.run(state)
        )

        patient_id = get_patient_id_from_context(state.patient)
        if patient_id is not None:
            logger.info("Saving report...")
            logger.info("Patient ID: %s", patient_id)
            save_ai_report(db, patient_id, final_state)
        else:
            logger.info("Skipping report persistence: no patient_id found in clinical analysis patient_context.")

        return ApiResponse(
            message="Clinical analysis completed successfully.",
            data={
                "workflow_state": final_state,
                "agent_results": results,
                "metrics": metrics,
            },
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical workflow failed: {exc}",
        )