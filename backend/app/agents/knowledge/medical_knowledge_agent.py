"""
Medical Knowledge Agent

Responsibilities
----------------
1. Build a disease-specific search query from the patient context.
2. Retrieve evidence from the ChromaDB knowledge base.
3. Re-rank results by combined similarity + disease-relevance boost.
4. Deduplicate and attach rank + supporting references.
5. Store retrieved evidence into AgentState.
6. Return standardized AgentResult.
"""

from __future__ import annotations

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.core.rag import (
    seed_sample_guidelines,
    query_knowledge_base,
)

# Disease keywords used to boost relevance of matching documents
_DISEASE_KEYWORDS: dict[str, list[str]] = {
    "diabetes": ["diabetes", "glucose", "hba1c", "insulin", "metformin", "ada", "glycemic"],
    "heart disease": ["heart", "cardiac", "cardiovascular", "coronary", "aha", "acc", "ecg", "troponin"],
    "stroke": ["stroke", "tpa", "thrombolysis", "ischemic", "hemorrhagic", "nihss", "asa"],
    "kidney disease": ["kidney", "renal", "ckd", "egfr", "creatinine", "dialysis", "kdigo"],
    "liver disease": ["liver", "hepatic", "cirrhosis", "alt", "ast", "bilirubin", "aasld"],
    "breast cancer": ["breast", "cancer", "mammogram", "biopsy", "nccn", "oncology"],
    "parkinson": ["parkinson", "dopamine", "levodopa", "aan", "tremor", "motor"],
    "hepatitis": ["hepatitis", "hbsag", "hcv", "viral", "liver", "aasld"],
    "thyroid": ["thyroid", "tsh", "hypothyroid", "hyperthyroid", "levothyroxine"],
    "hypertension": ["hypertension", "blood pressure", "systolic", "diastolic", "antihypertensive"],
}


def _compute_relevance_boost(document_text: str, disease: str | None) -> float:
    """Return 0.0–0.3 relevance boost based on disease-keyword overlap in the document."""
    if not disease:
        return 0.0
    disease_lower = disease.lower()
    # Find best matching keyword group
    keywords: list[str] = []
    for key, kws in _DISEASE_KEYWORDS.items():
        if key in disease_lower or disease_lower in key:
            keywords = kws
            break
    if not keywords:
        return 0.0
    doc_lower = document_text.lower()
    matched = sum(1 for kw in keywords if kw in doc_lower)
    return min(0.3, matched * 0.06)


def _apply_hallucination_guardrails(documents: list[dict], patient_context: dict) -> tuple[list[dict], list[str]]:
    """
    Hallucination Guardrail: Validates retrieved evidence against patient context
    and filters out ungrounded or conflicting snippets.
    Returns (filtered_documents, warnings).
    """
    filtered = []
    guardrail_warnings = []
    allergies = [str(a).lower() for a in (patient_context.get("allergies") or [])]
    
    for entry in documents:
        doc_text = str(entry.get("document", "")).lower()
        
        # Check 1: Allergy conflict check
        conflict_found = False
        for allergen in allergies:
            if allergen in doc_text and ("indicated" in doc_text or "first-line" in doc_text):
                guardrail_warnings.append(f"Guardrail Flagged: Document contains potential allergen conflict ({allergen}).")
                conflict_found = True
                break
        
        if conflict_found:
            continue
            
        # Check 2: Low-relevance grounding check (similarity score < 0.2)
        sim_score = entry.get("similarity_score")
        if isinstance(sim_score, (int, float)) and sim_score < 0.2:
            guardrail_warnings.append("Guardrail Flagged: Low semantic similarity snippet excluded.")
            continue
            
        filtered.append(entry)

    return filtered if filtered else documents, guardrail_warnings


