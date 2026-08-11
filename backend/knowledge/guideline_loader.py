import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

GUIDELINES_DIR = Path(__file__).resolve().parent / "guidelines"
_guideline_cache: Dict[str, List[Dict[str, Any]]] = {}

def load_guidelines(disease_key: str) -> List[Dict[str, Any]]:
    """
    Loads and caches structured guidelines JSON for a disease key.
    Normalizes disease key to match the directory structure.
    """
    normalized = disease_key.lower().replace(" ", "_")
    if "diabetes" in normalized:
        folder = "diabetes"
    elif "heart_failure" in normalized:
        folder = "heart_failure"
    elif "heart" in normalized or "cardio" in normalized:
        folder = "heart_disease"
    elif "kidney" in normalized or "renal" in normalized:
        folder = "kidney"
    elif "liver" in normalized or "hepatic" in normalized:
        folder = "liver"
    elif "breast" in normalized:
        folder = "breast_cancer"
    elif "stroke" in normalized:
        folder = "stroke"
    elif "parkinson" in normalized:
        folder = "parkinsons"
    elif "hepatitis" in normalized:
        folder = "hepatitis"
    else:
        logger.warning(f"Unknown disease guideline request: {disease_key}")
        return []

    if folder in _guideline_cache:
        return _guideline_cache[folder]

    file_path = GUIDELINES_DIR / folder / "guidelines.json"
    if not file_path.exists():
        logger.warning(f"Guideline file not found at: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _guideline_cache[folder] = data
            return data
    except Exception as e:
        logger.error(f"Error loading guidelines for {disease_key} from {file_path}: {e}")
        return []

def list_available_guidelines() -> List[Dict[str, Any]]:
    """
    Returns list of all available guidelines, their organization, and version.
    """
    summary = []
    folders = ["diabetes", "heart_disease", "kidney", "liver", "breast_cancer", "stroke", "heart_failure", "parkinsons", "hepatitis"]
    for folder in folders:
        file_path = GUIDELINES_DIR / folder / "guidelines.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        first = data[0]
                        summary.append({
                            "disease_key": folder,
                            "disease_name": first.get("disease", folder.replace("_", " ").title()),
                            "source": first.get("source"),
                            "organization": first.get("organization"),
                            "version": first.get("version"),
                            "sections_count": len(data)
                        })
            except Exception:
                pass
    return summary
