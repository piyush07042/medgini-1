"""Compatibility FHIR service for the API layer."""

from __future__ import annotations

from typing import Any

from app.models.models import Patient


class FHIRService:
    """Build a minimal FHIR-like bundle payload for a patient."""

    def build_patient_bundle(self, patient: Patient) -> dict[str, Any]:
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": str(patient.id),
                        "name": [{"family": patient.last_name, "given": [patient.first_name]}],
                        "gender": patient.gender,
                    }
                }
            ],
        }
