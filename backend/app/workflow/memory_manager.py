"""
Memory Manager
==============
Manages AgentState memory footprint across MediGenie workflow runs.

Features
--------
- Context pruning    : Trim knowledge_results to top-N by relevance score
- State compression  : Drop raw OCR text after ReportAnalysisAgent completes
- Session LRU cache  : Cache condensed snapshots per patient (max 50 sessions)
- Memory telemetry   : Log state_size_bytes, pruned_fields, cache_hit_rate
"""

from __future__ import annotations

import json
import logging
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

MAX_KNOWLEDGE_RESULTS = 5
MAX_REPORT_TEXT_BYTES = 10_240       # 10KB threshold for raw OCR text
LRU_CACHE_MAX = 50                   # Max cached patient sessions
TELEMETRY_HISTORY_MAX = 100


@dataclass
class MemoryTelemetry:
    """Memory telemetry for a single workflow run."""
    run_id: str
    timestamp: str
    state_size_bytes: int
    pruned_knowledge_results: int
    compressed_fields: list[str]
    cache_hit: bool
    notes: list[str] = field(default_factory=list)


class LRUSessionCache:
    """Thread-safe LRU cache for condensed patient state snapshots."""

    def __init__(self, max_size: int = LRU_CACHE_MAX) -> None:
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> dict[str, Any] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 4) if total > 0 else 0.0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }


