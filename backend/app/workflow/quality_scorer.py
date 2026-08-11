"""
Quality Scorer
==============
Multi-dimension response quality scoring for MediGenie AI agents.

Scoring Dimensions (each 0.0–0.25, total 0.0–1.0):
1. Completeness    — required output fields present
2. Confidence      — agent confidence reasonable and consistent
3. Medical Safety  — no toxic/dangerous keywords
4. Coherence       — structured data valid, no critical nulls

Maintains rolling history of quality scores per agent (last 100 runs).
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Keywords that should NEVER appear in agent output
TOXIC_KEYWORDS = [
    "ignore previous instructions",
    "pretend you are",
    "jailbreak",
    "you are now",
    "act as if",
    "disregard guidelines",
    "override",
    "forget the rules",
]

# Required fields per agent output category
REQUIRED_FIELDS_MAP: dict[str, list[str]] = {
    "RiskAssessmentAgent": ["disease", "risk_level", "confidence"],
    "MedicalKnowledgeAgent": ["results"],
    "DrugSafetyAgent": ["interactions"],
    "RecommendationAgent": ["recommendations"],
    "ReportGenerationAgent": ["summary"],
    "PatientIntakeAgent": ["patient"],
    "ReportAnalysisAgent": ["extracted_metrics"],
}


@dataclass
class QualityDimension:
    name: str
    score: float            # 0.0–0.25
    max_score: float = 0.25
    notes: list[str] = field(default_factory=list)


@dataclass
class QualityReport:
    agent_name: str
    overall_score: float        # 0.0–1.0
    grade: str                  # A / B / C / D / F
    dimensions: list[QualityDimension] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def grade_from_score(score: float) -> str:
        if score >= 0.90:
            return "A"
        elif score >= 0.75:
            return "B"
        elif score >= 0.60:
            return "C"
        elif score >= 0.45:
            return "D"
        return "F"


class QualityScorer:
    """
    Scores the quality of agent outputs across four dimensions.
    Maintains a rolling history of scores per agent (max 100 entries).
    """

    def __init__(self) -> None:
        # Rolling history: agent_name -> deque of (timestamp, score)
        self._history: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=100)
        )

    # ------------------------------------------------------------------
    # Main Scoring
    # ------------------------------------------------------------------

    def score_response(
        self,
        agent_name: str,
        output: Any,
        confidence: float = 0.0,
    ) -> QualityReport:
        """Score an agent's output across all four dimensions."""

        d1 = self._score_completeness(agent_name, output)
        d2 = self._score_confidence(agent_name, confidence)
        d3 = self._score_medical_safety(agent_name, output)
        d4 = self._score_coherence(agent_name, output)

        dimensions = [d1, d2, d3, d4]
        overall = round(sum(d.score for d in dimensions), 4)
        grade = QualityReport.grade_from_score(overall)

        suggestions = []
        for d in dimensions:
            if d.score < d.max_score * 0.7:
                suggestions.append(f"Improve {d.name}: {'; '.join(d.notes)}")

        report = QualityReport(
            agent_name=agent_name,
            overall_score=overall,
            grade=grade,
            dimensions=dimensions,
            suggestions=suggestions,
        )

        # Record to history
        self._history[agent_name].append({
            "timestamp": report.timestamp,
            "score": overall,
            "grade": grade,
        })

        return report

    # ------------------------------------------------------------------
    # Dimension 1 — Completeness
    # ------------------------------------------------------------------

    def _score_completeness(self, agent_name: str, output: Any) -> QualityDimension:
        required = REQUIRED_FIELDS_MAP.get(agent_name, [])
        if not required:
            return QualityDimension("completeness", 0.25, notes=["No required fields configured"])

        if output is None:
            return QualityDimension("completeness", 0.0, notes=["Output is None"])

        output_dict: dict[str, Any] = {}
        if isinstance(output, dict):
            output_dict = output
        elif hasattr(output, "__dict__"):
            output_dict = vars(output)
        else:
            # Try string contains
            output_str = str(output).lower()
            present = [f for f in required if f.lower() in output_str]
            ratio = len(present) / len(required)
            return QualityDimension(
                "completeness",
                round(ratio * 0.25, 4),
                notes=[f"Missing: {set(required) - set(present)}"] if len(present) < len(required) else [],
            )

        missing = [f for f in required if f not in output_dict or output_dict[f] is None]
        ratio = 1 - len(missing) / len(required)
        notes = [f"Missing fields: {missing}"] if missing else []
        return QualityDimension("completeness", round(ratio * 0.25, 4), notes=notes)

    # ------------------------------------------------------------------
    # Dimension 2 — Confidence Alignment
    # ------------------------------------------------------------------

    def _score_confidence(self, agent_name: str, confidence: float) -> QualityDimension:
        notes = []
        # Healthy range: 0.5 – 0.99
        if confidence < 0.1:
            score = 0.0
            notes.append("Confidence extremely low (< 0.10)")
        elif confidence < 0.3:
            score = 0.10
            notes.append("Confidence low (< 0.30)")
        elif confidence < 0.5:
            score = 0.15
            notes.append("Confidence moderate-low")
        elif confidence > 0.99:
            score = 0.18
            notes.append("Confidence suspiciously perfect (1.0)")
        else:
            score = 0.25

        # Compare with rolling history mean
        history = list(self._history.get(agent_name, []))
        if len(history) >= 5:
            mean_score = sum(h["score"] for h in history[-10:]) / min(10, len(history))
            drift = abs(confidence - mean_score)
            if drift > 0.4:
                score = max(score - 0.05, 0.0)
                notes.append(f"High confidence drift from history: {drift:.2f}")

        return QualityDimension("confidence_alignment", round(score, 4), notes=notes)

    # ------------------------------------------------------------------
    # Dimension 3 — Medical Safety
    # ------------------------------------------------------------------

    def _score_medical_safety(self, agent_name: str, output: Any) -> QualityDimension:
        output_str = json_safe_str(output).lower()
        violations = []
        for kw in TOXIC_KEYWORDS:
            if kw in output_str:
                violations.append(f"Toxic keyword detected: '{kw}'")

        # Contradiction detection: "take X" and "avoid X" for same drug
        take_matches = re.findall(r"take\s+(\w+)", output_str)
        avoid_matches = re.findall(r"avoid\s+(\w+)", output_str)
        contradictions = set(take_matches) & set(avoid_matches)
        if contradictions:
            violations.append(f"Contradictory drug advice: {contradictions}")

        if violations:
            return QualityDimension("medical_safety", 0.0, notes=violations)
        return QualityDimension("medical_safety", 0.25, notes=[])

    # ------------------------------------------------------------------
    # Dimension 4 — Coherence
    # ------------------------------------------------------------------

    def _score_coherence(self, agent_name: str, output: Any) -> QualityDimension:
        notes = []
        if output is None:
            return QualityDimension("coherence", 0.0, notes=["Output is None"])

        if isinstance(output, dict):
            empty_keys = [k for k, v in output.items() if v == "" or v == [] or v == {}]
            if len(empty_keys) > 3:
                notes.append(f"Many empty fields: {empty_keys[:5]}")
                return QualityDimension("coherence", 0.10, notes=notes)

            # Check for nested structure validity
            for k, v in output.items():
                if isinstance(v, str) and len(v) > 5000:
                    notes.append(f"Oversized text field '{k}' ({len(v)} chars)")

        elif isinstance(output, list):
            if len(output) == 0:
                return QualityDimension("coherence", 0.05, notes=["Empty list output"])

        output_str = json_safe_str(output)
        if len(output_str) < 10:
            return QualityDimension("coherence", 0.05, notes=["Output too short"])

        score = 0.25 if not notes else 0.15
        return QualityDimension("coherence", score, notes=notes)

    # ------------------------------------------------------------------
    # History & Aggregation
    # ------------------------------------------------------------------

    def get_history(self, agent_name: str) -> list[dict[str, Any]]:
        """Return rolling quality score history for an agent."""
        return list(self._history.get(agent_name, []))

    def get_agent_summary(self) -> list[dict[str, Any]]:
        """Return quality summary for all agents."""
        summaries = []
        for agent_name, history in self._history.items():
            scores = [h["score"] for h in history]
            if not scores:
                continue
            summaries.append({
                "agent": agent_name,
                "runs": len(scores),
                "mean_quality": round(sum(scores) / len(scores), 4),
                "min_quality": round(min(scores), 4),
                "max_quality": round(max(scores), 4),
                "last_grade": history[-1]["grade"] if history else "N/A",
                "last_timestamp": history[-1]["timestamp"] if history else None,
            })
        return sorted(summaries, key=lambda x: x["mean_quality"], reverse=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def json_safe_str(obj: Any) -> str:
    """Convert any object to a string for text analysis."""
    if isinstance(obj, str):
        return obj
    try:
        import json
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)


# Singleton
quality_scorer = QualityScorer()
