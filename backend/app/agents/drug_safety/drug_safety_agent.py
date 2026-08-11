"""
Drug Safety Agent

Responsibilities
----------------
1. Analyze patient medications.
2. Detect drug-drug interactions.
3. Detect allergy conflicts.
4. Store results into AgentState.
5. Return standardized AgentResult.
"""

from __future__ import annotations

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.core.notifications import send_drug_safety_alert
from app.services.drug_safety_service import get_drug_safety_service


class DrugSafetyAgent(BaseAgent):
    """
    Drug Safety Agent

    Uses the deterministic drug safety engine to detect:
    - Drug interactions
    - Allergy conflicts
    - Prescription warnings
    """

    agent_name = "DrugSafetyAgent"

    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:

        medications = state.medications or []
        if not medications:
            medications = (
                state.patient_context.get("current_medications")
                or state.patient.get("current_medications")
                or []
            )

        allergies = state.allergies or []
        if not allergies:
            allergies = (
                state.patient_context.get("allergies")
                or state.patient.get("allergies")
                or []
            )

        if isinstance(medications, str):
            medications = [medications]
        if isinstance(allergies, str):
            allergies = [allergies]

        service = get_drug_safety_service()
        result = service.analyze(
            medications=medications,
            patient_allergies=allergies,
            patient_context={
                **(state.patient or {}),
                **(state.patient_context or {}),
            },
        )

        assessment = result.get("drug_safety_assessment", {})
        warnings, evidence = service.build_agent_output(assessment)

        for warning_text in warnings:
            state.add_warning(warning_text)

        confidence = 1.0

        state.drug_analysis = assessment

        state.set_agent_output(
            self.agent_name,
            assessment,
            confidence=confidence,
        )

        # Notify external systems if the assessment is flagged
        try:
            if assessment.get("status") != "PASS":
                payload = {
                    "patient": state.patient or {},
                    "assessment": assessment,
                }
                send_drug_safety_alert(payload)
        except Exception:
            # non-fatal
            pass

        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=confidence,
            result=assessment,
            evidence=evidence,
            warnings=warnings,
            metadata={
                "medications_checked": len(medications),
                "allergies_checked": len(allergies),
                "status": assessment.get("status"),
            },
        )

    def validate(
        self,
        state: AgentState,
    ) -> None:
        """
        Validation hook.
        """
        return