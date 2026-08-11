import chromadb
from chromadb.utils import embedding_functions
from typing import Any
from pathlib import Path

from app.core.config import settings


chroma_client = None
collection = None
embedding_function = None


def _get_collection():
    """Lazily initialize the Chroma collection to avoid blocking startup."""
    global chroma_client, collection, embedding_function

    if collection is not None:
        return collection

    chroma_client = chromadb.PersistentClient(path=str(Path(getattr(settings, "RAG_DB_DIRECTORY", "medigenie_rag_db"))))

    try:
        if embedding_function is None:
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
    except Exception:
        embedding_function = None

    if embedding_function is None:
        collection = chroma_client.get_or_create_collection(name="clinical_guidelines")
    else:
        collection = chroma_client.get_or_create_collection(
            name="clinical_guidelines",
            embedding_function=embedding_function,
        )

    return collection


def seed_sample_guidelines():
    """Seed sample clinical guidelines into ChromaDB if empty, including PubMed, WHO, and Drug databases."""
    current_collection = _get_collection()
    if current_collection.count() == 0:
        current_collection.add(
            documents=[
                "PubMed ID 3489102: Double-blind RCT confirms Metformin reduces progression of diabetes by 31% in prediabetic patients compared to placebo when paired with lifestyle interventions.",
                "PubMed ID 3829014: High-intensity statins (atorvastatin 40-80mg) show 22% reduction in cardiovascular events for patients with established atherosclerosis.",
                "ACC/AHA Hypertension Guidelines: First-line pharmacotherapy includes thiazide diuretics, CCBs, and ACE inhibitors or ARBs. Monitor potassium and renal function.",
                "FDA Safety Warning: Fluoroquinolones carry black box warnings for tendonitis and tendon rupture. Avoid as first-line in uncomplicated infections if alternatives exist.",
                "WHO Diabetes Management Guidelines: Target HbA1c is below 7.0% for most non-pregnant adults. First-line glucose-lowering therapy is Metformin along with lifestyle interventions.",
                "Drug Database: Metformin is contraindicated in patients with severe renal impairment (eGFR < 30 mL/min/1.73m²) due to risk of lactic acidosis accumulation.",
                "Drug Database: Sacubitril/Valsartan (ARNI) is contraindicated with concurrent ACE inhibitor therapy or history of angioedema. Requires 36-hour washout period.",
                "AHA/ASA 2024 Guidelines for the Prevention of Stroke: Common risk factors for stroke include hypertension, diabetes mellitus, atrial fibrillation, high cholesterol (dyslipidemia), and carotid artery stenosis. Hypertension is the single most important modifiable risk factor for both ischemic and hemorrhagic stroke. Patients with atrial fibrillation should receive anticoagulation therapy to reduce stroke risk.",
                "AHA/ASA 2024 Guidelines for the Prevention of Stroke: Smoking cessation significantly reduces stroke risk. Physical inactivity and obesity are independent risk factors. Heavy alcohol consumption increases hemorrhagic stroke risk. Recommended management includes lifestyle modification, blood pressure control below 130/80 mmHg, and statin therapy for patients with elevated LDL cholesterol.",
                "WHO Stroke Prevention Guidelines: The World Health Organization identifies hypertension, tobacco use, diabetes, physical inactivity, obesity, and unhealthy diet as the leading modifiable risk factors for stroke worldwide. Population-level interventions targeting these factors can reduce stroke incidence by up to 80%. Early detection and management of atrial fibrillation is critical.",
                "AHA/ACC Cardiovascular Risk Guidelines: Comprehensive cardiovascular risk assessment should include evaluation of blood pressure, lipid profile, blood glucose, BMI, smoking status, and family history. Patients with multiple risk factors benefit from aggressive pharmacological and lifestyle interventions. 10-year ASCVD risk calculators guide statin and aspirin therapy decisions."
            ],
            metadatas=[
                {"source": "PubMed", "category": "Diabetes", "year": "2024"},
                {"source": "PubMed", "category": "Hypertension", "year": "2023"},
                {"source": "ACC/AHA Guidelines", "category": "Hypertension", "year": "2025"},
                {"source": "FDA Safety Alerts", "category": "Drug Safety", "year": "2024"},
                {"source": "WHO Guidelines", "category": "Diabetes", "year": "2024"},
                {"source": "Drug Database", "category": "Contraindications", "year": "2025"},
                {"source": "Drug Database", "category": "Contraindications", "year": "2024"},
                {"source": "AHA/ASA 2024 Guidelines", "category": "Stroke", "year": "2024"},
                {"source": "AHA/ASA 2024 Guidelines", "category": "Stroke", "year": "2024"},
                {"source": "WHO Guidelines", "category": "Stroke", "year": "2024"},
                {"source": "AHA/ACC Guidelines", "category": "Cardiovascular", "year": "2024"}
            ],
            ids=["pmid_dia_01", "pmid_htn_01", "guideline_htn_01", "guideline_fda_01", "guideline_dia_01", "drug_db_met_01", "drug_db_sac_01", "guideline_stroke_01", "guideline_stroke_02", "guideline_stroke_who_01", "guideline_cv_01"]
        )
        from app.core.logging import get_logger
        get_logger(__name__).info("Vector DB initialized with clinical practice guidelines")


