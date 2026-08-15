"""POST /ask â€” Full RAG pipeline with Claude answer generation.



Pipeline: Question â†’ Web Search OR ChromaDB retrieval â†’ Claude generation â†’ Answer with citations

Supports both regular POST and Server-Sent Events (SSE) streaming.



The system supports TWO modes (selected by use_web_search):

1. Knowledge Base (default, use_web_search=false): Pre-indexed ChromaDB content

2. Live Web Search (optional, use_web_search=true): Searches mcneese.edu in real time

"""



from __future__ import annotations



import asyncio

import json

import re

import time

import traceback

from typing import AsyncGenerator



from fastapi import APIRouter, HTTPException, Request

from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field, field_validator



from app.routers import guest as guest_router
from app.services.retrieval import search_chunks, get_collection_stats, RetrievedChunk

from app.services.query_logger import (

    create_query_id,

    log_full_query,

    get_pipeline_stats,

    debug_trace_enabled,

)

from app.services.query_expansion import expand_query

from app.services.llm import generate_answer, generate_answer_stream, check_api_key, CLAUDE_MODEL

from app.services.web_search import search_and_fetch, pages_to_context, FetchedPage

from app.services.intent import classify_intent, Intent
from app.services.conversation_context import build_request_context

from app.services.persona import (

    detect_persona,

    needs_clarification,

    clarification_question,

    already_clarified,

)

from app.services.answer_format import format_chunks_as_answer, _format_web_results

from app.services.grounded_fallback import render_grounded_fallback

from app.services.activity_events import (

    activity_payload,

    operation_activity,

    SAFE_MESSAGES,

    REQUEST_ACCEPTED,

    QUERY_ANALYZING,

    RETRIEVAL_STARTED,

    RETRIEVAL_SOURCE_FOUND,

    RETRIEVAL_COMPLETED,

    ANSWER_GENERATING,

    CITATIONS_VALIDATING,

    ANSWER_COMPLETED,

    REQUEST_FAILED,

    source_activities_from_citations,

    source_preview_from_citations,

)

from app.services.structured_answer import structure_answer

from app.services.rccs.ask_integration import (
    rccs_enabled,
    run_rccs_retrieval,
    result_to_pipeline_parts,
    validate_answer_citations,
)
from app.services.rccs.config import flags_snapshot as rccs_flags_snapshot
from app.services.orchestrator.config import (
    flags_snapshot as supervisor_flags_snapshot,
    supervisor_enabled,
)

from app.services.campus_intelligence.registry import capability_snapshot
from app.services.index_manifest import get_index_manifest_summary
from app.services.ask_execution import (
    execute_ask,
    execution_v2_enabled,
    sanitize_client_task_state,
)

from app.services.capabilities import (
    capability_answer_text,
    is_capability_question,
    retrieval_capabilities,
)

from app.services.test_case_recorder import (
    begin_run as begin_test_case_run,
    finalize_run as finalize_test_case_run,
    synthesize_activity_from_meta,
    classification_snapshot,
)





router = APIRouter(prefix="/ask", tags=["ask"])


def _sources_from_chunks(chunks) -> list[dict]:
    out = []
    for c in chunks or []:
        if hasattr(c, "model_dump"):
            d = c.model_dump()
        elif isinstance(c, dict):
            d = c
        else:
            d = {
                "title": getattr(c, "title", ""),
                "source_url": getattr(c, "source_url", ""),
                "category": getattr(c, "category", ""),
                "retrieval_channel": getattr(c, "retrieval_channel", None),
                "source_tier": getattr(c, "source_tier", None),
                "trust_level": getattr(c, "trust_level", None),
            }
        out.append(d)
    return out


def _planner_actions(question: str, parts: dict, history: list | None = None) -> list[dict]:
    """Build an explicit, user-requested Class Planner handoff from validated sections."""
    if not re.search(r"\b(?:put|add|save)\b.{0,50}\bclass planner\b", question or "", re.I):
        return []
    requested_crns = set(re.findall(r"(?<!\d)(\d{5})(?!\d)", question or ""))
    # "Put these in Class Planner" refers to the student's most recent explicit
    # CRN selection.  Resolve that reference without guessing from assistant text
    # or silently adding every result in the prior list.
    if not requested_crns and re.search(r"\b(?:these|them|those)\b", question or "", re.I):
        for turn in reversed(history or []):
            role = turn.get("role") if isinstance(turn, dict) else getattr(turn, "role", None)
            content = turn.get("content") if isinstance(turn, dict) else getattr(turn, "content", "")
            if role != "user":
                continue
            requested_crns = set(re.findall(r"(?<!\d)(\d{5})(?!\d)", str(content or "")))
            if requested_crns:
                break
    if not requested_crns:
        return []
    for chunk in parts.get("chunk_dicts") or []:
        metadata = chunk.get("metadata") or {}
        if metadata.get("structured_execution") != "class_planner_conflict":
            continue
        result = metadata.get("result") or {}
        if result.get("status") != "complete" or not result.get("termId"):
            continue
        candidates = [result.get("constraintSection"), *(result.get("sections") or [])]
        matched = [
            section for section in candidates
            if isinstance(section, dict) and str(section.get("crn") or "") in requested_crns
        ]
        if requested_crns - {str(section.get("crn") or "") for section in matched}:
            return []
        constraint = result.get("constraintSection")
        if isinstance(constraint, dict) and constraint not in matched:
            matched.insert(0, constraint)
        deduped = list({str(section.get("id")): section for section in matched if section.get("id")}.values())
        return [{
            "type": "class_planner_add",
            "term_id": str(result["termId"]),
            "sections": deduped,
            "source": "validated_class_planner",
        }]
    return []


def _record_test_case_finish(
    *,
    question: str,
    use_web_search: bool,
    answer: str,
    answer_type: str | None = None,
    model: str | None = None,
    num_results: int | None = None,
    retrieval_mode: str | None = None,
    retrieval_channels: list | None = None,
    used_companion_sources: list | None = None,
    checked_source_categories: list | None = None,
    freshness_status: str | None = None,
    web_search_executed: bool | None = None,
    sources: list | None = None,
    citations: list | None = None,
    error: str | None = None,
    total_ms: int | None = None,
    synthesize: bool = False,
    social_hint: bool = False,
) -> None:
    """Append one test-case block; safe no-op when recording is off."""
    try:
        if synthesize:
            synthesize_activity_from_meta(
                query_id="",
                mode="rccs_hybrid" if retrieval_mode else ("web_search" if use_web_search else "knowledge_base"),
                sources_found=int(num_results or 0),
                social=social_hint,
            )
        class_d, plan_d = classification_snapshot(question, use_web_search)
        finalize_test_case_run(
            answer=answer or "",
            answer_type=answer_type,
            model=model,
            num_results=num_results,
            retrieval_mode=retrieval_mode,
            retrieval_channels=retrieval_channels,
            used_companion_sources=used_companion_sources,
            checked_source_categories=checked_source_categories,
            freshness_status=freshness_status,
            web_search_executed=web_search_executed,
            classification=class_d,
            plan=plan_d,
            flags={**rccs_flags_snapshot(), **supervisor_flags_snapshot()},
            sources=sources or [],
            citations=citations or [],
            error=error,
            total_ms=total_ms,
        )
    except Exception as exc:
        print(f"test_case_recorder finalize failed: {exc}")






