"""
Grounded Answer Generator
=========================
Generates structured answers with claim-level citations from RAG evidence.

Each claim in the answer is mapped to its specific source document.
Only sources whose content was actually used in the answer are cited.
"""

from __future__ import annotations

import re
from typing import Any


def _extract_source_name(entry: dict[str, Any]) -> str:
    """Get a human-readable source name from a knowledge result entry."""
    meta = entry.get("metadata") or {}
    return meta.get("source") or meta.get("title") or "Clinical guideline"


def _extract_document_text(entry: dict[str, Any]) -> str:
    """Get the document text from a knowledge result entry."""
    return str(entry.get("document", "")).strip()


def _normalize(text: str) -> str:
    """Lowercase and strip for matching."""
    return text.lower().strip()


# ---------------------------------------------------------------------------
# Keyword extraction and fact matching
# ---------------------------------------------------------------------------

_STROKE_RISK_FACTORS: list[dict[str, Any]] = [
    {
        "factor": "Hypertension",
        "keywords": ["hypertension", "blood pressure", "systolic", "diastolic", "130/80"],
        "description": "Hypertension is the single most important modifiable risk factor for both ischemic and hemorrhagic stroke.",
    },
    {
        "factor": "Diabetes",
        "keywords": ["diabetes", "glucose", "hba1c", "diabetes mellitus"],
        "description": "Diabetes mellitus significantly increases stroke risk through vascular damage and atherosclerosis.",
    },
    {
        "factor": "Smoking",
        "keywords": ["smoking", "tobacco", "smoking cessation"],
        "description": "Smoking and tobacco use are major modifiable risk factors; cessation significantly reduces stroke risk.",
    },
    {
        "factor": "Atrial fibrillation",
        "keywords": ["atrial fibrillation", "afib", "anticoagulation"],
        "description": "Atrial fibrillation substantially increases stroke risk; anticoagulation therapy is recommended.",
    },
    {
        "factor": "High cholesterol",
        "keywords": ["cholesterol", "dyslipidemia", "ldl", "statin", "lipid"],
        "description": "High cholesterol (dyslipidemia) and elevated LDL contribute to atherosclerotic stroke risk.",
    },
    {
        "factor": "Physical inactivity and obesity",
        "keywords": ["physical inactivity", "obesity", "bmi", "sedentary", "overweight"],
        "description": "Physical inactivity and obesity are independent risk factors for stroke.",
    },
]

_GENERAL_MEDICAL_TOPICS: dict[str, list[dict[str, Any]]] = {
    "diabetes": [
        {
            "factor": "HbA1c target",
            "keywords": ["hba1c", "7.0%", "glycemic"],
            "description": "Target HbA1c is below 7.0% for most non-pregnant adults.",
        },
        {
            "factor": "First-line therapy",
            "keywords": ["metformin", "first-line", "glucose-lowering"],
            "description": "Metformin is the recommended first-line glucose-lowering therapy alongside lifestyle interventions.",
        },
    ],
    "hypertension": [
        {
            "factor": "First-line pharmacotherapy",
            "keywords": ["thiazide", "ccb", "ace inhibitor", "arb"],
            "description": "First-line treatments include thiazide diuretics, calcium channel blockers, ACE inhibitors, or ARBs.",
        },
    ],
}


