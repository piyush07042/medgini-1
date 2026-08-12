"""
Workflow API
============
REST endpoints for Phase 8 AI Workflow Improvements.

Endpoints:
  GET  /api/v1/workflow/prompts                  — list all prompts & versions
  POST /api/v1/workflow/prompts/{name}/test       — run prompt test suite
  POST /api/v1/workflow/prompts/{name}/promote/{version} — promote version
  GET  /api/v1/workflow/quality                  — quality score history per agent
  GET  /api/v1/workflow/evaluation               — agent leaderboard + snapshots
  GET  /api/v1/workflow/guardrails/log           — recent guardrail violations
  GET  /api/v1/workflow/citations/verify         — verify citations payload
  POST /api/v1/workflow/citations/verify         — verify submitted citations
  GET  /api/v1/workflow/memory                   — memory telemetry
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from app.workflow.prompt_registry import prompt_registry
from app.workflow.prompt_tester import prompt_tester
from app.workflow.quality_scorer import quality_scorer
from app.workflow.agent_evaluator import agent_evaluator
from app.workflow.guardrails import guardrails
from app.workflow.citation_verifier import citation_verifier
from app.workflow.memory_manager import memory_manager

router = APIRouter(prefix="/workflow", tags=["AI Workflow"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PromotionRequest(BaseModel):
    reason: str = "Manual promotion"


class CitationPayload(BaseModel):
    citations: list[dict[str, Any]] = []


class RegisterPromptRequest(BaseModel):
    name: str
    category: str
    template: str
    variables: list[str] = []
    description: str = ""


# ---------------------------------------------------------------------------
# Prompt Endpoints
# ---------------------------------------------------------------------------

@router.get("/prompts", summary="List all registered prompts")
def list_prompts():
    """Return all registered prompts with their versions and metadata."""
    return {
        "prompts": prompt_registry.list_prompts(),
        "total": len(prompt_registry.list_prompts()),
    }


@router.get("/prompts/{name}", summary="Get a specific prompt with all versions")
def get_prompt(name: str):
    """Return a prompt entry with all its versions."""
    entry = prompt_registry.get(name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    active = entry.get_active()
    return {
        "name": entry.name,
        "category": entry.category,
        "active_version": entry.active_version,
        "versions": [
            {
                "version": v.version,
                "description": v.description,
                "variables": v.variables,
                "active": v.active,
                "created_at": v.created_at,
                "template_preview": v.template[:200] + ("..." if len(v.template) > 200 else ""),
            }
            for v in entry.versions
        ],
        "active_template": active.template if active else None,
    }


@router.post("/prompts/{name}/test", summary="Run test suite for a prompt")
def test_prompt(name: str):
    """Execute all registered test cases for the specified prompt."""
    result = prompt_tester.run_prompt(name)
    return {
        "prompt_name": result.prompt_name,
        "version": result.version,
        "score": result.score,
        "passed": result.passed,
        "failed": result.failed,
        "total": result.total,
        "details": result.details,
        "warnings": result.warnings,
        "status": "PASS" if result.score >= 0.8 else "FAIL",
    }


@router.post("/prompts/test-all", summary="Run tests for all prompts")
def test_all_prompts():
    """Execute test suites across all registered prompts."""
    result = prompt_tester.run_all()
    return {
        "total_prompts": result.total_prompts,
        "total_tests": result.total_tests,
        "total_passed": result.total_passed,
        "total_failed": result.total_failed,
        "overall_score": result.overall_score,
        "results": result.results,
        "warnings": result.warnings,
        "status": "PASS" if result.overall_score >= 0.8 else "FAIL",
    }


@router.post("/prompts/{name}/promote/{version}", summary="Promote a prompt version")
def promote_prompt_version(name: str, version: int, body: PromotionRequest = Body(default=PromotionRequest())):
    """Set a specific prompt version as the active version."""
    success = prompt_registry.promote_version(name, version)
    if not success:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found or version {version} does not exist")
    return {
        "message": f"Prompt '{name}' promoted to v{version}",
        "reason": body.reason,
    }


@router.post("/prompts/register", summary="Register a new prompt or version")
def register_prompt(body: RegisterPromptRequest):
    """Register a new prompt or add a new version to an existing prompt."""
    entry = prompt_registry.register(
        name=body.name,
        category=body.category,
        template=body.template,
        variables=body.variables,
        description=body.description,
    )
    return {
        "message": f"Prompt '{body.name}' registered as v{entry.active_version}",
        "name": entry.name,
        "version": entry.active_version,
    }


# ---------------------------------------------------------------------------
# Quality Score Endpoints
# ---------------------------------------------------------------------------

@router.get("/quality", summary="Get quality score history per agent")
def get_quality_scores():
    """Return rolling quality score summaries for all agents."""
    return {
        "agent_summaries": quality_scorer.get_agent_summary(),
        "description": "Mean quality score (0.0–1.0) per agent across last 100 runs",
    }


@router.get("/quality/{agent_name}", summary="Get quality history for a specific agent")
def get_agent_quality(agent_name: str, limit: int = Query(20, ge=1, le=100)):
    """Return detailed quality score history for a specific agent."""
    history = quality_scorer.get_history(agent_name)
    return {
        "agent": agent_name,
        "history": history[-limit:],
        "count": len(history),
    }


# ---------------------------------------------------------------------------
# Agent Evaluation Endpoints
# ---------------------------------------------------------------------------

@router.get("/evaluation", summary="Get agent evaluation leaderboard")
def get_evaluation_leaderboard():
    """Return the agent leaderboard ranked by composite evaluation score."""
    leaderboard = agent_evaluator.get_leaderboard()
    return {
        "leaderboard": [
            {
                "rank": e.rank,
                "agent": e.agent_name,
                "runs": e.runs,
                "composite_score": e.mean_composite,
                "quality_score": e.mean_quality,
                "mean_latency_s": e.mean_latency,
                "failure_rate": e.failure_rate,
                "guardrail_pass_rate": e.guardrail_pass_rate,
                "grade": _grade(e.mean_composite),
            }
            for e in leaderboard
        ],
        "total_agents": len(leaderboard),
    }


@router.get("/evaluation/{agent_name}", summary="Get evaluation snapshots for an agent")
def get_agent_evaluation(agent_name: str, limit: int = Query(20, ge=1, le=100)):
    """Return detailed evaluation snapshots for a specific agent."""
    return {
        "agent": agent_name,
        "snapshots": agent_evaluator.get_snapshots(agent_name, limit),
    }


# ---------------------------------------------------------------------------
# Guardrails Endpoints
# ---------------------------------------------------------------------------

@router.get("/guardrails/log", summary="Get recent guardrail violation log")
def get_guardrail_log(limit: int = Query(50, ge=1, le=200)):
    """Return recent guardrail violations across all agents."""
    return {
        "violations": guardrails.get_violation_log(limit),
        "stats": guardrails.get_stats(),
    }


# ---------------------------------------------------------------------------
# Citation Verification Endpoints
# ---------------------------------------------------------------------------

@router.post("/citations/verify", summary="Verify a list of citations")
def verify_citations(body: CitationPayload):
    """Verify a submitted list of citations for format validity and source approval."""
    result = citation_verifier.verify(body.citations)
    return {
        "total": result.total,
        "verified": result.verified,
        "unverified": result.unverified,
        "invalid": result.invalid,
        "confidence_score": result.confidence_score,
        "verdicts": [
            {
                "citation_id": v.citation_id,
                "source_type": v.source_type,
                "status": v.status,
                "detail": v.detail,
            }
            for v in result.verdicts
        ],
        "timestamp": result.timestamp,
    }


# ---------------------------------------------------------------------------
# Memory Telemetry Endpoints
# ---------------------------------------------------------------------------

@router.get("/memory", summary="Get memory manager telemetry")
def get_memory_telemetry(limit: int = Query(20, ge=1, le=100)):
    """Return memory optimization telemetry for recent workflow runs."""
    return {
        "telemetry": memory_manager.get_telemetry(limit),
        "cache_stats": memory_manager.get_cache_stats(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    elif score >= 0.75:
        return "B"
    elif score >= 0.60:
        return "C"
    elif score >= 0.45:
        return "D"
    return "F"
