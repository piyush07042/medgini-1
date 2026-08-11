"""
Agent Evaluator
===============
Per-agent evaluation framework for MediGenie AI workflow.

Captures per-run evaluation snapshots and computes:
- Quality score (from QualityScorer)
- Latency percentile rank across history
- Confidence drift vs rolling baseline
- Failure rate
- Composite evaluation score (0.0–1.0)

Provides agent leaderboard ranked by composite eval score.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.workflow.quality_scorer import quality_scorer

logger = logging.getLogger(__name__)

EVAL_DIR = Path(__file__).resolve().parents[3] / "evaluation" / "agent_evals"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_MAX = 100


@dataclass
class AgentEvalSnapshot:
    """Single evaluation snapshot for one agent execution."""
    agent_name: str
    run_id: str
    timestamp: str
    quality_score: float
    confidence: float
    latency_seconds: float
    latency_percentile: float       # 0.0–1.0, higher = slower
    confidence_drift: float         # deviation from rolling mean
    success: bool
    guardrail_passed: bool
    composite_score: float          # 0.0–1.0 aggregate
    grade: str                      # A / B / C / D / F


@dataclass
class AgentLeaderboardEntry:
    """Aggregated eval for leaderboard display."""
    agent_name: str
    runs: int
    mean_composite: float
    mean_quality: float
    mean_latency: float
    failure_rate: float
    guardrail_pass_rate: float
    rank: int = 0


class AgentEvaluator:
    """
    Evaluates agents after each execution and maintains a leaderboard.
    """

    def __init__(self) -> None:
        # Per-agent rolling history
        self._snapshots: dict[str, deque[AgentEvalSnapshot]] = defaultdict(
            lambda: deque(maxlen=HISTORY_MAX)
        )
        self._latency_history: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=HISTORY_MAX)
        )
        self._confidence_history: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=HISTORY_MAX)
        )
        self._run_counter = 0

    def evaluate(
        self,
        agent_name: str,
        output: Any,
        confidence: float,
        latency: float,
        success: bool,
        guardrail_passed: bool,
    ) -> AgentEvalSnapshot:
        """Evaluate one agent execution and record snapshot."""
        self._run_counter += 1
        run_id = f"{agent_name}-{self._run_counter}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Quality score
        quality_report = quality_scorer.score_response(agent_name, output, confidence)
        quality_score = quality_report.overall_score

        # Latency percentile
        self._latency_history[agent_name].append(latency)
        latency_percentile = self._compute_percentile(
            latency, list(self._latency_history[agent_name])
        )

        # Confidence drift
        self._confidence_history[agent_name].append(confidence)
        conf_history = list(self._confidence_history[agent_name])
        mean_conf = sum(conf_history) / len(conf_history) if conf_history else confidence
        confidence_drift = round(abs(confidence - mean_conf), 4)

        # Composite score
        composite = self._compute_composite(
            quality_score=quality_score,
            latency_percentile=latency_percentile,
            confidence_drift=confidence_drift,
            success=success,
            guardrail_passed=guardrail_passed,
        )

        grade = _grade(composite)

        snapshot = AgentEvalSnapshot(
            agent_name=agent_name,
            run_id=run_id,
            timestamp=timestamp,
            quality_score=quality_score,
            confidence=confidence,
            latency_seconds=round(latency, 4),
            latency_percentile=latency_percentile,
            confidence_drift=confidence_drift,
            success=success,
            guardrail_passed=guardrail_passed,
            composite_score=composite,
            grade=grade,
        )

        self._snapshots[agent_name].append(snapshot)
        self._persist_snapshot(snapshot)

        logger.debug(
            "AgentEvaluator[%s] run=%s composite=%.3f grade=%s",
            agent_name, run_id, composite, grade,
        )
        return snapshot

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    def get_leaderboard(self) -> list[AgentLeaderboardEntry]:
        """Return agents ranked by composite eval score (descending)."""
        entries = []
        for agent_name, snaps in self._snapshots.items():
            snap_list = list(snaps)
            if not snap_list:
                continue
            runs = len(snap_list)
            mean_composite = round(sum(s.composite_score for s in snap_list) / runs, 4)
            mean_quality = round(sum(s.quality_score for s in snap_list) / runs, 4)
            mean_latency = round(sum(s.latency_seconds for s in snap_list) / runs, 4)
            failure_rate = round(sum(1 for s in snap_list if not s.success) / runs, 4)
            guard_pass = round(sum(1 for s in snap_list if s.guardrail_passed) / runs, 4)
            entries.append(AgentLeaderboardEntry(
                agent_name=agent_name,
                runs=runs,
                mean_composite=mean_composite,
                mean_quality=mean_quality,
                mean_latency=mean_latency,
                failure_rate=failure_rate,
                guardrail_pass_rate=guard_pass,
            ))

        # Sort by composite desc, then by failure_rate asc
        entries.sort(key=lambda e: (-e.mean_composite, e.failure_rate))
        for i, e in enumerate(entries, start=1):
            e.rank = i

        return entries

    def get_snapshots(self, agent_name: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent evaluation snapshots for an agent."""
        snaps = list(self._snapshots.get(agent_name, []))[-limit:]
        return [self._snapshot_to_dict(s) for s in reversed(snaps)]

    def get_all_snapshots(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent snapshots across all agents."""
        all_snaps = []
        for snaps in self._snapshots.values():
            all_snaps.extend(list(snaps))
        all_snaps.sort(key=lambda s: s.timestamp, reverse=True)
        return [self._snapshot_to_dict(s) for s in all_snaps[:limit]]

    # ------------------------------------------------------------------
    # Composite Score Calculation
    # ------------------------------------------------------------------

    def _compute_composite(
        self,
        quality_score: float,
        latency_percentile: float,
        confidence_drift: float,
        success: bool,
        guardrail_passed: bool,
    ) -> float:
        """
        Composite = weighted sum of:
        - Quality      40%
        - Latency      20%  (lower latency percentile = faster = better)
        - Success      20%
        - Guardrails   10%
        - Drift        10%  (lower drift = better)
        """
        quality_contrib = quality_score * 0.40
        latency_contrib = (1.0 - latency_percentile) * 0.20  # Inverted: faster = higher
        success_contrib = (1.0 if success else 0.0) * 0.20
        guard_contrib = (1.0 if guardrail_passed else 0.0) * 0.10
        drift_contrib = max(0.0, 1.0 - confidence_drift * 2) * 0.10

        composite = quality_contrib + latency_contrib + success_contrib + guard_contrib + drift_contrib
        return round(min(1.0, max(0.0, composite)), 4)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _compute_percentile(self, value: float, history: list[float]) -> float:
        """Compute what percentile the value falls in (0 = fastest, 1 = slowest)."""
        if len(history) <= 1:
            return 0.5
        below = sum(1 for h in history if h <= value)
        return round(below / len(history), 4)

    def _persist_snapshot(self, snapshot: AgentEvalSnapshot) -> None:
        """Write snapshot to disk for persistence."""
        try:
            path = EVAL_DIR / f"{snapshot.agent_name}_evals.jsonl"
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(self._snapshot_to_dict(snapshot)) + "\n")
        except Exception as exc:
            logger.warning("Failed to persist eval snapshot: %s", exc)

    @staticmethod
    def _snapshot_to_dict(s: AgentEvalSnapshot) -> dict[str, Any]:
        return {
            "agent_name": s.agent_name,
            "run_id": s.run_id,
            "timestamp": s.timestamp,
            "quality_score": s.quality_score,
            "confidence": s.confidence,
            "latency_seconds": s.latency_seconds,
            "latency_percentile": s.latency_percentile,
            "confidence_drift": s.confidence_drift,
            "success": s.success,
            "guardrail_passed": s.guardrail_passed,
            "composite_score": s.composite_score,
            "grade": s.grade,
        }


def _grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    elif score >= 0.75:
        return "B"
    elif score >= 0.60:
        return "C"
    elif score >= 0.45:
        return "D"
    return "F"


# Singleton
agent_evaluator = AgentEvaluator()