class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's question",
    )
    stream: bool = Field(default=False, description="Whether to stream the response")
    use_web_search: bool = Field(
        default=False,
        description="Legacy flag; prefer source_scope. True for adaptive/web.",
    )
    source_scope: str | None = Field(
        default=None,
        max_length=32,
        description="adaptive | knowledge | web — controls planner, page-open, and external discovery",
    )
    history: list[dict] | None = Field(
        default=None,
        max_length=20,
        description="At most 20 prior user/assistant turns",
    )
    request_id: str | None = Field(default=None, max_length=96)
    conversation_id: str | None = Field(default=None, max_length=96)
    turn_id: str | None = Field(default=None, max_length=96)
    parent_turn_id: str | None = Field(default=None, max_length=96)
    run_id: str | None = Field(default=None, max_length=96)
    user_message_id: str | None = Field(default=None, max_length=96)
    assistant_message_id: str | None = Field(default=None, max_length=96)
    task_state: dict | None = Field(
        default=None,
        description="Untrusted task-selection/context hints; backend facts are rehydrated.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must contain non-whitespace characters")
        return cleaned

    @field_validator("history")
    @classmethod
    def validate_history(cls, value: list[dict] | None) -> list[dict] | None:
        if value is None:
            return None
        normalized: list[dict] = []
        for turn in value:
            if not isinstance(turn, dict):
                raise ValueError("history turns must be objects")
            role = turn.get("role")
            content = turn.get("content")
            if role not in {"user", "assistant"}:
                raise ValueError("history role must be user or assistant")
            if not isinstance(content, str):
                raise ValueError("history content must be a string")
            content = content.strip()
            # Drop empty provisional/assistant shells instead of rejecting the whole ask.
            if not content:
                continue
            if len(content) > 4000:
                raise ValueError("history content must be at most 4000 characters")
            normalized.append({"role": role, "content": content})
        return normalized or None

    @field_validator("task_state")
    @classmethod
    def validate_task_state(cls, value: dict | None) -> dict | None:
        return sanitize_client_task_state(value)

def _resolve_request_id(value: str | None, *, max_len: int = 96) -> str | None:

    """Accept a client correlation id when it is short and safe; otherwise ignore."""

    if not value or not isinstance(value, str):

        return None

    cleaned = value.strip()

    if not cleaned or len(cleaned) > max_len:

        return None

    if not re.fullmatch(r"[A-Za-z0-9._:-]+", cleaned):

        return None

    return cleaned


class ChunkResponse(BaseModel):

    chunk_id: str

    text: str

    source_url: str

    title: str

    category: str

    score: float

    source_tier: str | None = None

    trust_level: str | None = None

    retrieval_channel: str | None = None

    is_link_only: bool | None = None

    source_id: str | None = None





class AskResponse(BaseModel):

    question: str

    answer: str

    chunks: list[ChunkResponse]

    num_results: int

    query_id: str

    model: str | None = None

    tokens_used: int | None = None

    retrieval_ms: int

    generation_ms: int | None = None

    total_ms: int

    answer_type: str | None = None

    title: str | None = None

    summary: str | None = None

    content_markdown: str | None = None

    key_facts: list[dict] | None = None

    important_dates: list[dict] | None = None

    requirements: list[str] | None = None

    steps: list[str] | None = None

    warnings: list[str] | None = None

    related_questions: list[str] | None = None

    confidence: str | None = None

    retrieval_mode: str | None = None

    checked_source_categories: list[str] | None = None

    used_companion_sources: list[str] | None = None

    freshness_status: str | None = None

    requested_mode: str | None = None

    effective_mode: str | None = None

    retrieval_channels: list[str] | None = None

    web_search_executed: bool | None = None

    web_search_status: str | None = None

    matched_source_ids: list[str] | None = None

    source_count: int | None = None

    actions: list[dict] | None = None
    sources: list[dict] | None = None
    task_state: dict | None = None
    execution: dict | None = None
    release_decision: dict | None = None
    claim_ledger: list[dict] | None = None





@router.post("")

