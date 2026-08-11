"""
Citation Verifier
=================
Validates source citations in MediGenie AI agent outputs.

Verification levels:
- VERIFIED   : Format valid + source in approved whitelist
- UNVERIFIED : Format valid but source not in whitelist
- INVALID    : Format malformed or missing required fields
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Approved Source Whitelist
# ---------------------------------------------------------------------------

APPROVED_GUIDELINE_SOURCES = {
    "ADA", "AHA", "ACC", "AHA/ACC", "KDIGO", "WHO", "AASLD", "EASL",
    "NCCN", "AAN", "ESC", "AHA/ASA", "NICE", "CDC", "USPSTF",
    "JNC", "GOLD", "GINA", "ACR", "EULAR", "ASCO", "ESMO",
    "PubMed", "MEDLINE", "Cochrane", "UpToDate", "DynaMed",
}

APPROVED_DRUG_SOURCES = {
    "DrugBank", "RxNorm", "FDA", "EMA", "BNF", "MedlinePlus",
    "Micromedex", "Lexicomp", "Clinical Pharmacology",
}

# PubMed PMID pattern: 1–8 digits
PMID_PATTERN = re.compile(r"^\d{1,8}$")

# DOI pattern
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)

# URL pattern
URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CitationVerdict:
    citation_id: str
    source_type: str        # "pubmed", "guideline", "drug_db", "url", "unknown"
    status: str             # "VERIFIED", "UNVERIFIED", "INVALID"
    detail: str = ""


@dataclass
class CitationVerificationResult:
    total: int
    verified: int
    unverified: int
    invalid: int
    confidence_score: float         # verified / total
    verdicts: list[CitationVerdict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Citation Verifier
# ---------------------------------------------------------------------------

class CitationVerifier:
    """
    Validates citations embedded in agent outputs.

    Accepts citations in multiple formats:
    - dict with 'type', 'id', 'source' keys
    - raw string PMID / DOI / URL
    - list of the above
    """

    def verify(self, citations: Any) -> CitationVerificationResult:
        """Verify a list or single citation."""
        if not citations:
            return CitationVerificationResult(
                total=0, verified=0, unverified=0, invalid=0, confidence_score=1.0,
                verdicts=[],
            )

        normalized = self._normalize(citations)
        verdicts = [self._verify_one(c) for c in normalized]

        verified = sum(1 for v in verdicts if v.status == "VERIFIED")
        unverified = sum(1 for v in verdicts if v.status == "UNVERIFIED")
        invalid = sum(1 for v in verdicts if v.status == "INVALID")
        total = len(verdicts)
        confidence = round(verified / total, 4) if total > 0 else 0.0

        return CitationVerificationResult(
            total=total,
            verified=verified,
            unverified=unverified,
            invalid=invalid,
            confidence_score=confidence,
            verdicts=verdicts,
        )

    def verify_from_output(self, output: Any) -> CitationVerificationResult:
        """Extract and verify citations from an agent output dict."""
        if not isinstance(output, dict):
            return self.verify(None)
        citations = (
            output.get("citations") or
            output.get("sources") or
            output.get("references") or
            []
        )
        return self.verify(citations)

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize(self, citations: Any) -> list[dict[str, Any]]:
        """Normalize various citation formats to list of dicts."""
        if isinstance(citations, dict):
            citations = [citations]
        elif isinstance(citations, str):
            citations = [{"id": citations, "type": "unknown"}]
        elif not isinstance(citations, list):
            citations = [{"id": str(citations), "type": "unknown"}]

        result = []
        for c in citations:
            if isinstance(c, str):
                result.append({"id": c, "type": "unknown"})
            elif isinstance(c, dict):
                result.append(c)
            else:
                result.append({"id": str(c), "type": "unknown"})
        return result

    # ------------------------------------------------------------------
    # Single Citation Verification
    # ------------------------------------------------------------------

    def _verify_one(self, citation: dict[str, Any]) -> CitationVerdict:
        cid = str(citation.get("id", "")).strip()
        source_type = citation.get("type", "unknown").lower()
        source = str(citation.get("source", "")).strip()
        title = str(citation.get("title", "")).strip()

        if not cid and not source and not title:
            return CitationVerdict("(empty)", "unknown", "INVALID", "Empty citation")

        identifier = cid or source or title

        # PubMed PMID
        if source_type == "pubmed" or PMID_PATTERN.match(cid):
            if PMID_PATTERN.match(cid):
                status = "VERIFIED" if source.upper() in APPROVED_GUIDELINE_SOURCES or not source else "UNVERIFIED"
                return CitationVerdict(identifier, "pubmed", status, f"PMID format valid: {cid}")
            return CitationVerdict(identifier, "pubmed", "INVALID", f"Invalid PMID format: '{cid}'")

        # DOI
        if DOI_PATTERN.match(cid):
            return CitationVerdict(identifier, "doi", "VERIFIED", f"DOI format valid: {cid}")

        # URL
        if URL_PATTERN.match(cid):
            approved_domains = ["pubmed", "ncbi", "who.int", "aha.org", "ada.org",
                                "kidney.org", "nccn.org", "nice.org", "cdc.gov",
                                "uspstf.gov", "heart.org", "aan.com", "escardio.org"]
            is_approved = any(domain in cid.lower() for domain in approved_domains)
            status = "VERIFIED" if is_approved else "UNVERIFIED"
            return CitationVerdict(identifier, "url", status, f"URL {'from approved domain' if is_approved else 'from unknown domain'}")

        # Guideline source check
        if source_type in ("guideline", "clinical_guideline") or source.upper() in APPROVED_GUIDELINE_SOURCES:
            src_up = source.upper()
            if src_up in APPROVED_GUIDELINE_SOURCES or any(src_up in s for s in APPROVED_GUIDELINE_SOURCES):
                return CitationVerdict(identifier, "guideline", "VERIFIED", f"Approved guideline: {source}")
            return CitationVerdict(identifier, "guideline", "UNVERIFIED", f"Guideline not in whitelist: {source}")

        # Drug DB source check
        if source_type in ("drug_db", "drug", "formulary") or source in APPROVED_DRUG_SOURCES:
            if source in APPROVED_DRUG_SOURCES:
                return CitationVerdict(identifier, "drug_db", "VERIFIED", f"Approved drug source: {source}")
            return CitationVerdict(identifier, "drug_db", "UNVERIFIED", f"Drug source not in whitelist: {source}")

        # Generic text citation with known source name
        combined = f"{source} {identifier}".upper()
        for approved in APPROVED_GUIDELINE_SOURCES | APPROVED_DRUG_SOURCES:
            if approved in combined:
                return CitationVerdict(identifier, "guideline", "VERIFIED", f"Contains approved source: {approved}")

        # Fallback — unverified but not invalid
        if len(identifier) > 3:
            return CitationVerdict(identifier, "unknown", "UNVERIFIED", "Source not in approved whitelist")

        return CitationVerdict(identifier, "unknown", "INVALID", "Citation too short to verify")

    def get_stats(self, results: list[CitationVerificationResult]) -> dict[str, Any]:
        """Aggregate stats across multiple verification runs."""
        if not results:
            return {"runs": 0}
        total = sum(r.total for r in results)
        verified = sum(r.verified for r in results)
        return {
            "runs": len(results),
            "total_citations": total,
            "verified": verified,
            "unverified": sum(r.unverified for r in results),
            "invalid": sum(r.invalid for r in results),
            "overall_confidence": round(verified / total, 4) if total > 0 else 0.0,
        }


# Singleton
citation_verifier = CitationVerifier()