class MedicalKnowledgeAgent(BaseAgent):
    """
    Retrieves evidence from the medical knowledge base (RAG).
    Applies disease-specific re-ranking, hybrid search, hallucination guardrails, and dynamic confidence scoring.
    """

    agent_name = "MedicalKnowledgeAgent"

    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:

        # -----------------------------------------------------
        # Ensure knowledge base is initialized
        # -----------------------------------------------------
        seed_sample_guidelines()

        # -----------------------------------------------------
        # Detect primary disease from state
        # -----------------------------------------------------
        disease: str | None = (
            (state.disease_risk or {}).get("disease")
            or (state.disease_risk or {}).get("condition")
            or (state.disease_risk or {}).get("label")
            or (state.disease_risk or {}).get("prediction")
            or (state.disease_risk or {}).get("risk_category")
        )

        # -----------------------------------------------------
        # Build query from patient context
        # -----------------------------------------------------
        query_parts: list[str] = []

        if disease:
            query_parts.append(str(disease))

        if state.symptoms:
            query_parts.extend(state.symptoms)

        if state.disease_risk:
            risk = state.disease_risk.get("condition") or state.disease_risk.get("evaluated_condition")
            category = state.disease_risk.get("risk_category")
            if risk and risk not in query_parts:
                query_parts.append(risk)
            if category and category not in query_parts:
                query_parts.append(category)

        if state.extracted_metrics:
            glucose = state.extracted_metrics.get("glucose")
            if glucose is not None and glucose >= 126:
                if "Diabetes" not in query_parts:
                    query_parts.append("Diabetes")
            systolic = state.extracted_metrics.get("systolic_bp")
            if systolic is not None and systolic >= 140:
                if "Hypertension" not in query_parts:
                    query_parts.append("Hypertension")

        diagnosis = getattr(state, "diagnosis", None) or state.patient.get("diagnosis")
        if diagnosis and str(diagnosis) not in query_parts:
            query_parts.append(str(diagnosis))

        if not query_parts:
            query_parts.append("General Clinical Guidelines")

        query = " ".join(query_parts)

        # -----------------------------------------------------
        # Query RAG with Hybrid Search
        # -----------------------------------------------------
        documents = query_knowledge_base(
            query_text=query,
            n_results=5,  # retrieve more so re-ranking can select best
        )

        knowledge: list[dict] = []
        citations: list[dict] = []
        evidence: list[str] = []

        for document in documents:
            if isinstance(document, dict):
                doc_text = str(document.get("document", ""))
                metadata = document.get("metadata", {}) or {}
                raw_id = document.get("id")
                similarity_score = document.get("similarity_score")
                hybrid_score = document.get("hybrid_score")
            else:
                doc_text = str(document)
                metadata = {}
                raw_id = None
                similarity_score = None
                hybrid_score = None

            entry = {
                "id": raw_id,
                "document": doc_text,
                "metadata": metadata,
                "similarity_score": similarity_score,
                "hybrid_score": hybrid_score,
            }
            knowledge.append(entry)

            if doc_text:
                evidence.append(doc_text[:200])

            citations.append({
                "source": metadata.get("source") or metadata.get("title") or "Clinical guideline",
                "identifier": metadata.get("id") or metadata.get("source") or "",
                "text": doc_text,
                "similarity_score": similarity_score,
                "hybrid_score": hybrid_score,
            })

        # -----------------------------------------------------
        # Deduplicate
        # -----------------------------------------------------
        unique_knowledge: list[dict] = []
        seen_docs: set[tuple[str, str]] = set()
        for entry in knowledge:
            doc_text = str(entry.get("document", "") or "").strip()
            identifier = entry.get("metadata", {}).get("id") or entry.get("metadata", {}).get("source") or ""
            key = (str(identifier), doc_text)
            if key not in seen_docs and doc_text:
                seen_docs.add(key)
                unique_knowledge.append(entry)

        # -----------------------------------------------------
        # Hallucination Guardrails Filter
        # -----------------------------------------------------
        patient_ctx = state.patient if isinstance(state.patient, dict) else {}
        unique_knowledge, guardrail_warnings = _apply_hallucination_guardrails(unique_knowledge, patient_ctx)
        for w in guardrail_warnings:
            state.add_warning(w)

        # -----------------------------------------------------
        # Disease-relevance re-ranking
        # -----------------------------------------------------
        for entry in unique_knowledge:
            base_score = float(entry.get("hybrid_score") or entry.get("similarity_score") or 0.0)
            boost = _compute_relevance_boost(str(entry.get("document", "")), disease)
            entry["relevance_score"] = round(base_score + boost, 4)

        unique_knowledge.sort(key=lambda e: e.get("relevance_score", 0.0), reverse=True)

        # Add rank and build references
        references: list[dict] = []
        for rank, entry in enumerate(unique_knowledge, start=1):
            entry["rank"] = rank
            meta = entry.get("metadata") or {}
            src = meta.get("source") or meta.get("title") or "Clinical guideline"
            references.append({
                "rank": rank,
                "source": src,
                "excerpt": str(entry.get("document", ""))[:200],
                "similarity_score": entry.get("similarity_score"),
                "hybrid_score": entry.get("hybrid_score"),
                "relevance_score": entry.get("relevance_score"),
            })

        # Keep only top 3 after re-ranking
        unique_knowledge = unique_knowledge[:3]
        references = references[:3]

        if not unique_knowledge:
            state.add_warning("No knowledge evidence was retrieved for the current query.")

        # Compute dynamic RAG confidence score based on top relevance scores
        scores = [e.get("relevance_score", 0.0) for e in unique_knowledge]
        avg_score = sum(scores) / len(scores) if scores else 0.5
        rag_confidence = round(min(0.98, max(0.50, avg_score + 0.3)), 2)

        state.knowledge_results = unique_knowledge

        state.set_agent_output(
            self.agent_name,
            unique_knowledge,
            confidence=rag_confidence,
        )

        # -----------------------------------------------------
        # Return Result
        # -----------------------------------------------------
        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=rag_confidence,
            result=unique_knowledge,
            evidence=evidence,
            metadata={
                "query": query,
                "disease_detected": disease,
                "documents_found": len(unique_knowledge),
                "citations": citations,
                "references": references,
                "rag_confidence": rag_confidence,
                "similarity_scores": [e.get("similarity_score") for e in unique_knowledge],
                "hybrid_scores": [e.get("hybrid_score") for e in unique_knowledge],
                "relevance_scores": [e.get("relevance_score") for e in unique_knowledge],
                "guardrail_warnings": guardrail_warnings,
            },
        )

    def validate(
        self,
        state: AgentState,
    ) -> None:
        """
        Optional validation.
        """
        return