async def ask(body: AskRequest, request: Request):

    """

    Ask a question and get an AI-generated answer from McNeese sources.

    

    Pipeline steps:

    1. Search for relevant content (web search OR knowledge base)

    2. Fetch and read actual page content

    3. Generate answer using Claude with real context

    4. Return answer with citations (real URLs)

    

    Set stream=true for Server-Sent Events streaming response.

    use_web_search defaults to false (knowledge base). Set true for optional live web search.

    """

    guest_router.claim_question_allowance(request)
    request_context = build_request_context(
        body.question,
        conversation_id=body.conversation_id,
        turn_id=body.turn_id,
        parent_turn_id=body.parent_turn_id,
        request_id=body.request_id,
    )

    if body.stream:

        return StreamingResponse(

            ask_stream(

                body.question,

                body.use_web_search,

                body.history,

                request_id=body.request_id,

                run_id=body.run_id,

                source_scope=body.source_scope,
                request_context=request_context,
                task_state=body.task_state,

            ),

            media_type="text/event-stream",

            headers={

                "Cache-Control": "no-cache",

                "Connection": "keep-alive",

                "X-Accel-Buffering": "no",

            }

        )

    

    query_id = _resolve_request_id(body.request_id) or create_query_id()

    begin_test_case_run(
        query_id=query_id,
        question=body.question,
        use_web_search=bool(body.use_web_search),
        stream=False,
    )

    start_time = time.perf_counter()

    retrieval_ms = 0

    generation_ms = 0

    chunk_responses = []

    sources_found = 0

    kb_chunks: list[RetrievedChunk] = []

    

    # Handle greetings / small talk directly (no web search, no LLM needed)

    intent_result = classify_intent(body.question)

    if intent_result.intent != Intent.QUESTION:

        total_ms = int((time.perf_counter() - start_time) * 1000)

        return AskResponse(

            question=body.question,

            chunks=[],

            num_results=0,

            query_id=query_id,

            model="conversational",

            tokens_used=0,

            retrieval_ms=0,

            generation_ms=None,

            total_ms=total_ms,

            **structure_answer(

                question=body.question,

                answer=intent_result.reply,

                num_results=0,

                model="conversational",

            ),

        )



    # Persona-clarification branch: for applicant-category-dependent questions

    # (scholarships, admissions, "how do I apply") where the stage is ambiguous,

    # ask ONE clarifying question instead of a generic everyone-answer.

    if needs_clarification(
        body.question,
        body.history,
        include_campus_intelligence=not (rccs_enabled() and execution_v2_enabled()),
    ) and not already_clarified(body.history):

        total_ms = int((time.perf_counter() - start_time) * 1000)

        clarification_answer = clarification_question(
            body.question,
            body.history,
            include_campus_intelligence=not (rccs_enabled() and execution_v2_enabled()),
        )

        return AskResponse(

            question=body.question,

            chunks=[],

            num_results=0,

            query_id=query_id,

            model="clarification",

            tokens_used=0,

            retrieval_ms=0,

            generation_ms=None,

            total_ms=total_ms,

            **structure_answer(

                question=body.question,

                answer=clarification_answer,

                num_results=0,

                model="clarification",

            ),

        )




    persona = detect_persona(body.question, body.history)



    if is_capability_question(body.question):

        answer = capability_answer_text(use_web_search=body.use_web_search)

        total_ms = int((time.perf_counter() - start_time) * 1000)

        caps = retrieval_capabilities()

        return AskResponse(

            question=body.question,

            chunks=[],

            num_results=0,

            query_id=query_id,

            model="capability",

            tokens_used=0,

            retrieval_ms=0,

            generation_ms=0,

            total_ms=total_ms,

            requested_mode="web" if body.use_web_search else "knowledge",

            effective_mode="capability",

            retrieval_channels=[],

            web_search_executed=False,

            web_search_status="not_requested",

            **structure_answer(

                question=body.question,

                answer=answer,

                num_results=0,

                model="capability",

            ),

        )



    try:

        if rccs_enabled() and execution_v2_enabled():
            logical = await execute_ask(
                body.question,
                use_web_search=body.use_web_search,
                source_scope=body.source_scope,
                history=body.history,
                request_context=request_context,
                task_state=body.task_state,
                persona=persona,
            )
            chunk_responses = [ChunkResponse(**chunk) for chunk in logical.chunks]
            safe_meta = logical.retrieval_metadata
            log_full_query(
                query_id=query_id,
                question=body.question,
                chunks=chunk_responses,
                retrieval_ms=logical.retrieval_ms,
                generation_ms=logical.generation_ms,
                answer_model=logical.model,
                answer_tokens=logical.tokens_used,
                final_status=(
                    "success"
                    if logical.release_decision.get("status") != "BLOCKED"
                    else "release_blocked"
                ),
                error_step=(
                    logical.release_decision.get("failure_stage")
                    if logical.release_decision.get("status") == "BLOCKED"
                    else None
                ),
                error_message=(
                    ",".join(logical.release_decision.get("reasons") or []) or None
                ),
                route_trace=logical.execution.get("route_trace"),
                task_type=(logical.task_state or {}).get("task_type"),
                release_decision=logical.release_decision,
                field_resolution_statuses={
                    key: str(value.get("status") or "")
                    for key, value in (logical.execution.get("field_resolutions") or {}).items()
                    if isinstance(value, dict)
                },
                contradiction_count=len(logical.execution.get("contradictions") or []),
                claim_count=len(logical.claim_ledger),
                recovery_attempted=bool(logical.execution.get("targeted_recovery")),
            )
            _record_test_case_finish(
                question=body.question,
                use_web_search=bool(body.use_web_search),
                answer=logical.answer,
                answer_type=logical.structured.get("answer_type"),
                model=logical.model,
                num_results=logical.num_results,
                retrieval_mode=safe_meta.get("retrieval_mode"),
                retrieval_channels=safe_meta.get("retrieval_channels"),
                used_companion_sources=safe_meta.get("used_companion_sources"),
                checked_source_categories=safe_meta.get("checked_source_categories"),
                freshness_status=safe_meta.get("freshness_status"),
                web_search_executed=safe_meta.get("web_search_executed"),
                sources=_sources_from_chunks(chunk_responses),
                citations=logical.citations,
                total_ms=logical.total_ms,
                synthesize=False,
            )
            return AskResponse(
                question=body.question,
                chunks=chunk_responses,
                num_results=logical.num_results,
                query_id=query_id,
                model=logical.model,
                tokens_used=logical.tokens_used,
                retrieval_ms=logical.retrieval_ms,
                generation_ms=logical.generation_ms,
                total_ms=logical.total_ms,
                retrieval_mode=safe_meta.get("retrieval_mode"),
                checked_source_categories=safe_meta.get("checked_source_categories"),
                used_companion_sources=safe_meta.get("used_companion_sources"),
                freshness_status=safe_meta.get("freshness_status"),
                requested_mode=safe_meta.get("requested_mode"),
                effective_mode=safe_meta.get("effective_mode"),
                retrieval_channels=safe_meta.get("retrieval_channels"),
                web_search_executed=safe_meta.get("web_search_executed"),
                web_search_status=safe_meta.get("web_search_status"),
                matched_source_ids=safe_meta.get("matched_source_ids"),
                source_count=logical.num_results,
                actions=logical.actions or None,
                sources=logical.citations or None,
                task_state=logical.task_state,
                execution=logical.execution,
                release_decision=logical.release_decision,
                claim_ledger=logical.claim_ledger,
                **logical.structured,
            )

        retrieval_start = time.perf_counter()

        

        if rccs_enabled():

            rccs_result = await run_rccs_retrieval(

                body.question,

                use_web_search=body.use_web_search,

                source_scope=body.source_scope,

                history=body.history,
                request_context=request_context,

            )

            parts = result_to_pipeline_parts(rccs_result)
            planner_actions = _planner_actions(body.question, parts, body.history)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = parts["sources_found"]

            chunk_responses = [

                ChunkResponse(

                    chunk_id=c["chunk_id"],

                    text=c["text"],

                    source_url=c["source_url"],

                    title=c["title"],

                    category=c["category"],

                    score=c["score"],

                    source_tier=c.get("source_tier"),

                    trust_level=c.get("trust_level"),

                    retrieval_channel=c.get("retrieval_channel"),

                    is_link_only=c.get("is_link_only"),

                    source_id=c.get("source_id"),

                )

                for c in parts["chunk_responses"]

            ]

            answer = ""

            model = None

            tokens_used = None

            generation_ms = None

            generation_error: str | None = None

            _safe_response_meta = (parts.get("metadata") or {}).get("safe_response") or {}
            _evidence_sufficiency = _safe_response_meta.get("evidence_sufficiency") or {}
            _evidence_releaseable = bool(
                _evidence_sufficiency.get("passed", True)
                or _evidence_sufficiency.get("partial_allowed", False)
            )

            if parts["chunk_dicts"] and _evidence_releaseable:

                generation_start = time.perf_counter()

                try:

                    _ctx = ((parts.get("metadata") or {}).get("conversation_context") or {})
                    _answer_q = _ctx.get("resolved_question") or body.question
                    result = await asyncio.to_thread(

                        generate_answer,

                        _answer_q,

                        parts["chunk_dicts"],

                        persona,

                        (parts.get("metadata") or {}).get("safe_response"),

                        body.history,

                    )

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = result.answer

                    model = result.model

                    tokens_used = result.tokens_used

                except Exception as llm_error:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    generation_error = f"{type(llm_error).__name__}: {llm_error}"
                    print(f"LLM generation failed (RCCS): {generation_error}")
                    traceback.print_exc()

                    answer = (

                        render_grounded_fallback(
                            body.question, parts["chunk_dicts"],
                            (parts.get("metadata") or {}).get("safe_response"),
                        )

                    )

                    model = "fallback-no-llm"

                    tokens_used = 0

            else:

                answer = (
                    _safe_response_meta.get("precise_failure")
                    or "I could not verify enough approved McNeese evidence to answer reliably."
                )

                model = "no_source"

                tokens_used = None

            citation_validation = validate_answer_citations(answer, rccs_result)
            parts["citations"] = citation_validation.get("citations") or []
            if not _evidence_releaseable:
                parts["citations"] = []
                chunk_responses = []
                sources_found = 0
            if not citation_validation.get("ok"):
                parts["citations"] = []
                answer = (
                    (((parts.get("metadata") or {}).get("safe_response") or {}).get("precise_failure"))
                    or "I could not verify enough claim-relevant McNeese evidence to release this answer reliably."
                )
                model = "citation-gated"
                tokens_used = 0

            total_ms = int((time.perf_counter() - start_time) * 1000)

            safe_meta = _safe_response_meta

            debug_kwargs: dict = {
                "route_trace": (parts.get("metadata") or {}).get("route_trace"),
            }

            if debug_trace_enabled():

                debug_kwargs.update({

                    "intent": intent_result.intent.value,

                    "persona": persona,

                    "expanded_queries": expand_query(body.question),

                    "rerank_scores": [round(c.score, 3) for c in chunk_responses],

                    "mode": "rccs_hybrid",

                })

            log_full_query(

                query_id=query_id,

                question=body.question,

                chunks=chunk_responses,

                retrieval_ms=retrieval_ms,

                generation_ms=generation_ms if sources_found else None,

                answer_model=model,

                answer_tokens=tokens_used,

                final_status="generation_error" if generation_error else ("success" if sources_found else "no_results"),

                error_step="generation" if generation_error else None,

                error_message=generation_error,

                **debug_kwargs,

            )

            
            _structured = structure_answer(
                question=body.question,
                answer=answer,
                num_results=sources_found,
                model=model,
            )
            _record_test_case_finish(
                question=body.question,
                use_web_search=bool(body.use_web_search),
                answer=answer,
                answer_type=_structured.get("answer_type"),
                model=model,
                num_results=sources_found,
                retrieval_mode=safe_meta.get("retrieval_mode"),
                retrieval_channels=safe_meta.get("retrieval_channels"),
                used_companion_sources=safe_meta.get("used_companion_sources"),
                checked_source_categories=safe_meta.get("checked_source_categories"),
                freshness_status=safe_meta.get("freshness_status"),
                web_search_executed=safe_meta.get("web_search_executed"),
                sources=_sources_from_chunks(chunk_responses),
                citations=parts.get("citations") or [],
                total_ms=total_ms,
                synthesize=True,
                social_hint=bool(safe_meta.get("used_companion_sources"))
                or "social" in (safe_meta.get("checked_source_categories") or []),
            )
            return AskResponse(

                question=body.question,

                chunks=chunk_responses,

                num_results=sources_found,

                query_id=query_id,

                model=model,

                tokens_used=tokens_used,

                retrieval_ms=retrieval_ms,

                generation_ms=generation_ms if sources_found else None,

                total_ms=total_ms,

                retrieval_mode=safe_meta.get("retrieval_mode"),

                checked_source_categories=safe_meta.get("checked_source_categories"),

                used_companion_sources=safe_meta.get("used_companion_sources"),

                freshness_status=safe_meta.get("freshness_status"),

                requested_mode=safe_meta.get("requested_mode"),

                effective_mode=safe_meta.get("effective_mode"),

                retrieval_channels=safe_meta.get("retrieval_channels"),

                web_search_executed=safe_meta.get("web_search_executed"),

                web_search_status=safe_meta.get("web_search_status"),

                matched_source_ids=safe_meta.get("matched_source_ids"),

                source_count=safe_meta.get("source_count"),

                actions=planner_actions or None,

                **_structured,

            )

        if body.use_web_search:


            # LIVE WEB SEARCH MODE

            # Search mcneese.edu and fetch real page content

            fetched_pages = await search_and_fetch(body.question, max_pages=5)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            

            if fetched_pages:

                context, sources = pages_to_context(fetched_pages)

                sources_found = len(fetched_pages)

                

                # Convert to chunk responses for compatibility

                chunk_responses = [

                    ChunkResponse(

                        chunk_id=s["id"],

                        text=s["snippet"],

                        source_url=s["url"],

                        title=s["title"],

                        category="web-search",

                        score=1.0,

                    )

                    for s in sources

                ]

                

                # Generate answer from fetched content

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": page.content, "title": page.title, "source_url": page.url}

                    for page in fetched_pages

                ]

                

                try:

                    result = await asyncio.to_thread(

                        generate_answer,

                        body.question,

                        chunk_dicts,

                        persona=persona,

                    )

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = result.answer

                    model = result.model

                    tokens_used = result.tokens_used

                except Exception as llm_error:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    # Fallback: summarize fetched content

                    answer = _format_web_results(fetched_pages, body.question)

                    model = "fallback-no-llm"

                    tokens_used = 0

            else:

                answer = "I couldn't find relevant information about that on the McNeese website. Please try rephrasing your question or ask about specific topics like admissions, programs, financial aid, or campus services."

                model = None

                tokens_used = None

        else:

            # KNOWLEDGE BASE MODE (original behavior)

            chunks = search_chunks(body.question)

            kb_chunks = chunks

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(chunks)

            

            chunk_responses = [

                ChunkResponse(

                    chunk_id=c.chunk_id,

                    text=c.text,

                    source_url=c.source_url,

                    title=c.title,

                    category=c.category,

                    score=c.score,

                )

                for c in chunks

            ]

            

            if chunks:

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": c.text, "title": c.title, "source_url": c.source_url}

                    for c in chunks

                ]

                

                try:

                    result = await asyncio.to_thread(

                        generate_answer,

                        body.question,

                        chunk_dicts,

                        persona=persona,

                    )

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = result.answer

                    model = result.model

                    tokens_used = result.tokens_used

                except Exception:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = format_chunks_as_answer(chunks, body.question)

                    model = "fallback-no-llm"

                    tokens_used = 0

            else:

                answer = "I couldn't find relevant information in the knowledge base. Try using web search mode for broader coverage."

                model = None

                tokens_used = None

        

        total_ms = int((time.perf_counter() - start_time) * 1000)

        

        # Web pages are FetchedPage objects, not RetrievedChunk; log schema differs.

        log_chunks = [] if body.use_web_search else kb_chunks

        # Debug-trace extras: only computed/passed when the flag is enabled so the

        # default log stays minimal and no extra work runs in normal operation.

        debug_kwargs: dict = {}

        if debug_trace_enabled():

            debug_kwargs = {

                "intent": intent_result.intent.value,

                "persona": persona,

                "expanded_queries": expand_query(body.question),

                "rerank_scores": [round(c.score, 3) for c in chunk_responses],

                "mode": "web_search" if body.use_web_search else "knowledge_base",

            }

        log_full_query(

            query_id=query_id,

            question=body.question,

            chunks=log_chunks,

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            answer_model=model,

            answer_tokens=tokens_used,

            final_status="success" if sources_found else "no_results",

            **debug_kwargs,

        )

        

        return AskResponse(

            question=body.question,

            chunks=chunk_responses,

            num_results=sources_found,

            query_id=query_id,

            model=model,

            tokens_used=tokens_used,

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            total_ms=total_ms,

            **structure_answer(

                question=body.question,

                answer=answer,

                num_results=sources_found,

                model=model,

            ),

        )

        

    except Exception as e:

        total_ms = int((time.perf_counter() - start_time) * 1000)

        log_full_query(

            query_id=query_id,

            question=body.question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            final_status="error",

            error_step="pipeline",

            error_message=str(e),

        )

        raise HTTPException(
            status_code=500,
            detail=f"The request could not be completed. Reference: {query_id}",
        )





