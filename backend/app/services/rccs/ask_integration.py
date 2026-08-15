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
    request_context: dict[str, Any] | None = None,
    on_activity: OnActivity | None = None,
    campus_query=None,
    conversation_context: dict[str, Any] | None = None,
) -> HybridRetrievalResult:
    """RCCS retrieval entrypoint.

    When SUPERVISOR_ENABLED=1, runs Plan→Route→Execute→Reflect over RCCS skills.
    Otherwise uses the existing hybrid_retrieve path. Both return HybridRetrievalResult
    so ask.py / SSE stay unchanged.
    """
    if supervisor_enabled():
        from app.services.orchestrator.supervisor import run as supervisor_run

        result = await supervisor_run(
            question,
            use_web_search=use_web_search,
            history=history,
            request_context=request_context,
            on_activity=on_activity,
            campus_query=campus_query,
            conversation_context=conversation_context,
        )
        result.metadata.setdefault("conversation_context", {})["request_context"] = dict(
            request_context or {}
        )
        result.metadata.setdefault("safe_response", {})["request_context"] = dict(
            request_context or {}
        )
        return result
    # Hybrid path owns planning + page-read execution and now uses history/scope.
    return await hybrid_retrieve(
        question,
        use_web_search=use_web_search,
        source_scope=source_scope,
        history=history,
        request_context=request_context,
        on_activity=on_activity,
        campus_query=campus_query,
        conversation_context=conversation_context,
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
    *,
    evidence_ids: set[str] | None = None,
) -> dict[str, Any]:
    ctx = (result.metadata or {}).get("conversation_context") or {}
    question = str(ctx.get("resolved_question") or ctx.get("original_question") or "")
    eligible = (
        [item for item in result.evidence if item.evidence_id in evidence_ids]
        if evidence_ids is not None
        else result.evidence
    )
    # Once the release ledger has named the evidence that supports released
    # claims, that allow-list is authoritative.  Re-running the legacy lexical
    # selector can incorrectly discard valid proof for paraphrases (for
    # example, "feel ill" versus "Student Health Services").  URL/trust checks
    # still run below in validate_citations.
    selected = (
        eligible[: max(1, cfg.max_citations())]
        if evidence_ids is not None
        else select_relevant_citation_evidence(
            f"{question}\n{answer}",
            eligible,
            max_citations=cfg.max_citations(),
        )
    )
    return validate_citations(answer, selected, plan=result.plan)