def query_knowledge_base(
    query_text: str,
    n_results: int = 2,
    source_filter: list[str] | None = None,
    category_filter: str | None = None,
    min_score: float = 0.25,
) -> list[dict[str, Any]]:
    """Retrieve relevant guideline snippets with metadata filtering and Hybrid Search scoring."""
    current_collection = _get_collection()
    
    # Setup metadata filter query if specified
    where_clause = {}
    if source_filter:
        if len(source_filter) == 1:
            where_clause["source"] = source_filter[0]
        else:
            where_clause["$or"] = [{"source": s} for s in source_filter]
    if category_filter:
        where_clause["category"] = category_filter

    results = current_collection.query(
        query_texts=[query_text],
        n_results=n_results * 2, # Fetch extra for re-ranking
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"],
    )

    if not results or "documents" not in results or len(results["documents"]) == 0:
        return []

    unique_items: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    documents = results["documents"][0]
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    # Tokenize query for keyword matching score (BM25 hybrid fallback)
    query_terms = set(query_text.lower().split())

    for idx, document in enumerate(documents):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        distance = distances[idx] if idx < len(distances) else None
        similarity_score = 0.0

        if isinstance(distance, (int, float)):
            # convert cosine distance to a similarity value
            similarity_score = 1.0 / (1.0 + distance)

        document_text = str(document or "").strip()
        identifier = metadata.get("id") or metadata.get("source") or ""
        key = (str(identifier), document_text)
        if not document_text or key in seen_keys:
            continue

        seen_keys.add(key)

        # Keyword matching score contribution (Hybrid Search term overlap)
        doc_words = document_text.lower().split()
        match_count = sum(1 for term in query_terms if term in doc_words)
        keyword_score = match_count / max(len(query_terms), 1)

        # Combined Hybrid Search score
        hybrid_score = round((similarity_score * 0.7) + (keyword_score * 0.3), 4)

        unique_items.append({
            "document": document_text,
            "metadata": metadata or {},
            "distance": distance,
            "similarity_score": similarity_score,
            "hybrid_score": hybrid_score,
            "keyword_match_ratio": keyword_score
        })

    # Sort by hybrid score
    unique_items.sort(
        key=lambda item: item.get("hybrid_score", 0.0),
        reverse=True,
    )

    # Filter out documents below minimum relevance threshold
    if min_score > 0:
        unique_items = [item for item in unique_items if item.get("hybrid_score", 0.0) >= min_score]

    return unique_items[:n_results]



def ingest_documents(documents: list[str], metadatas: list[dict] | None = None, ids: list[str] | None = None) -> dict:
    """Add documents to the clinical_guidelines collection.

    documents: list of document text
    metadatas: optional list of metadata dicts matching documents
    ids: optional list of ids for the documents

    Returns a summary dict with counts and any errors.
    """
    current_collection = _get_collection()
    try:
        if metadatas is None:
            metadatas = [{} for _ in documents]
        if ids is None:
            # create generated ids
            ids = [f"doc_{i}_{abs(hash(doc)) % 100000}" for i, doc in enumerate(documents)]

        current_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return {
            "added": len(documents),
            "ids": ids,
        }
    except Exception as exc:
        return {
            "added": 0,
            "error": str(exc),
        }