async def ask_stream(question: str, use_web_search: bool = False,

                     history: list[dict] | None = None,

                     request_id: str | None = None,

                     run_id: str | None = None,
                     source_scope: str | None = None,
                     request_context: dict | None = None,
                     task_state: dict | None = None) -> AsyncGenerator[str, None]:

    """

    Stream the response using Server-Sent Events.

    

    Events:

    - step: Pipeline step updates (search, fetch, generation)

    - chunk: Text chunks as they're generated

    - citations: Source citations with real URLs

    - done: Final response metadata

    - error: Error information

    """

    query_id = _resolve_request_id(request_id) or create_query_id()

    begin_test_case_run(
        query_id=query_id,
        question=question,
        use_web_search=bool(use_web_search),
        stream=True,
    )

    client_run_id = _resolve_request_id(run_id)
    request_context = dict(request_context or build_request_context(question, request_id=query_id))
    event_sequence = 0

    start_time = time.perf_counter()

    retrieval_ms = 0

    generation_ms = 0

    sources_found = 0

    full_answer = ""
    route_trace = None

    

    def send_event(event: str, data: dict) -> str:
        nonlocal event_sequence
        event_sequence += 1
        envelope = dict(data)
        envelope.update(
            {
                "request_id": query_id,
                "conversation_id": request_context.get("conversation_id"),
                "turn_id": request_context.get("turn_id"),
                "attempt_id": client_run_id or query_id,
                "sequence": event_sequence,
                "event_id": f"{query_id}:{event_sequence}",
                "event_type": event,
                "status": envelope.get("status") or (
                    "complete" if event == "done" else "failed" if event == "error" else "in_progress"
                ),
            }
        )
        return f"event: {event}\ndata: {json.dumps(envelope)}\n\n"

    def emit_activity(

        event: str,

        message: str | None = None,

        metadata: dict | None = None,

    ) -> str:

        return send_event(

            "activity",

            activity_payload(

                query_id,

                event,

                start_time,

                message=message,

                metadata=metadata,

                run_id=client_run_id,

            ),

        )

    yield emit_activity(REQUEST_ACCEPTED)

    

    # Handle greetings / small talk directly (no web search, no LLM needed)

    intent_result = classify_intent(question)

    if intent_result.intent != Intent.QUESTION:

        full_answer = intent_result.reply

        yield send_event("chunk", {"text": full_answer})

        total_ms = int((time.perf_counter() - start_time) * 1000)

        yield send_event(

            "activity",

            activity_payload(query_id, ANSWER_COMPLETED, start_time, metadata={"num_results": 0, "mode": "conversational"}),

        )

        yield send_event("done", {

            "query_id": query_id,

            "num_results": 0,

            "retrieval_ms": 0,

            "generation_ms": 0,

            "total_ms": total_ms,

            "mode": "conversational",

            **structure_answer(

                question=question,

                answer=full_answer,

                num_results=0,

                model="conversational",

            ),

        })

        return



    # Persona-clarification branch (ask ONE question when stage is ambiguous).

    if needs_clarification(
        question,
        history,
        include_campus_intelligence=not (rccs_enabled() and execution_v2_enabled()),
    ) and not already_clarified(history):

        full_answer = clarification_question(
            question,
            history,
            include_campus_intelligence=not (rccs_enabled() and execution_v2_enabled()),
        )

        yield send_event("chunk", {"text": full_answer})

        total_ms = int((time.perf_counter() - start_time) * 1000)

        yield send_event(

            "activity",

            activity_payload(query_id, ANSWER_COMPLETED, start_time, metadata={"num_results": 0, "mode": "clarification"}),

        )

        yield send_event("done", {

            "query_id": query_id,

            "num_results": 0,

            "retrieval_ms": 0,

            "generation_ms": 0,

            "total_ms": total_ms,

            "mode": "clarification",

            **structure_answer(

                question=question,

                answer=full_answer,

                num_results=0,

                model="clarification",

            ),

        })

        return



    persona = detect_persona(question, history)



    if is_capability_question(question):

        answer = capability_answer_text(use_web_search=use_web_search)

        yield send_event("chunk", {"text": answer})

        structured = structure_answer(

            question=question,

            answer=answer,

            num_results=0,

            model="capability",

        )

        total_ms = int((time.perf_counter() - start_time) * 1000)

        yield send_event("done", {

            "query_id": query_id,

            "num_results": 0,

            "retrieval_ms": 0,

            "generation_ms": 0,

            "total_ms": total_ms,

            "mode": "capability",

            "requested_mode": "web" if use_web_search else "knowledge",

            "effective_mode": "capability",

            "retrieval_channels": [],

            "web_search_executed": False,

            "web_search_status": "not_requested",

            **structured,

        })

        return



    try:

        yield send_event(

            "activity",

            activity_payload(query_id, QUERY_ANALYZING, start_time),

        )

        if rccs_enabled():
            if execution_v2_enabled():
                yield send_event("step", {
                    "step": "search",
                    "status": "started",
                    "message": "Choosing and checking trusted McNeese sources",
                })
                activity_q: asyncio.Queue = asyncio.Queue()

                def _on_execution_activity(event: str, metadata=None, message=None):
                    activity_q.put_nowait((event, metadata, message))

                execution_task = asyncio.create_task(execute_ask(
                    question,
                    use_web_search=use_web_search,
                    source_scope=source_scope,
                    history=history,
                    request_context=request_context,
                    task_state=task_state,
                    persona=persona,
                    on_activity=_on_execution_activity,
                ))
                while not execution_task.done():
                    try:
                        ev_name, ev_meta, ev_msg = await asyncio.wait_for(
                            activity_q.get(), timeout=0.15
                        )
                        yield send_event(
                            "activity",
                            activity_payload(
                                query_id,
                                ev_name,
                                start_time,
                                message=ev_msg,
                                metadata=ev_meta,
                            ),
                        )
                    except asyncio.TimeoutError:
                        continue
                while not activity_q.empty():
                    ev_name, ev_meta, ev_msg = activity_q.get_nowait()
                    yield send_event(
                        "activity",
                        activity_payload(
                            query_id,
                            ev_name,
                            start_time,
                            message=ev_msg,
                            metadata=ev_meta,
                        ),
                    )
                logical = await execution_task
                safe_meta = logical.retrieval_metadata
                sources_found = logical.num_results
                route_trace = logical.execution.get("route_trace")
                for src_ev in source_activities_from_citations(
                    query_id,
                    start_time,
                    logical.citations,
                    operation_id="cite-executor-v2",
                    source_type="official",
                    sources_found=sources_found,
                    run_id=client_run_id,
                ):
                    yield send_event("activity", src_ev)
                yield send_event("step", {
                    "step": "search",
                    "status": "completed",
                    "message": f"Verified {sources_found} claim-relevant source{'s' if sources_found != 1 else ''}",
                    "duration_ms": logical.retrieval_ms,
                })
                yield send_event("chunk", {"text": logical.answer})
                yield send_event("citations", {"citations": logical.citations})
                yield send_event(
                    "activity",
                    activity_payload(
                        query_id,
                        ANSWER_COMPLETED,
                        start_time,
                        metadata={
                            "sources_found": sources_found,
                            "release_status": logical.release_decision.get("status"),
                        },
                    ),
                )
                logged_chunks = [ChunkResponse(**chunk) for chunk in logical.chunks]
                log_full_query(
                    query_id=query_id,
                    question=question,
                    chunks=logged_chunks,
                    retrieval_ms=logical.retrieval_ms,
                    generation_ms=logical.generation_ms,
                    answer_model=logical.model,
                    answer_tokens=logical.tokens_used,
                    final_status=(
                        "success"
                        if logical.release_decision.get("status") != "BLOCKED"
                        else "release_blocked"
                    ),
                    error_step=logical.release_decision.get("failure_stage"),
                    error_message=(
                        ",".join(logical.release_decision.get("reasons") or []) or None
                    ),
                    route_trace=logical.execution.get("route_trace"),
                    task_type=(logical.task_state or {}).get("task_type"),
                    release_decision=logical.release_decision,
                    field_resolution_statuses={
                        key: str(value.get("status") or "")
                        for key, value in (logical.execution.get("field_resolutions") or {}).items()
                        if isinstance(value, dict)
                    },
                    contradiction_count=len(logical.execution.get("contradictions") or []),
                    claim_count=len(logical.claim_ledger),
                    recovery_attempted=bool(logical.execution.get("targeted_recovery")),
                )
                _record_test_case_finish(
                    question=question,
                    use_web_search=bool(use_web_search),
                    answer=logical.answer,
                    answer_type=logical.structured.get("answer_type"),
                    model=logical.model,
                    num_results=sources_found,
                    retrieval_mode=safe_meta.get("retrieval_mode"),
                    retrieval_channels=safe_meta.get("retrieval_channels"),
                    used_companion_sources=safe_meta.get("used_companion_sources"),
                    checked_source_categories=safe_meta.get("checked_source_categories"),
                    freshness_status=safe_meta.get("freshness_status"),
                    web_search_executed=safe_meta.get("web_search_executed"),
                    sources=logical.chunks,
                    citations=logical.citations,
                    total_ms=logical.total_ms,
                    synthesize=False,
                )
                yield send_event("done", {
                    "query_id": query_id,
                    "num_results": sources_found,
                    "retrieval_ms": logical.retrieval_ms,
                    "generation_ms": logical.generation_ms,
                    "total_ms": logical.total_ms,
                    "mode": "rccs_hybrid",
                    "retrieval_mode": safe_meta.get("retrieval_mode"),
                    "checked_source_categories": safe_meta.get("checked_source_categories"),
                    "used_companion_sources": safe_meta.get("used_companion_sources"),
                    "freshness_status": safe_meta.get("freshness_status"),
                    "requested_mode": safe_meta.get("requested_mode"),
                    "effective_mode": safe_meta.get("effective_mode"),
                    "retrieval_channels": safe_meta.get("retrieval_channels"),
                    "web_search_executed": safe_meta.get("web_search_executed"),
                    "web_search_status": safe_meta.get("web_search_status"),
                    "matched_source_ids": safe_meta.get("matched_source_ids"),
                    "source_count": sources_found,
                    "actions": logical.actions or None,
                    "task_state": logical.task_state,
                    "execution": logical.execution,
                    "release_decision": logical.release_decision,
                    "claim_ledger": logical.claim_ledger,
                    **logical.structured,
                })
                return
            from app.services.conversation_context import normalize_source_scope

            trail_scope = normalize_source_scope(
                source_scope, use_web_search=use_web_search
            )
            scope_start_message = {
                "knowledge": "Searching McNeese sources only",
                "adaptive": "Choosing the most direct source path",
                "web": "Searching official McNeese sources and the live web",
            }.get(trail_scope, "Searching trusted McNeese sources")

            yield send_event(
                "step",
                {
                    "step": "search",
                    "status": "started",
                    "message": scope_start_message,
                },
            )

            yield send_event(

                "activity",

                activity_payload(
                    query_id,
                    RETRIEVAL_STARTED,
                    start_time,
                    message=scope_start_message,
                    metadata={
                        "mode": trail_scope,
                        "source_scope": trail_scope,
                    },
                ),

            )

            retrieval_start = time.perf_counter()

            # Forward mid-retrieval activity for both supervisor and hybrid paths
            # so the live trail reflects realtime channel work (not a frozen script).
            activity_q: asyncio.Queue = asyncio.Queue()

            def _on_retrieval_activity(event: str, metadata=None, message=None):

                activity_q.put_nowait((event, metadata, message))

            retrieval_task = asyncio.create_task(

                run_rccs_retrieval(

                    question,

                    use_web_search=use_web_search,

                    source_scope=source_scope,

                    history=history,
                    request_context=request_context,

                    on_activity=_on_retrieval_activity,

                )

            )

            while not retrieval_task.done():

                try:

                    ev_name, ev_meta, ev_msg = await asyncio.wait_for(activity_q.get(), timeout=0.15)

                    yield send_event(

                        "activity",

                        activity_payload(query_id, ev_name, start_time, message=ev_msg, metadata=ev_meta),

                    )

                except asyncio.TimeoutError:

                    continue

            while not activity_q.empty():

                ev_name, ev_meta, ev_msg = activity_q.get_nowait()

                yield send_event(

                    "activity",

                    activity_payload(query_id, ev_name, start_time, message=ev_msg, metadata=ev_meta),

                )

            rccs_result = await retrieval_task

            parts = result_to_pipeline_parts(rccs_result)
            planner_actions = _planner_actions(question, parts, history)
            route_trace = (parts.get("metadata") or {}).get("route_trace")

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = parts["sources_found"]

            citations = parts["citations"]

            preview = source_preview_from_citations(citations)

            result_meta = parts.get("metadata") or {}
            conversation_ctx = result_meta.get("conversation_context") or {}
            resolved_for_answer = (
                conversation_ctx.get("resolved_question")
                or question
            )
            completed_meta = {
                "sources_found": sources_found,
                "duration_ms": retrieval_ms,
                "mode": trail_scope,
                "source_scope": trail_scope,
                "followup": bool(conversation_ctx.get("followup")),
            }
            primary_intent = getattr(
                getattr(rccs_result, "classification", None),
                "primary_intent",
                None,
            )
            if primary_intent:
                completed_meta["primary_intent"] = primary_intent
            if preview:
                completed_meta["source_preview"] = preview

            # Only re-emit citations that were not already shown as live reads.
            for src_ev in source_activities_from_citations(
                query_id,
                start_time,
                citations,
                operation_id=f"cite-{trail_scope}",
                source_type="official",
                sources_found=sources_found,
                run_id=client_run_id,
            ):
                yield send_event("activity", src_ev)

            yield send_event("step", {

                "step": "search",

                "status": "completed",

                "message": f"Found {sources_found} approved sources",

                "duration_ms": retrieval_ms

            })

            yield send_event(

                "activity",

                activity_payload(

                    query_id,

                    RETRIEVAL_COMPLETED,

                    start_time,

                    metadata=completed_meta,

                ),

            )

            yield send_event(

                "activity",

                activity_payload(query_id, CITATIONS_VALIDATING, start_time, metadata={"sources_found": sources_found}),

            )

            full_answer = ""

            generation_ms = None

            model_used = None

            _safe_response_meta = (parts.get("metadata") or {}).get("safe_response") or {}
            _evidence_sufficiency = _safe_response_meta.get("evidence_sufficiency") or {}
            _evidence_releaseable = bool(
                _evidence_sufficiency.get("passed", True)
                or _evidence_sufficiency.get("partial_allowed", False)
            )

            if parts["chunk_dicts"] and _evidence_releaseable:

                yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer from sources..."})

                yield send_event(

                    "activity",

                    activity_payload(query_id, ANSWER_GENERATING, start_time, metadata={"sources_found": sources_found}),

                )

                generation_start = time.perf_counter()

                try:

                    async for text_chunk in generate_answer_stream(
                        resolved_for_answer,
                        parts["chunk_dicts"],
                        persona,
                        (parts.get("metadata") or {}).get("safe_response"),
                        history,
                    ):

                        full_answer += text_chunk

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    model_used = CLAUDE_MODEL

                except Exception as e:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    print(f"LLM stream failed (RCCS): {type(e).__name__}: {e}")
                    traceback.print_exc()

                    full_answer = (

                        render_grounded_fallback(
                            resolved_for_answer, parts["chunk_dicts"],
                            (parts.get("metadata") or {}).get("safe_response"),
                        )

                    )

                    model_used = "fallback-no-llm"

            else:

                full_answer = (
                    _safe_response_meta.get("precise_failure")
                    or "I could not verify enough approved McNeese evidence to answer reliably."
                )

                model_used = "no_source"

            citation_validation = validate_answer_citations(full_answer, rccs_result)
            citations = citation_validation.get("citations") or []
            if not _evidence_releaseable:
                citations = []
            if not citation_validation.get("ok"):
                citations = []
                full_answer = (
                    (((parts.get("metadata") or {}).get("safe_response") or {}).get("precise_failure"))
                    or "I could not verify enough claim-relevant McNeese evidence to release this answer reliably."
                )
                model_used = "citation-gated"
            yield send_event("chunk", {"text": full_answer})
            yield send_event("citations", {"citations": citations})

            structured = structure_answer(

                question=question,

                answer=full_answer,

                num_results=sources_found,

                model=model_used,

            )

            safe_meta = _safe_response_meta

            total_ms = int((time.perf_counter() - start_time) * 1000)

            yield send_event(

                "activity",

                activity_payload(query_id, ANSWER_COMPLETED, start_time, metadata={"sources_found": sources_found}),

            )

            _record_test_case_finish(
                question=question,
                use_web_search=bool(use_web_search),
                answer=full_answer,
                answer_type=structured.get("answer_type"),
                model=model_used,
                num_results=sources_found,
                retrieval_mode=safe_meta.get("retrieval_mode"),
                retrieval_channels=safe_meta.get("retrieval_channels"),
                used_companion_sources=safe_meta.get("used_companion_sources"),
                checked_source_categories=safe_meta.get("checked_source_categories"),
                freshness_status=safe_meta.get("freshness_status"),
                web_search_executed=safe_meta.get("web_search_executed"),
                sources=parts.get("chunk_responses") or [],
                citations=citations if isinstance(citations, list) else [],
                total_ms=total_ms,
                synthesize=False,
                social_hint=bool(safe_meta.get("used_companion_sources"))
                or "social" in (safe_meta.get("checked_source_categories") or []),
            )

            yield send_event("done", {

                "query_id": query_id,

                "num_results": sources_found,

                "retrieval_ms": retrieval_ms,

                "generation_ms": generation_ms,

                "total_ms": total_ms,

                "mode": "rccs_hybrid",

                "retrieval_mode": safe_meta.get("retrieval_mode"),

                "checked_source_categories": safe_meta.get("checked_source_categories"),

                "used_companion_sources": safe_meta.get("used_companion_sources"),

                "freshness_status": safe_meta.get("freshness_status"),

                "requested_mode": safe_meta.get("requested_mode"),

                "effective_mode": safe_meta.get("effective_mode"),

                "retrieval_channels": safe_meta.get("retrieval_channels"),

                "web_search_executed": safe_meta.get("web_search_executed"),

                "web_search_status": safe_meta.get("web_search_status"),

                "matched_source_ids": safe_meta.get("matched_source_ids"),

                "source_count": safe_meta.get("source_count"),

                "actions": planner_actions or None,

                **structured,

            })

            return

        if use_web_search:

            # LIVE WEB SEARCH MODE

            yield send_event("step", {"step": "search", "status": "started", "message": "Searching mcneese.edu..."})

            yield send_event(

                "activity",

                activity_payload(query_id, RETRIEVAL_STARTED, start_time, metadata={"mode": "web_search"}),

            )

            

            retrieval_start = time.perf_counter()

            fetched_pages = await search_and_fetch(question, max_pages=5)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(fetched_pages)

            

            # Send citations with real URLs

            citations = [

                {"id": f"src-{i}", "title": p.title, "url": p.url, "snippet": p.content[:200]}

                for i, p in enumerate(fetched_pages, 1)

            ]

            preview = source_preview_from_citations(citations)

            completed_meta = {
                "sources_found": sources_found,
                "duration_ms": retrieval_ms,
                "mode": "web_search",
            }
            if preview:
                completed_meta["source_preview"] = preview

            for src_ev in source_activities_from_citations(
                query_id,
                start_time,
                citations,
                operation_id="live-web",
                source_type="web",
                sources_found=sources_found,
                run_id=client_run_id,
            ):
                yield send_event("activity", src_ev)

            yield send_event("step", {

                "step": "search", 

                "status": "completed", 

                "message": f"Found and read {sources_found} pages",

                "duration_ms": retrieval_ms

            })

            yield send_event(

                "activity",

                activity_payload(

                    query_id,

                    RETRIEVAL_COMPLETED,

                    start_time,

                    metadata=completed_meta,

                ),

            )

            yield send_event(

                "activity",

                activity_payload(query_id, CITATIONS_VALIDATING, start_time, metadata={"sources_found": sources_found}),

            )

            yield send_event("citations", {"citations": citations})

            

            if fetched_pages:

                yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer from sources..."})

                yield send_event(

                    "activity",

                    activity_payload(query_id, ANSWER_GENERATING, start_time, metadata={"sources_found": sources_found}),

                )

                

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": page.content, "title": page.title, "source_url": page.url}

                    for page in fetched_pages

                ]

                

                try:

                    async for text_chunk in generate_answer_stream(question, chunk_dicts, persona=persona):

                        full_answer += text_chunk

                        yield send_event("chunk", {"text": text_chunk})

                    

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    

                    yield send_event("step", {

                        "step": "generation", 

                        "status": "completed", 

                        "message": "Answer generated",

                        "duration_ms": generation_ms

                    })

                except Exception:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    fallback_answer = _format_web_results(fetched_pages, question)

                    # Replace (do not append) so partial LLM output is not doubled.
                    full_answer = fallback_answer

                    yield send_event("chunk", {"text": full_answer})

                    yield send_event("step", {

                        "step": "generation", 

                        "status": "completed", 

                        "message": "Formatted from sources (LLM unavailable)",

                        "duration_ms": generation_ms

                    })

            else:

                full_answer = "I couldn't find relevant information about that on the McNeese website. Please try rephrasing your question or ask about specific topics."

                yield send_event("chunk", {

                    "text": full_answer

                })

        else:

            # KNOWLEDGE BASE MODE

            yield send_event("step", {"step": "retrieval", "status": "started", "message": "Searching knowledge base..."})

            yield send_event(

                "activity",

                activity_payload(query_id, RETRIEVAL_STARTED, start_time, metadata={"mode": "knowledge_base"}),

            )

            

            retrieval_start = time.perf_counter()

            chunks = search_chunks(question)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(chunks)

            citations = [

                {"id": c.chunk_id, "title": c.title, "url": c.source_url, "snippet": c.text[:200]}

                for c in chunks

            ]

            preview = source_preview_from_citations(citations)

            completed_meta = {
                "sources_found": sources_found,
                "duration_ms": retrieval_ms,
                "mode": "knowledge_base",
            }
            if preview:
                completed_meta["source_preview"] = preview

            for src_ev in source_activities_from_citations(
                query_id,
                start_time,
                citations,
                operation_id="kb-retrieve",
                source_type="knowledge",
                sources_found=sources_found,
                run_id=client_run_id,
            ):
                yield send_event("activity", src_ev)

            yield send_event("step", {

                "step": "retrieval", 

                "status": "completed", 

                "message": f"Found {sources_found} relevant sources",

                "duration_ms": retrieval_ms

            })

            yield send_event(

                "activity",

                activity_payload(

                    query_id,

                    RETRIEVAL_COMPLETED,

                    start_time,

                    metadata=completed_meta,

                ),

            )

            yield send_event(

                "activity",

                activity_payload(query_id, CITATIONS_VALIDATING, start_time, metadata={"sources_found": sources_found}),

            )

            yield send_event("citations", {"citations": citations})

            

            if chunks:

                yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer..."})

                yield send_event(

                    "activity",

                    activity_payload(query_id, ANSWER_GENERATING, start_time, metadata={"sources_found": sources_found}),

                )

                

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": c.text, "title": c.title, "source_url": c.source_url}

                    for c in chunks

                ]

                

                try:

                    async for text_chunk in generate_answer_stream(question, chunk_dicts, persona=persona):

                        full_answer += text_chunk

                        yield send_event("chunk", {"text": text_chunk})

                    

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    

                    yield send_event("step", {

                        "step": "generation", 

                        "status": "completed", 

                        "message": "Answer generated",

                        "duration_ms": generation_ms

                    })

                except Exception:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    fallback_answer = format_chunks_as_answer(chunks, question)

                    # Replace (do not append) so partial LLM output is not doubled.
                    full_answer = fallback_answer

                    yield send_event("chunk", {"text": full_answer})

                    yield send_event("step", {

                        "step": "generation", 

                        "status": "completed", 

                        "message": "Formatted from sources (LLM unavailable)",

                        "duration_ms": generation_ms

                    })

            else:

                full_answer = "I couldn't find relevant information in the knowledge base. Try enabling web search for broader coverage."

                yield send_event("chunk", {

                    "text": full_answer

                })

        

        total_ms = int((time.perf_counter() - start_time) * 1000)

        

        debug_kwargs: dict = {}

        if debug_trace_enabled():

            debug_kwargs = {

                "intent": intent_result.intent.value,

                "persona": persona,

                "expanded_queries": expand_query(question),

                "mode": "web_search" if use_web_search else "knowledge_base",

            }

        log_full_query(

            query_id=query_id,

            question=question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            answer_model=CLAUDE_MODEL if sources_found else None,

            final_status="success" if sources_found else "no_results",
            route_trace=route_trace,

            **debug_kwargs,

        )

        mode = "web_search" if use_web_search else "knowledge_base"

        structured = structure_answer(

            question=question,

            answer=full_answer,

            num_results=sources_found,

            model=CLAUDE_MODEL if sources_found else None,

        )

        yield send_event(

            "activity",

            activity_payload(query_id, ANSWER_COMPLETED, start_time, metadata={"num_results": sources_found, "mode": mode}),

        )

        

        yield send_event("done", {

            "query_id": query_id,

            "num_results": sources_found,

            "retrieval_ms": retrieval_ms,

            "generation_ms": generation_ms,

            "total_ms": total_ms,

            "mode": mode,

            **structured,

        })

        

    except Exception as e:

        safe_error = SAFE_MESSAGES[REQUEST_FAILED]

        yield send_event(

            "activity",

            activity_payload(query_id, REQUEST_FAILED, start_time, message=safe_error, metadata={"status": "error"}),

        )

        yield send_event("error", {"message": safe_error})

        log_full_query(

            query_id=query_id,

            question=question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            final_status="error",

            error_step="stream",

            error_message=str(e),

        )





