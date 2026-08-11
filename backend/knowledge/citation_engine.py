from typing import Any, Dict, List

def format_citation(source: str, section: str, version: str) -> str:
    """
    Formats guideline source into standard citation format.
    """
    cite = f"{source} (v{version})"
    if section:
        cite += f", {section}"
    return cite

def build_citations(matched_guidelines: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts and formats citations from matched guidelines.
    """
    citations = []
    seen = set()
    for entry in matched_guidelines:
        source = entry.get("source", "")
        section = entry.get("section", "")
        version = entry.get("version", "")
        if source:
            cite_str = format_citation(source, section, version)
            if cite_str not in seen:
                seen.add(cite_str)
                citations.append(cite_str)
    return citations
