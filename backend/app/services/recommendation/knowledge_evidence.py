from __future__ import annotations

from typing import Any


def build_citations_from_knowledge(knowledge_results: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []

    for entry in knowledge_results or []:
        if not isinstance(entry, dict):
            continue

        source = entry.get("metadata", {}).get("source") or entry.get("metadata", {}).get("title") or "Clinical guideline"
        identifier = entry.get("id") or entry.get("metadata", {}).get("id") or entry.get("metadata", {}).get("source")
        text = str(entry.get("document", "")).strip()
        score = entry.get("similarity_score")

        if not text:
            continue

        citations.append({
            "source": source,
            "identifier": identifier,
            "text": text,
            "similarity_score": score,
        })

    return citations


def summarize_evidence(knowledge_results: list[dict[str, Any]] | None) -> str:
    if not knowledge_results:
        return "No evidence was retrieved for the current clinical query."

    sources = []
    categories = []
    conditions = []

    for entry in knowledge_results or []:
        if not isinstance(entry, dict):
            continue
        metadata = entry.get("metadata", {}) or {}
        source = metadata.get("source") or metadata.get("title")
        category = metadata.get("category")
        document = str(entry.get("document", ""))

        if source and source not in sources:
            sources.append(source)
        if category and category not in categories:
            categories.append(category)
        if "hypertension" in document.lower() and "Hypertension" not in conditions:
            conditions.append("Hypertension")
        if "diabetes" in document.lower() and "Diabetes" not in conditions:
            conditions.append("Diabetes")
        if "fluoroquinolone" in document.lower() and "Drug Safety" not in conditions:
            conditions.append("Drug Safety")

    if not sources:
        return "No evidence was retrieved for the current clinical query."

    summary_parts = [f"Retrieved evidence from {', '.join(sources)}."]
    if categories:
        summary_parts.append(f"Covered categories: {', '.join(categories)}.")
    if conditions:
        summary_parts.append(f"Relevant topics include {', '.join(conditions)}.")

    return " ".join(summary_parts)