@router.get("/stats")

async def ask_stats() -> dict:

    """Get statistics about the knowledge base, web search, and pipeline."""

    kb_stats = {
        key: value
        for key, value in get_collection_stats().items()
        if key != "path"
    }

    pipeline_stats = get_pipeline_stats()

    llm_status = check_api_key()
    runtime_capabilities = retrieval_capabilities()

    

    return {

        "knowledge_base": kb_stats,

        "pipeline": pipeline_stats,

        "llm": llm_status,

        "web_search": {

            "enabled": True,

            "domains": [
                "mcneese.edu",
                "catalog.mcneese.edu",
                "mcneesesports.com",
                "mcneesecowboystore.com",
                "mcneesereslife.com",
            ],

            "description": "Live search across McNeese websites",

        },

        "rccs": rccs_flags_snapshot(),

        "supervisor": supervisor_flags_snapshot(),

        "capabilities": runtime_capabilities,
        "campus_intelligence": capability_snapshot(runtime=runtime_capabilities),
        "source_coverage": get_index_manifest_summary(),

        "modes": {

            "web_search": "Optional: search and read mcneese.edu pages when use_web_search=true",

            "knowledge_base": "Default: use pre-indexed content from the source registry",

            "rccs": "Optional hybrid retrieval when RCCS_ENABLED=1 (KB + official live + registry companions)",

        }

    }






