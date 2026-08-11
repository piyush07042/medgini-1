"""
Agent Registry
==============

Central registry for all MediGenie workflow agents.

This module defines the execution order for the workflow.
"""

from __future__ import annotations

from app.agents.base.base_agent import BaseAgent

from app.agents.intake.patient_intake_agent import PatientIntakeAgent
from app.agents.report_analysis.medical_report_analysis_agent import (
    MedicalReportAnalysisAgent,
)
from app.agents.risk.disease_risk_agent import DiseaseRiskAgent
from app.agents.knowledge.medical_knowledge_agent import (
    MedicalKnowledgeAgent,
)
from app.agents.drug_safety.drug_safety_agent import (
    DrugSafetyAgent,
)
from app.agents.recommendation.recommendation_agent import (
    RecommendationAgent,
)
from app.agents.report_generation.report_generation_agent import (
    ReportGenerationAgent,
)


def get_workflow_agents() -> list[BaseAgent]:
    """
    Return workflow agents in execution order.
    """

    return [
        PatientIntakeAgent(),
        MedicalReportAnalysisAgent(),
        DiseaseRiskAgent(),
        MedicalKnowledgeAgent(),
        DrugSafetyAgent(),
        RecommendationAgent(),
        ReportGenerationAgent(),
    ]