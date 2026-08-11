"""Model registry helpers for packaged disease models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODEL_ROOTS = [
    ROOT / "models",
    ROOT / "ml" / "models",
]


def resolve_model_directory(model_name: str) -> Path:
    """Resolve a model directory from known packaging roots."""
    for root in MODEL_ROOTS:
        candidate = root / model_name
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return (ROOT / "models" / model_name).resolve()


def get_model_registry() -> dict[str, Any]:
    """Return the known packaged model names."""
    registry: dict[str, Any] = {}
    for root in MODEL_ROOTS:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "model.joblib").exists():
                if child.name not in registry:
                    registry[child.name] = child.resolve()
    return registry
