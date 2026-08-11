"""
Guardrails
==========
Safety guardrail system for all MediGenie AI agent outputs.

Six guard types:
1. Hallucination Guard   — checks drug names against known formulary
2. Dosage Safety Guard   — flags dosage values outside safe range
3. Contradiction Guard   — catches conflicting advice in same response
4. Empty Response Guard  — rejects null/empty critical outputs
5. Confidence Floor      — rejects outputs with confidence < 0.10
6. Citation Required     — requires citations for knowledge responses
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known Drug Formulary (subset — extended for production use)
# ---------------------------------------------------------------------------
KNOWN_DRUGS = {
    "metformin", "lisinopril", "atorvastatin", "amlodipine", "aspirin",
    "losartan", "omeprazole", "levothyroxine", "albuterol", "furosemide",
    "gabapentin", "sertraline", "metoprolol", "pantoprazole", "hydrochlorothiazide",
    "montelukast", "rosuvastatin", "escitalopram", "tramadol", "amoxicillin",
    "azithromycin", "ciprofloxacin", "warfarin", "clopidogrel", "insulin",
    "glipizide", "sitagliptin", "empagliflozin", "dapagliflozin", "canagliflozin",
    "spironolactone", "digoxin", "carvedilol", "bisoprolol", "ramipril",
    "enalapril", "valsartan", "irbesartan", "diltiazem", "verapamil",
    "nifedipine", "nitrates", "isosorbide", "acetaminophen", "ibuprofen",
    "naproxen", "prednisone", "dexamethasone", "prednisolone", "colchicine",
    "allopurinol", "febuxostat", "hydroxychloroquine", "methotrexate",
    "adalimumab", "etanercept", "infliximab", "rituximab", "trastuzumab",
    "tamoxifen", "letrozole", "anastrozole", "leuprolide", "bicalutamide",
    "carboplatin", "cisplatin", "paclitaxel", "docetaxel", "vincristine",
    "cyclophosphamide", "doxorubicin", "fluorouracil", "capecitabine",
    "pembrolizumab", "nivolumab", "ipilimumab", "bevacizumab", "cetuximab",
    "heparin", "enoxaparin", "apixaban", "rivaroxaban", "dabigatran",
    "levetiracetam", "valproate", "lamotrigine", "carbamazepine", "phenytoin",
    "donepezil", "memantine", "rivastigmine", "galantamine",
    "haloperidol", "risperidone", "olanzapine", "quetiapine", "aripiprazole",
    "fluoxetine", "paroxetine", "venlafaxine", "duloxetine", "bupropion",
    "clonazepam", "diazepam", "lorazepam", "alprazolam", "zolpidem",
}

# Dosage pattern: number + unit (mg, mcg, g, units)
DOSAGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|units?|iu|ml)", re.IGNORECASE)

# Safe dosage upper bounds (mg) — rough clinical thresholds
DOSAGE_LIMITS: dict[str, float] = {
    "mg": 5000.0,
    "mcg": 1000.0,
    "g": 5.0,
    "ml": 500.0,
}

# Knowledge agents requiring citations
KNOWLEDGE_AGENTS = {"MedicalKnowledgeAgent", "RecommendationAgent"}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class GuardrailViolation:
    guard: str
    severity: str           # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    message: str
    detail: str = ""


@dataclass
class GuardrailResult:
    agent_name: str
    passed: bool
    violations: list[GuardrailViolation] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def critical(self) -> bool:
        return any(v.severity == "CRITICAL" for v in self.violations)

    @property
    def violation_summary(self) -> list[str]:
        return [f"[{v.severity}] {v.guard}: {v.message}" for v in self.violations]


# ---------------------------------------------------------------------------
# Guardrails Engine
# ---------------------------------------------------------------------------

class Guardrails:
    """
    Safety guardrail validation for all MediGenie agent outputs.
    Maintains a rolling violation log (last 500 entries).
    """

    def __init__(self) -> None:
        self._violation_log: list[dict[str, Any]] = []

    def validate(
        self,
        agent_name: str,
        output: Any,
        confidence: float = 0.0,
    ) -> GuardrailResult:
        """Run all guardrails for an agent output."""
        violations: list[GuardrailViolation] = []
        output_str = _to_str(output)

        # Guard 1 — Hallucination (drug name check)
        violations.extend(self._hallucination_guard(output_str))

        # Guard 2 — Dosage Safety
        violations.extend(self._dosage_safety_guard(output_str))

        # Guard 3 — Contradictory Advice
        violations.extend(self._contradiction_guard(output_str))

        # Guard 4 — Empty Response
        violations.extend(self._empty_response_guard(agent_name, output))

        # Guard 5 — Confidence Floor
        violations.extend(self._confidence_floor_guard(agent_name, confidence))

        # Guard 6 — Citation Required
        if agent_name in KNOWLEDGE_AGENTS:
            violations.extend(self._citation_required_guard(output_str, output))

        passed = all(v.severity not in ("HIGH", "CRITICAL") for v in violations)
        result = GuardrailResult(
            agent_name=agent_name,
            passed=passed,
            violations=violations,
        )

        # Log violations
        if violations:
            entry = {
                "timestamp": result.timestamp,
                "agent": agent_name,
                "passed": passed,
                "violations": [{"guard": v.guard, "severity": v.severity, "message": v.message}
                               for v in violations],
            }
            self._violation_log.append(entry)
            if len(self._violation_log) > 500:
                self._violation_log = self._violation_log[-500:]

        return result

    # ------------------------------------------------------------------
    # Guard 1: Hallucination — unknown drug names
    # ------------------------------------------------------------------

    def _hallucination_guard(self, output_str: str) -> list[GuardrailViolation]:
        """Detect drug names in output not present in known formulary."""
        violations = []
        # Look for patterns like "prescribe X" or "administer X" or "take X"
        suspicious_patterns = re.findall(
            r"(?:prescribe|administer|take|start|initiate|give)\s+([A-Za-z]+)",
            output_str, re.IGNORECASE
        )
        unknowns = []
        for drug_candidate in suspicious_patterns:
            if drug_candidate.lower() not in KNOWN_DRUGS and len(drug_candidate) > 4:
                unknowns.append(drug_candidate)
        if len(unknowns) > 3:  # Threshold to avoid false positives
            violations.append(GuardrailViolation(
                guard="HallucinationGuard",
                severity="MEDIUM",
                message=f"Output references {len(unknowns)} potential unknown drug(s)",
                detail=f"Unrecognized: {unknowns[:5]}",
            ))
        return violations

    # ------------------------------------------------------------------
    # Guard 2: Dosage Safety
    # ------------------------------------------------------------------

    def _dosage_safety_guard(self, output_str: str) -> list[GuardrailViolation]:
        violations = []
        matches = DOSAGE_PATTERN.findall(output_str)
        for value_str, unit in matches:
            try:
                value = float(value_str)
                limit = DOSAGE_LIMITS.get(unit.lower().rstrip("s"), 5000.0)
                if value > limit:
                    violations.append(GuardrailViolation(
                        guard="DosageSafetyGuard",
                        severity="HIGH",
                        message=f"Potentially unsafe dosage: {value}{unit} (limit: {limit}{unit})",
                    ))
            except ValueError:
                pass
        return violations

    # ------------------------------------------------------------------
    # Guard 3: Contradictory Advice
    # ------------------------------------------------------------------

    def _contradiction_guard(self, output_str: str) -> list[GuardrailViolation]:
        violations = []
        output_lower = output_str.lower()
        take_drugs = set(re.findall(r"(?:take|use|start|prescribe)\s+(\w{4,})", output_lower))
        avoid_drugs = set(re.findall(r"(?:avoid|stop|contraindicated|do not use)\s+(\w{4,})", output_lower))
        contradictions = take_drugs & avoid_drugs
        if contradictions:
            violations.append(GuardrailViolation(
                guard="ContradictionGuard",
                severity="HIGH",
                message=f"Contradictory advice for: {list(contradictions)[:3]}",
                detail="Same drug recommended and contraindicated simultaneously",
            ))
        return violations

    # ------------------------------------------------------------------
    # Guard 4: Empty Response
    # ------------------------------------------------------------------

    def _empty_response_guard(self, agent_name: str, output: Any) -> list[GuardrailViolation]:
        if output is None:
            return [GuardrailViolation(
                guard="EmptyResponseGuard",
                severity="CRITICAL",
                message="Agent returned None output",
            )]
        output_str = _to_str(output)
        if len(output_str.strip()) < 5:
            return [GuardrailViolation(
                guard="EmptyResponseGuard",
                severity="CRITICAL",
                message="Agent returned nearly empty output",
                detail=f"Output length: {len(output_str)}",
            )]
        return []

    # ------------------------------------------------------------------
    # Guard 5: Confidence Floor
    # ------------------------------------------------------------------

    def _confidence_floor_guard(self, agent_name: str, confidence: float) -> list[GuardrailViolation]:
        if confidence < 0.10:
            return [GuardrailViolation(
                guard="ConfidenceFloorGuard",
                severity="HIGH",
                message=f"Confidence below floor: {confidence:.3f} < 0.10",
                detail="Output may be unreliable",
            )]
        return []

    # ------------------------------------------------------------------
    # Guard 6: Citation Required
    # ------------------------------------------------------------------

    def _citation_required_guard(self, output_str: str, output: Any) -> list[GuardrailViolation]:
        has_citation = False
        # Check for citation markers
        if any(kw in output_str.lower() for kw in ["source:", "reference:", "doi:", "pmid:", "pubmed", "guideline"]):
            has_citation = True
        if isinstance(output, dict):
            if output.get("citations") or output.get("sources") or output.get("references"):
                has_citation = True
        if not has_citation:
            return [GuardrailViolation(
                guard="CitationRequiredGuard",
                severity="MEDIUM",
                message="Knowledge agent output missing source citations",
                detail="Evidence-based responses must include citations",
            )]
        return []

    # ------------------------------------------------------------------
    # Violation Log
    # ------------------------------------------------------------------

    def get_violation_log(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent guardrail violations."""
        return list(reversed(self._violation_log[-limit:]))

    def get_stats(self) -> dict[str, Any]:
        """Return violation statistics."""
        if not self._violation_log:
            return {"total_checks": 0, "total_violations": 0, "passed_rate": 1.0}
        passed = sum(1 for e in self._violation_log if e["passed"])
        return {
            "total_checks": len(self._violation_log),
            "total_violations": sum(len(e["violations"]) for e in self._violation_log),
            "passed_rate": round(passed / len(self._violation_log), 4),
        }


def _to_str(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)


# Singleton
guardrails = Guardrails()