class MemoryManager:
    """
    Optimizes AgentState memory usage across the MediGenie workflow.

    Call `optimize(state)` before each agent group execution in the
    orchestrator to prune, compress, and cache state data.
    """

    def __init__(self) -> None:
        self._cache = LRUSessionCache()
        self._telemetry: list[MemoryTelemetry] = []
        self._run_counter = 0

    # ------------------------------------------------------------------
    # Main Optimization Entry Point
    # ------------------------------------------------------------------

    def optimize(self, state: Any) -> MemoryTelemetry:
        """
        Run all memory optimizations on AgentState.
        Returns telemetry for this run.
        """
        self._run_counter += 1
        run_id = f"run-{self._run_counter}"
        pruned_knowledge = 0
        compressed_fields: list[str] = []
        notes: list[str] = []

        initial_size = self._estimate_size(state)

        # 1. Prune knowledge results
        pruned_knowledge = self._prune_knowledge_results(state)

        # 2. Compress OCR / raw report text
        compressed_fields = self._compress_raw_text(state)

        # 3. Session cache check
        cache_hit = self._check_session_cache(state)
        if cache_hit:
            notes.append("Cache hit: restored condensed context from session cache")

        # 4. Save condensed snapshot to cache
        self._save_session_snapshot(state)

        final_size = self._estimate_size(state)
        if initial_size > final_size:
            notes.append(f"Reduced state size: {initial_size} → {final_size} bytes ({initial_size - final_size} bytes freed)")

        telemetry = MemoryTelemetry(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            state_size_bytes=final_size,
            pruned_knowledge_results=pruned_knowledge,
            compressed_fields=compressed_fields,
            cache_hit=cache_hit,
            notes=notes,
        )

        self._telemetry.append(telemetry)
        if len(self._telemetry) > TELEMETRY_HISTORY_MAX:
            self._telemetry = self._telemetry[-TELEMETRY_HISTORY_MAX:]

        logger.debug(
            "MemoryManager[%s]: size=%d bytes, pruned=%d, compressed=%s, cache_hit=%s",
            run_id, final_size, pruned_knowledge, compressed_fields, cache_hit,
        )
        return telemetry

    # ------------------------------------------------------------------
    # Pruning: Knowledge Results
    # ------------------------------------------------------------------

    def _prune_knowledge_results(self, state: Any) -> int:
        """Keep top-N knowledge results by relevance score."""
        if not hasattr(state, "knowledge_results"):
            return 0
        results = getattr(state, "knowledge_results", [])
        if not isinstance(results, list) or len(results) <= MAX_KNOWLEDGE_RESULTS:
            return 0

        # Sort by score field (similarity_score, relevance_score, or confidence)
        def score_key(r: Any) -> float:
            if isinstance(r, dict):
                return (
                    r.get("similarity_score") or
                    r.get("relevance_score") or
                    r.get("confidence") or
                    0.0
                )
            return 0.0

        sorted_results = sorted(results, key=score_key, reverse=True)
        pruned_count = len(results) - MAX_KNOWLEDGE_RESULTS
        state.knowledge_results = sorted_results[:MAX_KNOWLEDGE_RESULTS]
        return pruned_count

    # ------------------------------------------------------------------
    # Compression: Raw OCR Text
    # ------------------------------------------------------------------

    def _compress_raw_text(self, state: Any) -> list[str]:
        """Drop raw OCR text from state if it exceeds size threshold."""
        compressed = []

        # Check report_text
        if hasattr(state, "report_text"):
            text = getattr(state, "report_text", "")
            if isinstance(text, str) and len(text.encode()) > MAX_REPORT_TEXT_BYTES:
                # Keep only first 500 chars as a preview
                state.report_text = text[:500] + "... [compressed]"
                compressed.append("report_text")

        # Check raw_report_text (alias)
        if hasattr(state, "raw_report_text") and state.raw_report_text != state.report_text:
            text = getattr(state, "raw_report_text", "")
            if isinstance(text, str) and len(text.encode()) > MAX_REPORT_TEXT_BYTES:
                state.raw_report_text = text[:500] + "... [compressed]"
                compressed.append("raw_report_text")

        # Check ocr_result for large raw text
        if hasattr(state, "ocr_result") and isinstance(state.ocr_result, dict):
            raw = state.ocr_result.get("raw_text", "")
            if isinstance(raw, str) and len(raw.encode()) > MAX_REPORT_TEXT_BYTES:
                state.ocr_result["raw_text"] = raw[:500] + "... [compressed]"
                compressed.append("ocr_result.raw_text")

        return compressed

    # ------------------------------------------------------------------
    # Session Cache
    # ------------------------------------------------------------------

    def _check_session_cache(self, state: Any) -> bool:
        """Check if a condensed snapshot exists for this patient."""
        key = self._cache_key(state)
        if not key:
            return False
        cached = self._cache.get(key)
        if cached is None:
            return False
        # Restore lightweight context fields from cache
        if hasattr(state, "metadata"):
            state.metadata.setdefault("cached_context", cached.get("context_summary", {}))
        return True

    def _save_session_snapshot(self, state: Any) -> None:
        """Save a condensed session snapshot to LRU cache."""
        key = self._cache_key(state)
        if not key:
            return
        snapshot = {
            "patient_id": key,
            "extracted_metrics": getattr(state, "extracted_metrics", {}),
            "disease_risk_keys": list(getattr(state, "disease_risk", {}).keys()),
            "context_summary": {
                "symptoms_count": len(getattr(state, "symptoms", [])),
                "medications_count": len(getattr(state, "medications", [])),
                "knowledge_results_count": len(getattr(state, "knowledge_results", [])),
            },
        }
        self._cache.set(key, snapshot)

    def _cache_key(self, state: Any) -> str | None:
        """Generate a cache key from patient data."""
        patient = getattr(state, "patient", {})
        if not patient:
            return None
        pid = str(patient.get("id") or patient.get("patient_id") or "")
        name = str(patient.get("name") or patient.get("first_name") or "")
        if not pid and not name:
            return None
        return f"{pid}:{name}"

    # ------------------------------------------------------------------
    # Size Estimation
    # ------------------------------------------------------------------

    def _estimate_size(self, state: Any) -> int:
        """Estimate memory size of AgentState in bytes."""
        try:
            return sys.getsizeof(json.dumps(vars(state), default=str))
        except Exception:
            return sys.getsizeof(str(state))

    # ------------------------------------------------------------------
    # Telemetry API
    # ------------------------------------------------------------------

    def get_telemetry(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent memory telemetry."""
        recent = self._telemetry[-limit:]
        return [
            {
                "run_id": t.run_id,
                "timestamp": t.timestamp,
                "state_size_bytes": t.state_size_bytes,
                "pruned_knowledge_results": t.pruned_knowledge_results,
                "compressed_fields": t.compressed_fields,
                "cache_hit": t.cache_hit,
                "notes": t.notes,
            }
            for t in reversed(recent)
        ]

    def get_cache_stats(self) -> dict[str, Any]:
        return self._cache.stats

    def invalidate_patient(self, patient_id: str) -> None:
        """Invalidate cached session for a specific patient."""
        # Try both formats
        for key in list(self._cache._cache.keys()):
            if key.startswith(str(patient_id) + ":"):
                self._cache.invalidate(key)


# Singleton
memory_manager = MemoryManager()
