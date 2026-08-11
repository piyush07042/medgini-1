from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import ChatConversation, ChatMessage
from fastapi.responses import StreamingResponse
import json
import asyncio

from app.agents.base.agent_state import AgentState
from app.core.deps import get_supervisor
from app.core.answer_generator import generate_grounded_answer
from app.schemas.common import ApiResponse


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _build_chat_reply(final_state: AgentState, user_message: str = "") -> tuple[str, list[dict]]:
    """
    Build the chat reply. For knowledge questions (where RAG evidence is
    available and a user message was provided), generate a grounded answer
    with claim-level citations. For workflow-centric results, fall back to
    the existing clinical summary / recommendation / risk display.

    Returns (reply_text, cited_sources).
    """
    cited_sources: list[dict] = []

    # If we have RAG knowledge and a user question, generate a grounded answer
    if user_message and final_state.knowledge_results:
        result = generate_grounded_answer(user_message, final_state.knowledge_results)
        answer = result.get("answer", "")
        cited_sources = result.get("cited_sources", [])
        if answer:
            return answer, cited_sources

    # Fallback: existing behavior for patient-workflow results
    if final_state.final_report:
        clinical_summary = final_state.final_report.get("clinical_summary")
        if clinical_summary:
            return str(clinical_summary), cited_sources

    if final_state.recommendations:
        first_rec = final_state.recommendations[0]
        if isinstance(first_rec, dict):
            title = first_rec.get("title") or first_rec.get("priority") or "Recommendation"
            recommendation = first_rec.get("recommendation") or first_rec.get("summary") or "Please review the recommended next steps."
            return f"{title}: {recommendation}", cited_sources
        return str(first_rec), cited_sources

    if final_state.disease_risk:
        risk_category = final_state.disease_risk.get("risk_category") or final_state.disease_risk.get("risk_level") or "Unknown"
        probability = final_state.disease_risk.get("probability") or final_state.disease_risk.get("risk_score") or final_state.disease_risk.get("confidence")
        if probability is not None:
            return f"Risk assessment indicates {risk_category} with estimated probability {probability}.", cited_sources
        return f"Risk assessment indicates {risk_category}.", cited_sources

    return "I reviewed the context and prepared a clinical workflow summary for you.", cited_sources


def _build_rag_sources(final_state: AgentState, cited_sources: list[dict] | None = None) -> list[str]:
    """
    Collect source references. If cited_sources is provided (from the grounded
    answer generator), return only the sources that were actually cited.
    Otherwise fall back to collecting all source names from knowledge_results.
    """
    if cited_sources:
        # Return only sources that were actually cited in the answer
        return [s["name"] for s in cited_sources if s.get("name")][:6]

    # Fallback: collect all unique source names
    sources: list[str] = []
    for entry in (final_state.knowledge_results or []):
        if not isinstance(entry, dict):
            continue
        meta = entry.get("metadata") or {}
        src = meta.get("source") or meta.get("title") or ""
        if src and src not in sources:
            sources.append(src)
    # Also include CI guideline reference
    if final_state.final_report:
        ci = final_state.final_report.get("clinical_intelligence") or {}
        guideline = ci.get("Guideline") or ci.get("Guideline Source") or ""
        if guideline and guideline not in sources:
            sources.append(guideline)
    return sources[:6]


def _build_follow_up_suggestions(final_state: AgentState, message: str) -> list[str]:
    """Generate context-aware follow-up questions for the chat UI."""
    suggestions: list[str] = []
    risk = final_state.disease_risk or {}
    risk_category = risk.get("risk_category") or risk.get("risk_level") or ""
    disease = risk.get("disease") or risk.get("condition") or risk.get("prediction") or ""

    if risk_category.lower() in ("high", "critical"):
        suggestions.append("What are the most urgent next steps for high-risk patients?")
        suggestions.append("What emergency warning signs should I watch for?")
    elif risk_category.lower() == "moderate":
        suggestions.append("What lifestyle changes are recommended for moderate risk?")
        suggestions.append("When should the next follow-up appointment be scheduled?")
    else:
        suggestions.append("What preventive measures are recommended?")
        suggestions.append("What is the recommended monitoring frequency?")

    if disease:
        suggestions.append(f"What medications are commonly used for {disease}?")
        suggestions.append(f"What are the diagnostic criteria for {disease}?")

    if final_state.drug_analysis:
        status = final_state.drug_analysis.get("status") or ""
        if status == "FLAGGED":
            suggestions.append("What are the alternative medications to the flagged ones?")

    return suggestions[:4]


