"""
Central API Router

Registers all API modules for MediGenie.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.chat import router as chat_router
from app.api.settings import router as settings_router
from app.api.clinical import router as clinical_router
from app.api.diagnostics import router as diagnostics_router
from app.api.drug_safety import router as drug_safety_router
from app.api.endpoints import router as endpoints_router
from app.api.fhir import router as fhir_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.model_registry import router as model_registry_router
from app.api.metrics import router as metrics_router
from app.api.patients import router as patients_router
from app.api.reporting import router as reporting_router
from app.api.upload import router as upload_router
from app.api.version import router as version_router
from app.api.v1.heart_disease import router as heart_disease_router
from app.api.v1.heart_failure import router as heart_failure_router
from app.api.v1.diabetes import router as diabetes_router
from app.api.v1.kidney_disease import router as kidney_disease_router
from app.api.v1.liver import router as liver_router
from app.api.v1.breast_cancer import router as breast_cancer_router
from app.api.v1.parkinsons import router as parkinsons_router
from app.api.v1.hepatitis import router as hepatitis_router
from app.api.v1.stroke import router as stroke_router
from app.api.guidelines import router as guidelines_router
from app.api.multi_disease import router as multi_disease_router
from app.api.workflow import router as workflow_router

api_router = APIRouter()



# =====================================================
# Authentication
# =====================================================

api_router.include_router(
    auth_router,
)

# =====================================================
# Patient Management
# =====================================================

api_router.include_router(patients_router)
api_router.include_router(dashboard_router)

# =====================================================
# Clinical Decision Support
# =====================================================
 
api_router.include_router(clinical_router)
api_router.include_router(guidelines_router)
api_router.include_router(multi_disease_router)
api_router.include_router(workflow_router)



# =====================================================
# Medical Report Upload
# =====================================================

api_router.include_router(upload_router)

# =====================================================
# Clinical Reporting
# =====================================================

api_router.include_router(reporting_router)

# =====================================================
# Drug Safety API
# =====================================================
api_router.include_router(drug_safety_router)

# =====================================================
# Knowledge / RAG indexing
# =====================================================
api_router.include_router(knowledge_router)

# =====================================================
# FHIR Export
# =====================================================

api_router.include_router(fhir_router)

# =====================================================
# AI Clinical Chat
# =====================================================

api_router.include_router(chat_router)
api_router.include_router(settings_router)

# =====================================================
# Health & Monitoring
# =====================================================

api_router.include_router(
    health_router,
)
api_router.include_router(
    metrics_router,
)

# =====================================================
# Model Package Registry
# =====================================================

api_router.include_router(model_registry_router)

api_router.include_router(
    version_router,
)
api_router.include_router(heart_disease_router)
api_router.include_router(heart_failure_router)
api_router.include_router(diabetes_router)
api_router.include_router(kidney_disease_router)
api_router.include_router(liver_router)
api_router.include_router(breast_cancer_router)
api_router.include_router(parkinsons_router)
api_router.include_router(hepatitis_router)
api_router.include_router(stroke_router)
api_router.include_router(diagnostics_router, prefix="/diagnostics")

from evaluation.routes import router as evaluation_router

api_router.include_router(evaluation_router)

# =====================================================
# Miscellaneous / General Endpoints
# =====================================================

api_router.include_router(
    endpoints_router,
    tags=["General"],
)