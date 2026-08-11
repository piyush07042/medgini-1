from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Body

from app.core.rag import ingest_documents, query_knowledge_base
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
)


@router.post("/index", response_model=ApiResponse)
def index_documents(
    documents: List[str] = Body(..., description="List of document texts to index."),
    metadatas: List[dict] | None = Body(None, description="Optional list of metadata dicts."),
    ids: List[str] | None = Body(None, description="Optional list of ids for documents."),
):
    """Index provided documents into the RAG knowledge store (ChromaDB).

    This is a simple ingestion endpoint intended for admin or CI use.
    """
    if not documents:
        raise HTTPException(status_code=400, detail="No documents provided")

    result = ingest_documents(documents=documents, metadatas=metadatas, ids=ids)

    if result.get("added", 0) == 0 and result.get("error"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return ApiResponse(
        message="Documents indexed successfully.",
        data=result,
    )


@router.post("/query", response_model=ApiResponse)
def query_documents(
    query_text: str = Body(..., description="Query text to search relevant knowledge snippets."),
    n_results: int = Body(2, description="Number of results to return."),
):
    """Query the indexed knowledge base for relevant snippets."""
    if not query_text:
        raise HTTPException(status_code=400, detail="Query text is required")

    results = query_knowledge_base(query_text=query_text, n_results=n_results)
    return ApiResponse(
        message="Knowledge query completed successfully.",
        data={"results": results},
    )
