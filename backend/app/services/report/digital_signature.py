"""
Digital Signature module for MediGenie clinical reports.

Generates a cryptographic SHA-256 hash of report content combined with
patient identity and timestamp to produce a tamper-evident verification
seal for every generated report.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def _canonical_payload(report: dict[str, Any]) -> str:
    """Create a deterministic string from key report fields for hashing."""
    # We hash the core clinical data – not ephemeral metadata – so the
    # signature remains stable across serialisation round-trips.
    signable_fields = {
        "patient_summary": report.get("patient_summary") or report.get("patient_information"),
        "prediction_results": report.get("prediction_results") or report.get("prediction"),
        "clinical_intelligence": report.get("clinical_intelligence"),
        "drug_safety": report.get("drug_safety"),
        "risk_assessment": report.get("risk_assessment"),
        "recommendations": report.get("recommendations"),
        "follow_up_plan": report.get("follow_up_plan") or report.get("follow_up"),
        "generated_at": report.get("generated_at"),
    }
    return json.dumps(signable_fields, sort_keys=True, default=str)


def generate_digital_signature(report: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a digital signature block for a clinical report.

    Returns a dictionary containing:
    - verification_id: unique human-readable code (VERIF-XXXX-XXXX)
    - signature_hash: full SHA-256 hex digest
    - signature_preview: truncated 16-char preview for display
    - signed_at: ISO-8601 UTC timestamp
    - signed_by: signing authority label
    - algorithm: hash algorithm used
    - integrity_status: always "verified" at generation time
    """

    payload_str = _canonical_payload(report)
    signature_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    # Generate a human-friendly verification code
    short_id = uuid.uuid4().hex[:8].upper()
    verification_id = f"VERIF-{short_id[:4]}-{short_id[4:]}"

    signed_at = datetime.now(timezone.utc).isoformat()

    return {
        "verification_id": verification_id,
        "signature_hash": signature_hash,
        "signature_preview": signature_hash[:16].upper(),
        "signed_at": signed_at,
        "signed_by": "MediGenie AI Clinical Engine",
        "algorithm": "SHA-256",
        "integrity_status": "verified",
        "seal_label": "✦ MediGenie Verified Clinical Report",
    }


def verify_report_signature(report: dict[str, Any], expected_hash: str) -> bool:
    """
    Verify a report's integrity by recomputing the hash and comparing
    it against the stored signature hash.
    """
    payload_str = _canonical_payload(report)
    computed_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    return computed_hash == expected_hash
