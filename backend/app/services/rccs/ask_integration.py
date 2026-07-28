"""Helpers to integrate RCCS hybrid retrieval into ask.py without rewriting the router."""

from __future__ import annotations

from typing import Any

from app.services.orchestrator.config import supervisor_enabled
from app.services.orchestrator.models import OnActivity
from app.services.rccs import config as cfg
from app.services.rccs.citations import (
    evidence_to_chunk_responses,
    select_relevant_citation_evidence,
    validate_citations,
)
from app.services.rccs.hybrid import hybrid_retrieve
from app.services.rccs.models import HybridRetrievalResult


def rccs_enabled() -> bool:
    return bool(cfg.rccs_enabled())


async def run_rccs_retrieval(
    question: str,
    *,
    use_web_search: bool = False,
    source_scope: str | None = None,
    history: list[dict[str, Any]] | None = None,
    on_activity: OnActivity | None = None,
) -> HybridRetrievalResult:
    """RCCS retrieval entrypoint.

    When SUPERVISOR_ENABLED=1, runs Plan→Route→Execute→Reflect over RCCS skills.
    Otherwise uses the existing hybrid_retrieve path. Both return HybridRetrievalResult
    so ask.py / SSE stay unchanged.
    """
    if supervisor_enabled():
        from app.services.orchestrator.supervisor import run as supervisor_run

        return await supervisor_run(
            question,
            use_web_search=use_web_search,
            history=history,
            on_activity=on_activity,
        )
    # Hybrid path owns planning + page-read execution and now uses history/scope.
    return await hybrid_retrieve(
        question,
        use_web_search=use_web_search,
        source_scope=source_scope,
        history=history,
        on_activity=on_activity,
    )


def result_to_pipeline_parts(
    result: HybridRetrievalResult,
) -> dict[str, Any]:
    """Convert hybrid result into shapes ask.py already understands."""
    evidence = result.evidence
    ctx = (result.metadata or {}).get("conversation_context") or {}
    citation_question = (
        ctx.get("resolved_question")
        or (result.plan.search_queries or [""])[0]
        or ctx.get("original_question")
        or ""
    )
    citation_evidence = select_relevant_citation_evidence(
        citation_question,
        evidence,
        max_citations=cfg.max_citations(),
    )
    chunk_dicts = [e.to_chunk_dict() for e in evidence]
    chunk_responses = evidence_to_chunk_responses(evidence)
    citations = [e.to_citation() for e in citation_evidence]
    validation = validate_citations(
        "",  # answer not yet generated
        citation_evidence,
        plan=result.plan,
    )
    # Prefer validated citation list (drops blocked URLs)
    if validation.get("citations"):
        citations = validation["citations"]

    return {
        "chunk_dicts": chunk_dicts,
        "chunk_responses": chunk_responses,
        "citations": citations,
        "sources_found": len(evidence),
        "citation_count": len(citation_evidence),
        "validation": validation,
        "metadata": result.metadata,
        "errors_by_channel": result.errors_by_channel,
        "classification": result.classification,
        "plan": result.plan,
    }


def validate_answer_citations(
    answer: str,
    result: HybridRetrievalResult,
) -> dict[str, Any]:
    return validate_citations(answer, result.evidence, plan=result.plan)
