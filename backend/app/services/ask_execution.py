"""Canonical, transport-neutral execution contract for one AskMcNeese turn.

The router owns HTTP/SSE concerns. RCCS owns retrieval. This module owns the
single sequence: the user's wording -> one CampusQuery -> evidence for that
goal -> claims -> release. A new complete question is never answered as if it
were a category selected from the previous turn.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.models import ClaimSupport
from app.services.campus_intelligence.route_validator import route_matches_goal
from app.services.conversation_context import looks_like_followup, resolve_question_with_history
from app.services.grounded_fallback import render_grounded_fallback
from app.services.llm import generate_answer
from app.services.rccs.ask_integration import (
    result_to_pipeline_parts,
    run_rccs_retrieval,
    validate_answer_citations,
)
from app.services.structured_answer import structure_answer


OnActivity = Callable[[str, dict[str, Any] | None, str | None], Any]

_TRUTHY = {"1", "true", "yes", "on"}
_TASK_STATUSES = {
    "active",
    "awaiting_input",
    "blocked",
    "completed",
    "ready_for_confirmation",
}
_SELECTION_RE = re.compile(r"(?<!\d)(\d{5})(?!\d)")
_MONEY_RE = re.compile(r"\$\s*\d+(?:\.\d{2})?")
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_DATE_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:,\s*\d{4})?\b|\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
    re.I,
)
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.I)
_CRN_RE = re.compile(r"\bCRN\s+(\d{5})\b", re.I)


def outcome_status(release_decision: dict[str, Any] | None, model: str | None) -> str:
    """Separate pipeline completion from answer-quality success."""
    decision = release_decision or {}
    release = str(decision.get("status") or "")
    reasons = {str(item) for item in (decision.get("reasons") or [])}
    label = str(model or "")
    if release == "BLOCKED":
        return "release_blocked"
    if label == "clarification" or "CLARIFICATION_REQUIRED" in reasons:
        return "clarification"
    if release == "CAN_RELEASE_PARTIAL" or label in {
        "grounded-partial-fast",
        "fallback-no-llm",
    }:
        return "partial"
    if label == "no_source":
        return "no_results"
    return "success"


def execution_v2_enabled() -> bool:
    """Rollback switch. ASK_EXECUTION_V2=0 restores the existing router path."""
    return os.getenv("ASK_EXECUTION_V2", "1").strip().lower() in _TRUTHY


def _generation_timeout_seconds(*, page_read: bool = False) -> float:
    """Claude needs more than a retrieval slice to write from official pages."""
    try:
        base = max(0.5, float(os.getenv("ASK_GENERATION_TIMEOUT_SECONDS", "15")))
    except ValueError:
        base = 15.0
    if page_read:
        return max(base, 15.0)
    return base


def _short_text(value: Any, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:limit] if cleaned else None


def sanitize_client_task_state(value: Any) -> dict[str, Any] | None:
    """Accept selection/context hints only; discard all institutional facts."""
    if not isinstance(value, dict):
        return None
    task_type = _short_text(value.get("task_type"), 64)
    status = _short_text(value.get("status"), 32)
    if not task_type or status not in _TASK_STATUSES:
        return None
    state: dict[str, Any] = {
        "schema_version": 1,
        "task_type": task_type,
        "status": status,
    }
    for key, limit in (
        ("domain", 48),
        ("term", 64),
        ("subject", 64),
        ("constraint_course", 96),
        ("constraint_section", 32),
        ("pending_field", 64),
        ("query_anchor", 240),
    ):
        cleaned = _short_text(value.get(key), limit)
        if cleaned:
            state[key] = cleaned
    selections: list[str] = []
    for raw in value.get("selected_crns") or []:
        match = _SELECTION_RE.fullmatch(str(raw).strip())
        if match and match.group(1) not in selections:
            selections.append(match.group(1))
        if len(selections) >= 20:
            break
    if selections:
        state["selected_crns"] = selections
    # Deliberately ignored: fees, hours, deadlines, contacts, compatibility,
    # section records, evidence, release decisions, and all other client fields.
    return state


@dataclass
class LogicalAskResult:
    question: str
    answer: str
    chunks: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    num_results: int
    model: str | None
    tokens_used: int | None
    retrieval_ms: int
    generation_ms: int | None
    total_ms: int
    structured: dict[str, Any]
    retrieval_metadata: dict[str, Any]
    task_state: dict[str, Any] | None
    execution: dict[str, Any]
    release_decision: dict[str, Any]
    claim_ledger: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)


def _normal(value: str, claim_type: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip(" \t\r\n.,;:")
    if claim_type == "phone":
        return re.sub(r"\D", "", text)[-10:]
    if claim_type == "money":
        return "$" + re.sub(r"[^0-9.]", "", text)
    if claim_type == "url":
        return text.rstrip("/)").casefold()
    if claim_type == "crn":
        return re.sub(r"\D", "", text)
    return text.casefold()


def _material_claims(answer: str) -> list[tuple[str, str]]:
    claims: list[tuple[str, str]] = []
    claims.extend(("money", match.group(0)) for match in _MONEY_RE.finditer(answer or ""))
    claims.extend(("phone", match.group(0)) for match in _PHONE_RE.finditer(answer or ""))
    claims.extend(("email", match.group(0)) for match in _EMAIL_RE.finditer(answer or ""))
    claims.extend(("date", match.group(0)) for match in _DATE_RE.finditer(answer or ""))
    claims.extend(("url", match.group(0)) for match in _URL_RE.finditer(answer or ""))
    claims.extend(("crn", match.group(1)) for match in _CRN_RE.finditer(answer or ""))
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for claim_type, value in claims:
        key = (claim_type, _normal(value, claim_type))
        if key[1] and key not in seen:
            seen.add(key)
            deduped.append((claim_type, value))
    return deduped


def _evidence_blob(item) -> str:
    metadata = getattr(item, "metadata", None) or {}
    structured = metadata.get("structured_result") or {}
    return "\n".join(
        (
            str(getattr(item, "title", "") or ""),
            str(getattr(item, "text", "") or ""),
            str(getattr(item, "url", "") or ""),
            json.dumps(structured, sort_keys=True, default=str),
        )
    )


def _claim_ledger(
    answer: str,
    evidence: list,
    sufficiency: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    ledger: list[ClaimSupport] = []
    for field_name, resolution in (sufficiency.get("field_resolutions") or {}).items():
        if not isinstance(resolution, dict) or resolution.get("status") != "RESOLVED":
            continue
        value = resolution.get("value")
        ledger.append(ClaimSupport(
            claim_id=f"field:{field_name}",
            claim_type="field",
            value=json.dumps(value, sort_keys=True, default=str),
            status="SUPPORTED",
            evidence_ids=[str(item) for item in resolution.get("evidence_ids") or []],
        ))

    unsupported: list[str] = []
    for index, (claim_type, value) in enumerate(_material_claims(answer), start=1):
        needle = _normal(value, claim_type)
        preferred_ids: set[str] = set()
        for resolution in (sufficiency.get("field_resolutions") or {}).values():
            if not isinstance(resolution, dict) or resolution.get("status") != "RESOLVED":
                continue
            resolved_value = resolution.get("value")
            resolved_values = resolved_value if isinstance(resolved_value, list) else [resolved_value]
            if any(
                _normal(str(candidate or ""), claim_type) == needle
                for candidate in resolved_values
            ):
                preferred_ids.update(str(item) for item in resolution.get("evidence_ids") or [])
        supporting_items: list[Any] = []
        for item in evidence:
            blob = _evidence_blob(item)
            if claim_type == "phone":
                supported = needle in re.sub(r"\D", "", blob)
            elif claim_type == "money":
                supported = needle in {
                    _normal(match.group(0), "money") for match in _MONEY_RE.finditer(blob)
                }
            elif claim_type == "crn":
                supported = bool(re.search(rf"(?<!\d){re.escape(needle)}(?!\d)", blob))
            else:
                supported = needle in _normal(blob, claim_type)
            if supported:
                supporting_items.append(item)
        preferred_items = [
            item
            for item in supporting_items
            if str(getattr(item, "evidence_id", "") or "") in preferred_ids
        ]
        if preferred_items:
            supporting_items = preferred_items
        strongest_score = max(
            (float(getattr(item, "relevance_score", 0.0) or 0.0) for item in supporting_items),
            default=None,
        )
        supporting_ids = [
            str(getattr(item, "evidence_id", "") or "")
            for item in supporting_items
            if strongest_score is not None
            and float(getattr(item, "relevance_score", 0.0) or 0.0) == strongest_score
        ]
        status = "SUPPORTED" if supporting_ids else "UNSUPPORTED"
        if not supporting_ids:
            unsupported.append(f"{claim_type}:{value}")
        digest = hashlib.sha1(f"{claim_type}:{needle}".encode("utf-8")).hexdigest()[:10]
        ledger.append(ClaimSupport(
            claim_id=f"material:{index}:{digest}",
            claim_type=claim_type,
            value=value,
            status=status,
            evidence_ids=list(dict.fromkeys(supporting_ids)),
        ))
    return [item.to_dict() for item in ledger], unsupported


def _released_evidence_ids(
    ledger: list[dict[str, Any]],
    evidence: list | None = None,
) -> set[str]:
    ids = {
        str(evidence_id)
        for claim in ledger
        if claim.get("status") in {"SUPPORTED", "DERIVED"}
        for evidence_id in claim.get("evidence_ids") or []
        if evidence_id
    }
    if ids:
        return ids
    return {
        str(getattr(item, "evidence_id", "") or "")
        for item in evidence or []
        if getattr(item, "evidence_id", None)
    }


def _derive_task_state(
    campus_query,
    evidence: list,
    sufficiency: dict[str, Any],
    release_decision: dict[str, Any],
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema_version": 1,
        "task_type": f"{campus_query.domain}:{campus_query.intent}",
        "domain": campus_query.domain,
        "status": "completed" if release_decision.get("status") != "BLOCKED" else "blocked",
        "query_anchor": campus_query.original_query[:240],
    }
    missing = list(sufficiency.get("missing_fields") or [])
    if missing:
        state["pending_fields"] = missing[:12]
        state["pending_field"] = missing[0]
    for item in evidence:
        structured = (getattr(item, "metadata", None) or {}).get("structured_result") or {}
        if structured.get("kind") != "class_planner_conflict":
            continue
        entities = structured.get("query_entities") or {}
        result = structured.get("result") or {}
        status = str(structured.get("status") or result.get("status") or "")
        state.update({
            "task_type": "course_schedule_conflict",
            "domain": "registration",
            "term": str(entities.get("term") or result.get("termLabel") or ""),
            "subject": str(entities.get("subject") or ""),
            "constraint_course": str(entities.get("constraint_course") or ""),
        })
        if status == "clarification_required":
            state["status"] = "awaiting_input"
            state["pending_field"] = "constraint_section"
            state["candidate_crns"] = [
                str(section.get("crn"))
                for section in result.get("constraintSections") or []
                if section.get("crn")
            ][:24]
        elif status == "complete":
            constraint = result.get("constraintSection") or {}
            state["status"] = "active"
            state["pending_field"] = "selected_sections"
            state["constraint_section"] = str(constraint.get("crn") or "")
            state["candidate_crns"] = [
                str(section.get("crn"))
                for section in result.get("sections") or []
                if section.get("crn")
            ][:100]
        break
    return state


async def execute_ask(
    question: str,
    *,
    use_web_search: bool = False,
    source_scope: str | None = None,
    history: list[dict[str, Any]] | None = None,
    request_context: dict[str, Any] | None = None,
    task_state: dict[str, Any] | None = None,
    persona: str | None = None,
    on_activity: OnActivity | None = None,
) -> LogicalAskResult:
    """Execute one institutional question with one authoritative CampusQuery."""
    started = time.perf_counter()
    client_state = sanitize_client_task_state(task_state)
    if not looks_like_followup(question, history, client_state):
        client_state = None
    resolved_question, conversation_context = resolve_question_with_history(
        question,
        history,
        client_state,
    )
    conversation_context["request_context"] = dict(request_context or {})
    campus_query = compile_campus_query(resolved_question)
    route_goal_matches = route_matches_goal(campus_query)

    if campus_query.clarification_required and campus_query.ambiguities:
        answer = campus_query.ambiguities[0]
        structured = structure_answer(
            question=question,
            answer=answer,
            num_results=0,
            model="clarification",
        )
        release_decision = {
            "status": "CAN_RELEASE",
            "reasons": ["CLARIFICATION_REQUIRED"],
            "evidence_passed": False,
            "partial_allowed": False,
            "failure_stage": None,
            "unsupported_material_claims": [],
        }
        task = {
            "schema_version": 1,
            "task_type": f"{campus_query.domain}:{campus_query.intent}",
            "domain": campus_query.domain,
            "status": "awaiting_input",
            "pending_field": "clarification",
            "query_anchor": campus_query.original_query[:240],
        }
        execution = {
            "schema_version": 1,
            "executor": "ask_execution_v2",
            "compiled_query": campus_query.to_dict(),
            "compiled_query_count": 1,
            "conversation_context": conversation_context,
            "route_trace": {},
            "field_resolutions": {},
            "contradictions": [],
            "targeted_recovery": {},
            "release_decision": release_decision,
        }
        return LogicalAskResult(
            question=question,
            answer=answer,
            chunks=[],
            citations=[],
            num_results=0,
            model="clarification",
            tokens_used=0,
            retrieval_ms=0,
            generation_ms=None,
            total_ms=int((time.perf_counter() - started) * 1000),
            structured=structured,
            retrieval_metadata={},
            task_state=task,
            execution=execution,
            release_decision=release_decision,
            claim_ledger=[],
            actions=[],
        )

    retrieval_started = time.perf_counter()
    retrieval_result = await run_rccs_retrieval(
        question,
        use_web_search=use_web_search,
        source_scope=source_scope,
        history=history,
        request_context=request_context,
        on_activity=on_activity,
        campus_query=campus_query,
        conversation_context=conversation_context,
    )
    retrieval_ms = int((time.perf_counter() - retrieval_started) * 1000)
    parts = result_to_pipeline_parts(retrieval_result)
    metadata = parts.get("metadata") or {}
    safe = metadata.get("safe_response") or {}
    sufficiency = safe.get("evidence_sufficiency")

    release_reasons: list[str] = []
    if not route_goal_matches:
        release_reasons.append("COMPILED_ROUTE_MISMATCH")
    if not isinstance(sufficiency, dict) or "passed" not in sufficiency:
        sufficiency = {}
        release_reasons.append("EVIDENCE_EVALUATION_UNAVAILABLE")
    contradictions = list(sufficiency.get("contradictions") or [])
    if contradictions:
        release_reasons.append("UNRESOLVED_AUTHORITATIVE_CONTRADICTION")
    passed = bool(sufficiency.get("passed"))
    partial_allowed = bool(sufficiency.get("partial_allowed")) and not contradictions
    evidence_releaseable = bool((passed or partial_allowed) and not release_reasons)
    evidence_contract_releaseable = evidence_releaseable
    accepted_ids = {
        str(item)
        for item in (sufficiency.get("accepted_evidence_ids") or [])
        if item
    }
    accepted_evidence = [
        item for item in retrieval_result.evidence
        if item.evidence_id in accepted_ids
    ]
    generation_chunks = [
        chunk for chunk in parts.get("chunk_dicts") or []
        if str(chunk.get("chunk_id") or "") in accepted_ids
    ]
    has_readable_evidence = any(
        not chunk.get("is_link_only")
        and len(str(chunk.get("text") or "").strip()) >= 120
        and "Governed campus source record" not in str(chunk.get("text") or "")
        for chunk in generation_chunks
    )

    answer = ""
    model: str | None = None
    tokens_used: int | None = None
    generation_ms: int | None = None
    if generation_chunks and evidence_releaseable and not contradictions:
        generation_started = time.perf_counter()
        fast_partial_shapes = {
            "job_list",
            "event_list",
            "calendar_list",
            "categorized_list",
            "action_link_result",
            "precise_partial",
        }
        use_fast_partial = (
            partial_allowed
            and not passed
            and not has_readable_evidence
            and (
                bool(safe.get("retrieval_budget_exhausted"))
                or str(safe.get("answer_shape") or "") in fast_partial_shapes
            )
        )
        if use_fast_partial:
            answer = render_grounded_fallback(resolved_question, generation_chunks, safe)
            model = "grounded-partial-fast"
            tokens_used = 0
        else:
            page_read = any(
                (chunk.get("metadata") or {}).get("page_read")
                or (chunk.get("metadata") or {}).get("page_fetched")
                for chunk in generation_chunks
            )
            try:
                generated = await asyncio.wait_for(
                    asyncio.to_thread(
                        generate_answer,
                        resolved_question,
                        generation_chunks,
                        persona,
                        safe,
                        history,
                    ),
                    timeout=_generation_timeout_seconds(page_read=page_read),
                )
                answer = generated.answer
                model = generated.model
                tokens_used = generated.tokens_used
            except Exception as exc:
                print(f"LLM generation failed: {type(exc).__name__}: {exc}")
                answer = render_grounded_fallback(resolved_question, generation_chunks, safe)
                model = "fallback-no-llm"
                tokens_used = 0
        generation_ms = int((time.perf_counter() - generation_started) * 1000)
    else:
        answer = (
            safe.get("precise_failure")
            or "I could not verify enough approved McNeese evidence to answer reliably."
        )
        model = "no_source"

    ledger, unsupported = _claim_ledger(
        answer,
        accepted_evidence,
        sufficiency,
    )
    fallback_models = {"fallback-no-llm", "grounded-partial-fast", "clarification", "no_source"}
    if unsupported and evidence_releaseable and model not in fallback_models:
        evidence_releaseable = False
        release_reasons.append("UNSUPPORTED_MATERIAL_CLAIM")

    approved_ids = _released_evidence_ids(ledger, retrieval_result.evidence)
    citation_validation = validate_answer_citations(
        answer,
        retrieval_result,
        evidence_ids=approved_ids,
    )
    citations = citation_validation.get("citations") or []
    if evidence_releaseable and not citation_validation.get("ok") and model not in fallback_models:
        evidence_releaseable = False
        release_reasons.append("CITATION_VALIDATION_FAILED")

    if not evidence_releaseable:
        if evidence_contract_releaseable and generation_chunks and not contradictions:
            answer = render_grounded_fallback(resolved_question, generation_chunks, safe)
            model = "fallback-no-llm"
            evidence_releaseable = True
            release_reasons.append("SYNTHESIS_UNAVAILABLE_USED_EVIDENCE")
            tokens_used = 0
            approved_ids = _released_evidence_ids([], accepted_evidence)
            citation_validation = validate_answer_citations(
                answer,
                retrieval_result,
                evidence_ids=approved_ids,
            )
            citations = citation_validation.get("citations") or []
        else:
            answer = (
                safe.get("precise_failure")
                or "I could not verify enough claim-relevant McNeese evidence to release this answer reliably."
            )
            model = "release-gated"
            tokens_used = 0
            citations = []
            approved_ids = set()

    release_status = (
        "CAN_RELEASE_PARTIAL"
        if evidence_releaseable and not passed
        else "CAN_RELEASE"
        if evidence_releaseable
        else "BLOCKED"
    )
    release_decision = {
        "status": release_status,
        "reasons": list(dict.fromkeys(release_reasons)),
        "evidence_passed": passed,
        "partial_allowed": partial_allowed,
        "failure_stage": "release" if release_status == "BLOCKED" else None,
        "unsupported_material_claims": unsupported,
    }
    task = _derive_task_state(
        campus_query,
        retrieval_result.evidence,
        sufficiency,
        release_decision,
    )
    chunks = [
        chunk
        for chunk in parts.get("chunk_responses") or []
        if str(chunk.get("chunk_id") or "") in approved_ids
    ]
    structured = structure_answer(
        question=question,
        answer=answer,
        num_results=len(chunks),
        model=model,
    )
    # The legacy formatter inferred "partial" from answer length and citation
    # count.  The executor now owns that decision: a completed, fully released
    # task is factual even when one authoritative page is sufficient.  Tasks
    # still awaiting a user selection (for example a planner CRN) remain partial.
    if (
        release_status == "CAN_RELEASE"
        and task.get("status") == "completed"
        and structured.get("answer_type") == "partial"
    ):
        structured["answer_type"] = "factual"
    total_ms = int((time.perf_counter() - started) * 1000)
    execution = {
        "schema_version": 1,
        "executor": "ask_execution_v2",
        "compiled_query": campus_query.to_dict(),
        "compiled_query_count": 1,
        "conversation_context": conversation_context,
        "route_trace": metadata.get("route_trace") or {},
        "field_resolutions": sufficiency.get("field_resolutions") or {},
        "contradictions": contradictions,
        "targeted_recovery": metadata.get("targeted_recovery") or {},
        "release_decision": release_decision,
    }
    safe["release_decision"] = release_decision
    safe["claim_ledger"] = ledger
    return LogicalAskResult(
        question=question,
        answer=answer,
        chunks=chunks,
        citations=citations,
        num_results=len(chunks),
        model=model,
        tokens_used=tokens_used,
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
        total_ms=total_ms,
        structured=structured,
        retrieval_metadata=safe,
        task_state=task,
        execution=execution,
        release_decision=release_decision,
        claim_ledger=ledger,
        actions=[],
    )