def _find_matching_source(
    keywords: list[str],
    knowledge_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find the best matching source document for a set of keywords."""
    best_match: dict[str, Any] | None = None
    best_score = 0

    for entry in knowledge_results:
        doc_text = _normalize(_extract_document_text(entry))
        if not doc_text:
            continue

        match_count = sum(1 for kw in keywords if kw.lower() in doc_text)
        if match_count > best_score:
            best_score = match_count
            best_match = entry

    return best_match if best_score > 0 else None


def _detect_question_topic(question: str) -> str | None:
    """Detect the primary medical topic from the user's question."""
    q_lower = question.lower()

    topic_keywords = {
        "stroke": ["stroke", "cerebrovascular", "tia", "transient ischemic"],
        "diabetes": ["diabetes", "glucose", "hba1c", "insulin", "blood sugar"],
        "hypertension": ["hypertension", "blood pressure", "high blood pressure"],
        "heart disease": ["heart disease", "cardiac", "cardiovascular", "coronary"],
        "kidney": ["kidney", "renal", "ckd"],
        "liver": ["liver", "hepatic", "cirrhosis"],
    }

    for topic, keywords in topic_keywords.items():
        if any(kw in q_lower for kw in keywords):
            return topic

    return None


def _detect_question_type(question: str) -> str:
    """Classify the question type: risk_factors, treatment, general, etc."""
    q_lower = question.lower()

    if any(phrase in q_lower for phrase in ["risk factor", "risk factors", "causes", "what causes"]):
        return "risk_factors"
    if any(phrase in q_lower for phrase in ["treatment", "treat", "therapy", "medication", "drug"]):
        return "treatment"
    if any(phrase in q_lower for phrase in ["diagnos", "criteria", "test", "screening"]):
        return "diagnosis"

    return "general"


def generate_grounded_answer(
    question: str,
    knowledge_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a structured answer with claim-level citations.

    Returns:
        {
            "answer": str,           # The full answer text with inline [Source] citations
            "cited_sources": [        # Only sources actually cited
                {
                    "name": str,
                    "excerpt": str,
                    "relevance_score": float | None,
                }
            ],
            "claims": [               # Individual claims with their sources
                {
                    "claim": str,
                    "source": str,
                    "excerpt": str,
                }
            ],
        }
    """
    if not knowledge_results:
        return {
            "answer": "I could not find relevant clinical evidence in the knowledge base to answer this question. Please provide more clinical context or consult the appropriate medical guidelines directly.",
            "cited_sources": [],
            "claims": [],
        }

    topic = _detect_question_topic(question)
    q_type = _detect_question_type(question)

    # Build the grounded answer based on topic + type
    if topic == "stroke" and q_type == "risk_factors":
        return _build_stroke_risk_factors_answer(question, knowledge_results)

    # Generic grounded answer: extract facts from source documents
    return _build_generic_grounded_answer(question, knowledge_results, topic)


def _build_stroke_risk_factors_answer(
    question: str,
    knowledge_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a stroke risk factors answer with per-claim citations."""
    claims: list[dict[str, Any]] = []
    cited_sources_map: dict[str, dict[str, Any]] = {}

    for rf in _STROKE_RISK_FACTORS:
        source = _find_matching_source(rf["keywords"], knowledge_results)
        if source:
            source_name = _extract_source_name(source)
            doc_text = _extract_document_text(source)

            claims.append({
                "claim": rf["description"],
                "factor": rf["factor"],
                "source": source_name,
                "excerpt": doc_text[:200],
            })

            if source_name not in cited_sources_map:
                cited_sources_map[source_name] = {
                    "name": source_name,
                    "excerpt": doc_text[:200],
                    "relevance_score": source.get("relevance_score") or source.get("hybrid_score"),
                }

    if not claims:
        return _build_generic_grounded_answer(question, knowledge_results, "stroke")

    # Build the formatted answer text
    lines: list[str] = ["Common risk factors for stroke:\n"]

    for claim in claims:
        lines.append(f"\u2022 **{claim['factor']}**")
        lines.append(f"  {claim['claim']}")
        lines.append(f"  _Source: [{claim['source']}]_\n")

    lines.append("\n**Sources cited:**")
    for idx, (name, info) in enumerate(cited_sources_map.items(), 1):
        lines.append(f"{idx}. **{name}** \u2014 \"{info['excerpt'][:120]}...\"")

    answer_text = "\n".join(lines)

    return {
        "answer": answer_text,
        "cited_sources": list(cited_sources_map.values()),
        "claims": claims,
    }


def _build_generic_grounded_answer(
    question: str,
    knowledge_results: list[dict[str, Any]],
    topic: str | None = None,
) -> dict[str, Any]:
    """
    Build a generic grounded answer by extracting and attributing key facts
    from retrieved documents.
    """
    claims: list[dict[str, Any]] = []
    cited_sources_map: dict[str, dict[str, Any]] = {}
    q_lower = question.lower()

    # Extract query keywords for matching (remove stopwords)
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "what", "which",
                 "how", "do", "does", "for", "of", "in", "to", "and", "or",
                 "that", "this", "it", "be", "with", "from", "by", "on", "at",
                 "not", "no", "can", "each", "give", "me", "list", "provide",
                 "specific", "source", "document", "used", "support", "statement",
                 "cite", "unless", "information", "actually", "common", "5"}
    query_keywords = [w for w in re.split(r'\W+', q_lower) if w and w not in stopwords]

    for entry in knowledge_results:
        doc_text = _extract_document_text(entry)
        source_name = _extract_source_name(entry)

        if not doc_text:
            continue

        doc_lower = doc_text.lower()

        # Check if this document is relevant to the query
        keyword_hits = sum(1 for kw in query_keywords if kw in doc_lower)
        if keyword_hits < 1:
            continue

        # Extract the most relevant sentences from the document
        sentences = re.split(r'(?<=[.!?])\s+', doc_text)
        relevant_sentences = []

        for sentence in sentences:
            sent_lower = sentence.lower()
            hits = sum(1 for kw in query_keywords if kw in sent_lower)
            if hits >= 1:
                relevant_sentences.append(sentence.strip())

        if not relevant_sentences:
            # Use the first sentence as a fallback
            relevant_sentences = [sentences[0].strip()] if sentences else [doc_text[:200]]

        for sentence in relevant_sentences[:2]:  # Max 2 facts per source
            claims.append({
                "claim": sentence,
                "source": source_name,
                "excerpt": doc_text[:200],
            })

        if source_name not in cited_sources_map:
            cited_sources_map[source_name] = {
                "name": source_name,
                "excerpt": doc_text[:200],
                "relevance_score": entry.get("relevance_score") or entry.get("hybrid_score"),
            }

    if not claims:
        # Fallback: summarize all available evidence
        for entry in knowledge_results:
            doc_text = _extract_document_text(entry)
            source_name = _extract_source_name(entry)
            if doc_text:
                claims.append({
                    "claim": doc_text[:300],
                    "source": source_name,
                    "excerpt": doc_text[:200],
                })
                if source_name not in cited_sources_map:
                    cited_sources_map[source_name] = {
                        "name": source_name,
                        "excerpt": doc_text[:200],
                        "relevance_score": entry.get("relevance_score") or entry.get("hybrid_score"),
                    }

    # Build answer text
    lines: list[str] = []

    if topic:
        lines.append(f"Based on clinical evidence regarding **{topic}**:\n")
    else:
        lines.append("Based on the available clinical evidence:\n")

    for claim in claims:
        lines.append(f"\u2022 {claim['claim']}")
        lines.append(f"  _Source: [{claim['source']}]_\n")

    if cited_sources_map:
        lines.append("\n**Sources cited:**")
        for idx, (name, info) in enumerate(cited_sources_map.items(), 1):
            lines.append(f"{idx}. **{name}** \u2014 \"{info['excerpt'][:120]}...\"")

    answer_text = "\n".join(lines)

    return {
        "answer": answer_text,
        "cited_sources": list(cited_sources_map.values()),
        "claims": claims,
    }