@router.post(
    "/",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(
    payload: dict,
    supervisor=Depends(get_supervisor),
):
    """
    Execute the clinical workflow for chat-style requests and return a
    structured reply derived from the workflow state.
    """
    try:
        payload = payload or {}
        patient_context = payload.get("patient_context") or payload.get("patient") or {}
        message = payload.get("message") or payload.get("query") or payload.get("text") or ""
        raw_report_text = payload.get("raw_report_text") or payload.get("report_text") or payload.get("report") or ""

        state = AgentState()
        if isinstance(patient_context, dict):
            state.patient = dict(patient_context)
            state.patient.setdefault("name", state.patient.get("name", ""))
            state.patient.setdefault("age", state.patient.get("age", 0))
            state.patient.setdefault("gender", state.patient.get("gender", ""))

        if message:
            state.symptoms = _as_list(payload.get("symptoms") or message)

        medications = payload.get("medications") or state.patient.get("current_medications") or []
        allergies = payload.get("allergies") or state.patient.get("allergies") or []
        state.medications = _as_list(medications)
        state.allergies = _as_list(allergies)

        if raw_report_text:
            state.raw_report_text = raw_report_text
            state.report_text = raw_report_text

        final_state, results, metrics = await supervisor.run(state)

        reply, cited_sources = _build_chat_reply(final_state, user_message=message)
        rag_sources = _build_rag_sources(final_state, cited_sources=cited_sources)
        follow_up_suggestions = _build_follow_up_suggestions(final_state, message)

        return ApiResponse(
            message="Chat processed successfully.",
            data={
                "reply": reply,
                "workflow_state": final_state,
                "agent_results": results,
                "metrics": metrics,
                "clinical_summary": (final_state.final_report or {}).get("clinical_summary") if final_state.final_report else None,
                "sources": rag_sources,
                "cited_sources": cited_sources,
                "follow_up_suggestions": follow_up_suggestions,
                "clinical_intelligence": (final_state.final_report or {}).get("clinical_intelligence") if final_state.final_report else {},
                "execution_log": final_state.metadata.get("execution_log") if isinstance(final_state.metadata, dict) else [],
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat workflow failed: {exc}",
        )



@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
)
async def chat_stream(
    payload: dict = Body(...),
    supervisor=Depends(get_supervisor),
):
    """
    Run the chat workflow and stream the assistant reply back as Server-Sent Events (SSE).
    This is a pragmatic streaming implementation that chunks the final assistant reply.
    """
    try:
        payload = payload or {}
        patient_context = payload.get("patient_context") or payload.get("patient") or {}
        message = payload.get("message") or payload.get("query") or payload.get("text") or ""
        raw_report_text = payload.get("raw_report_text") or payload.get("report_text") or payload.get("report") or ""

        state = AgentState()
        if isinstance(patient_context, dict):
            state.patient = dict(patient_context)
            state.patient.setdefault("name", state.patient.get("name", ""))
            state.patient.setdefault("age", state.patient.get("age", 0))
            state.patient.setdefault("gender", state.patient.get("gender", ""))

        if message:
            state.symptoms = _as_list(payload.get("symptoms") or message)

        medications = payload.get("medications") or state.patient.get("current_medications") or []
        allergies = payload.get("allergies") or state.patient.get("allergies") or []
        state.medications = _as_list(medications)
        state.allergies = _as_list(allergies)

        if raw_report_text:
            state.raw_report_text = raw_report_text
            state.report_text = raw_report_text

        # run workflow to compute final reply
        final_state, results, metrics = await supervisor.run(state)

        reply, cited_sources = _build_chat_reply(final_state, user_message=message)
        clinical_summary = (final_state.final_report or {}).get("clinical_summary") if final_state.final_report else None
        rag_sources = _build_rag_sources(final_state, cited_sources=cited_sources)
        follow_up_suggestions = _build_follow_up_suggestions(final_state, message)
        clinical_intelligence = (final_state.final_report or {}).get("clinical_intelligence") if final_state.final_report else {}

        # sentence-based chunking to improve readability
        import re

        def sentence_chunks(text):
            if not text:
                return []
            # split on sentence boundaries (period/question/exclamation followed by space)
            parts = re.split(r'(?<=[.!?])\s+', text)
            out = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                # if sentence too long, split into 200-char pieces
                if len(p) <= 200:
                    out.append(p + " ")
                else:
                    for i in range(0, len(p), 200):
                        out.append(p[i : i + 200])
            return out

        async def event_generator(text: str):
            # initial event
            yield f"data: {json.dumps({'type': 'started'})}\n\n"

            chunks = sentence_chunks(text)
            for chunk in chunks:
                payload_obj = {"type": "chunk", "text": chunk}
                yield f"data: {json.dumps(payload_obj)}\n\n"
                # small pause for UX smoothness
                await asyncio.sleep(0.06)

            # final event with metadata and sources
            yield f"data: {json.dumps({'type': 'done', 'clinical_summary': clinical_summary, 'sources': rag_sources, 'cited_sources': cited_sources, 'follow_up_suggestions': follow_up_suggestions, 'clinical_intelligence': clinical_intelligence})}\n\n"

        return StreamingResponse(event_generator(reply), media_type="text/event-stream")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat stream failed: {exc}",
        )



@router.post(
    "/store",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def store_chat(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Persist a chat conversation and its messages to the database.
    """
    try:
        patient_id = payload.get("patient_id")
        title = payload.get("title") or None
        messages = payload.get("messages") or []

        convo = ChatConversation(patient_id=patient_id, title=title, metadata_json=payload.get("metadata") or {})
        db.add(convo)
        db.flush()

        for msg in messages:
            cm = ChatMessage(
                conversation_id=convo.id,
                role=msg.get("role") or "user",
                text=msg.get("text") or "",
                metadata_json=msg.get("metadata") or {},
            )
            db.add(cm)

        db.commit()

        return ApiResponse(message="Conversation stored", data={"conversation_id": convo.id})
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unable to store conversation: {exc}")


@router.get(
    "/patient/{patient_id}/conversations",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversations_for_patient(patient_id: int, db: Session = Depends(get_db)):
    try:
        convos = db.query(ChatConversation).filter(ChatConversation.patient_id == patient_id).order_by(ChatConversation.created_at.desc()).all()
        results = []
        for c in convos:
            msgs = [
                {"id": m.id, "role": m.role, "text": m.text, "timestamp": m.timestamp.isoformat(), "metadata": getattr(m, "metadata_json", None)}
                for m in sorted(c.messages, key=lambda x: x.timestamp)
            ]
            results.append({"id": c.id, "title": c.title, "created_at": c.created_at.isoformat(), "messages": msgs})

        return ApiResponse(message="Conversations retrieved", data=results)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unable to fetch conversations: {exc}")