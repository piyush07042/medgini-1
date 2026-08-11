from datetime import datetime
from typing import Dict, Any


def create_fhir_bundle(patient_data: Dict[str, Any], cdss_output: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Converts internal patient records and CDSS predictions into an HL7 FHIR JSON Bundle.
    Uses official LOINC codes for standard medical metrics.
    """
    patient_id = str(patient_data.get("patient_id", "PT-UNKNOWN"))
    timestamp = datetime.utcnow().isoformat() + "Z"

    # 1. FHIR Patient Resource
    patient_resource = {
        "fullUrl": f"urn:uuid:patient-{patient_id}",
        "resource": {
            "resourceType": "Patient",
            "id": patient_id,
            "gender": str(patient_data.get("gender", "unknown")).lower(),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                    "valueInteger": int(patient_data.get("age", 0))
                }
            ]
        }
    }

    # 2. FHIR Observations mapped with standard LOINC codes
    observations = []
    metrics_map = [
        ("glucose", "2339-0", "Glucose [Mass/volume] in Blood", "mg/dL"),
        ("cholesterol", "2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "mg/dL"),
        ("systolic_bp", "8480-6", "Systolic blood pressure", "mmHg"),
        ("bmi", "39156-5", "Body mass index (BMI) [Ratio]", "kg/m2")
    ]

    for key, loinc_code, display_name, unit in metrics_map:
        if key in patient_data and patient_data[key] is not None:
            observations.append({
                "fullUrl": f"urn:uuid:observation-{key}-{patient_id}",
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": loinc_code,
                            "display": display_name
                        }]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "valueQuantity": {
                        "value": float(patient_data[key]),
                        "unit": unit
                    }
                }
            })

    # 3. Combine into HL7 FHIR Bundle Resource
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": timestamp,
        "entry": [patient_resource] + observations
    }

    return fhir_bundle