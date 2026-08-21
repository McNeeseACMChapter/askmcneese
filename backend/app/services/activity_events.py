"""Trust-calibrated live activity events for AskMcNeese SSE streams.

This module exposes real system work without mirroring raw terminal output.
Only canonical event names and allowlisted, user-safe facts leave the backend.
Prompts, commands, stack traces, paths, credentials, database statements, and
internal model reasoning must never be placed in an activity payload.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Literal
from urllib.parse import urlparse

LivePhase = Literal["understand", "search", "verify", "compose"]
LiveKind = Literal["milestone", "operation", "evidence"]
LiveVisibility = Literal["headline", "detail", "debug"]

SCHEMA_VERSION = 2

REQUEST_ACCEPTED = "request.accepted"
QUERY_ANALYZING = "query.analyzing"
QUERY_CLASSIFIED = "query.classified"
QUERY_REWRITTEN = "query.rewritten"
PLAN_CREATED = "plan.created"
RETRIEVAL_STARTED = "retrieval.started"
RETRIEVAL_SOURCE_FOUND = "retrieval.source_found"
PAGE_OPENED = "page.opened"
RETRIEVAL_COMPLETED = "retrieval.completed"
RERANKING_STARTED = "reranking.started"
RERANKING_COMPLETED = "reranking.completed"
ANSWER_OUTLINING = "answer.outlining"
ANSWER_GENERATING = "answer.generating"
CITATIONS_VALIDATING = "citations.validating"
ANSWER_COMPLETED = "answer.completed"
REQUEST_FAILED = "request.failed"
REQUEST_CANCELLED = "request.cancelled"

PHASE_BY_EVENT: dict[str, LivePhase] = {
    REQUEST_ACCEPTED: "understand",
    QUERY_ANALYZING: "understand",
    QUERY_CLASSIFIED: "understand",
    QUERY_REWRITTEN: "understand",
    PLAN_CREATED: "understand",
    RETRIEVAL_STARTED: "search",
    RETRIEVAL_SOURCE_FOUND: "search",
    PAGE_OPENED: "search",
    RETRIEVAL_COMPLETED: "search",
    RERANKING_STARTED: "verify",
    RERANKING_COMPLETED: "verify",
    CITATIONS_VALIDATING: "verify",
    ANSWER_OUTLINING: "compose",
    ANSWER_GENERATING: "compose",
    ANSWER_COMPLETED: "compose",
    REQUEST_FAILED: "compose",
    REQUEST_CANCELLED: "compose",
}

SAFE_MESSAGES = {
    REQUEST_ACCEPTED: "Starting your request",
    QUERY_ANALYZING: "Understanding what you need",
    QUERY_CLASSIFIED: "Choosing the right search path",
    QUERY_REWRITTEN: "Refining the search terms",
    PLAN_CREATED: "Planning the search",
    RETRIEVAL_STARTED: "Searching trusted McNeese sources",
    RETRIEVAL_SOURCE_FOUND: "Reading a relevant source",
    PAGE_OPENED: "Reading a selected page",
    RETRIEVAL_COMPLETED: "Collected the relevant sources",
    RERANKING_STARTED: "Ranking evidence by relevance",
    RERANKING_COMPLETED: "Selected the strongest evidence",
    ANSWER_OUTLINING: "Organizing the answer",
    ANSWER_GENERATING: "Writing your answer",
    CITATIONS_VALIDATING: "Checking every citation",
    ANSWER_COMPLETED: "Answer ready",
    REQUEST_FAILED: "The request could not finish",
    REQUEST_CANCELLED: "The request was stopped",
}

_ALLOWED_METADATA = {
    "schema_version",
    "event_id",
    "phase",
    "kind",
    "visibility",
    "operation_id",
    "operation_label",
    "sources_found",
    "sources_read",
    "num_results",
    "result_count",
    "selected_count",
    "citation_count",
    "citations_used",
    "mode",
    "duration_ms",
    "status",
    "channel",
    "provider",
    "skill",
    "source_type",
    "source_title",
    "source_host",
    "source_url",
    "source_status",
    "source_scope",
    "primary_intent",
    "followup",
    "planned_query_count",
    "category",
    # Temporary compatibility only. Prefer one source_title per event.
    "source_preview",
}

_SENSITIVE = re.compile(
    r"(?:bearer\s+[a-z0-9._-]+|api[_ -]?key|access[_ -]?token|secret|password|"
    r"\.env|traceback|stack trace|[a-z]:\\|/(?:users|home|var|etc|private|tmp)/)",
    re.IGNORECASE,
)


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _clean_text(value: Any, *, limit: int = 160) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split()).strip()
    if not cleaned or _SENSITIVE.search(cleaned):
        return None
    return cleaned[:limit]


def _phase_for_event(event: str) -> LivePhase:
    explicit = PHASE_BY_EVENT.get(event)
    if explicit:
        return explicit
    if event.startswith(("request.", "query.", "plan.", "intent.")):
        return "understand"
    if event.startswith(("retrieval.", "search.", "source.", "page.", "tool.", "skill.")):
        return "search"
    if event.startswith(("reranking.", "evidence.", "citation.", "citations.", "validation.")):
        return "verify"
    return "compose"


def _kind_for_event(event: str, metadata: dict[str, Any]) -> LiveKind:
    explicit = metadata.get("kind")
    if explicit in {"milestone", "operation", "evidence"}:
        return explicit
    if (
        "source_found" in event
        or "source.found" in event
        or event.startswith("page.")
        or metadata.get("source_title")
    ):
        return "evidence"
    if metadata.get("operation_id") or metadata.get("skill") or metadata.get("channel"):
        return "operation"
    return "milestone"


def _clean_public_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password:
        return None
    hostname = (parsed.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local"):
        return None
    return value.strip()[:500]


def safe_metadata(meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return only non-sensitive, bounded telemetry facts."""
    if not meta:
        return {}

    output: dict[str, Any] = {}
    for key, value in meta.items():
        if key not in _ALLOWED_METADATA:
            continue
        if isinstance(value, str):
            cleaned = _clean_public_url(value) if key == "source_url" else _clean_text(value)
            if cleaned:
                output[key] = cleaned
        elif isinstance(value, (int, float, bool)) or value is None:
            output[key] = value
    return output


def activity_payload(
    request_id: str,
    event: str,
    start: float,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
    run_id: str | None = None,
    *,
    phase: LivePhase | None = None,
    kind: LiveKind | None = None,
    visibility: LiveVisibility = "detail",
    operation_id: str | None = None,
) -> dict[str, Any]:
    """Build one canonical SSE activity payload."""
    meta = safe_metadata(metadata)
    resolved_phase = phase or _phase_for_event(event)
    resolved_kind = kind or _kind_for_event(event, meta)

    meta.update(
        {
            "schema_version": SCHEMA_VERSION,
            "event_id": meta.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}",
            "phase": resolved_phase,
            "kind": resolved_kind,
            "visibility": visibility,
        }
    )
    if operation_id:
        cleaned_operation = _clean_text(operation_id, limit=80)
        if cleaned_operation:
            meta["operation_id"] = cleaned_operation

    resolved_message = _clean_text(message, limit=180) or SAFE_MESSAGES.get(
        event, "Working on your answer"
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "event": event,
        "message": resolved_message,
        "elapsed_ms": elapsed_ms(start),
        "phase": resolved_phase,
        "kind": resolved_kind,
        "visibility": visibility,
        "metadata": meta,
    }
    if run_id:
        payload["run_id"] = run_id

    try:
        from app.services.test_case_recorder import note_activity

        note_activity(payload)
    except Exception:
        pass
    return payload


def operation_activity(
    request_id: str,
    event: str,
    start: float,
    *,
    operation_id: str,
    operation_label: str,
    skill: str | None = None,
    status: str | None = None,
    result_count: int | None = None,
    run_id: str | None = None,
    phase: LivePhase = "search",
) -> dict[str, Any]:
    """Describe a real backend operation without exposing its command or prompt."""
    metadata: dict[str, Any] = {
        "operation_label": operation_label,
        "skill": skill,
        "status": status,
        "result_count": result_count,
    }
    return activity_payload(
        request_id,
        event,
        start,
        metadata=metadata,
        run_id=run_id,
        phase=phase,
        kind="operation",
        operation_id=operation_id,
    )


def source_activity(
    request_id: str,
    start: float,
    *,
    source_title: str,
    source_host: str | None = None,
    source_url: str | None = None,
    source_type: str = "official",
    source_status: str = "read",
    operation_id: str | None = None,
    sources_found: int | None = None,
    sources_read: int | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Emit one source at a time so the UI can animate a truthful source reel."""
    return activity_payload(
        request_id,
        RETRIEVAL_SOURCE_FOUND,
        start,
        metadata={
            "source_title": source_title,
            "source_host": source_host,
            "source_url": source_url,
            "source_type": source_type,
            "source_status": source_status,
            "sources_found": sources_found,
            "sources_read": sources_read,
        },
        run_id=run_id,
        phase="search",
        kind="evidence",
        visibility="headline",
        operation_id=operation_id,
    )


def layman_message(
    event: str, *, sources_found: int | None = None, mode: str | None = None
) -> str:
    """Build a plain-language status line for a frozen activity event."""
    n = sources_found
    mode_key = (mode or "").strip().lower()

    if event == REQUEST_ACCEPTED:
        return "Got your question — starting now"
    if event == QUERY_ANALYZING:
        return "Reading your question to decide what to search"
    if event == QUERY_REWRITTEN:
        return "Clarified the search terms for better results"
    if event == RETRIEVAL_STARTED:
        if mode_key in {"knowledge_base", "knowledge"}:
            return "Searching McNeese sources only"
        if mode_key in {"web_search", "web"}:
            return "Searching official McNeese sources and the live web"
        if mode_key == "adaptive":
            return "Choosing the most direct source path"
        if mode_key in {"supervisor_rccs", "rccs_hybrid"}:
            return "Searching trusted McNeese sources"
        return "Searching McNeese-approved sources"
    if event == RETRIEVAL_SOURCE_FOUND:
        if isinstance(n, int) and n >= 0:
            return f"Found {n} useful source{'s' if n != 1 else ''} so far"
        return "Found useful sources"
    if event == RETRIEVAL_COMPLETED:
        if isinstance(n, int) and n >= 0:
            return f"Finished collecting sources ({n} total)"
        return "Finished collecting sources"
    if event == RERANKING_STARTED:
        return "Checking whether we have enough good sources"
    if event == RERANKING_COMPLETED:
        return "Sources look ready for an answer"
    if event == ANSWER_GENERATING:
        if isinstance(n, int) and n > 0:
            return f"Writing your answer from {n} source{'s' if n != 1 else ''}"
        return "Writing your answer from those sources"
    if event == CITATIONS_VALIDATING:
        return "Double-checking the source links"
    if event == ANSWER_COMPLETED:
        return "Answer ready"
    if event == REQUEST_FAILED:
        return "Something went wrong — please try again"
    return SAFE_MESSAGES.get(event, "Working on your answer…")


def skill_start_message(skill_id: str, *, social: bool = False) -> str:
    """Plain-language line when a supervisor skill begins."""
    if skill_id == "agentic_web" and social:
        return "Searching public profiles and related web sources…"
    return {
        "registry_specialist": "Resolving the requested campus source…",
        "structured_specialist": "Resolving the requested campus source…",
        "kb_retrieve": "Searching the McNeese knowledge base…",
        "official_web": "Checking official McNeese pages…",
        "companion": "Checking approved companion sources (for example professor ratings)…",
        "agentic_web": "Searching live sources the question needs…",
        "page_open": "Opening selected pages to read full content…",
    }.get(skill_id, "Searching approved sources…")


def skill_result_message(skill_id: str, count: int, *, social: bool = False) -> str:
    """Plain-language line after a supervisor skill returns results."""
    n = max(0, int(count))
    unit = "result" if n == 1 else "results"
    if skill_id in {"registry_specialist", "structured_specialist"}:
        return "Campus source route resolved"
    if skill_id == "kb_retrieve":
        return f"Knowledge base returned {n} {unit}"
    if skill_id == "official_web":
        return f"Official source check returned {n} {unit}"
    if skill_id == "companion":
        return f"Companion sources returned {n} {unit}"
    if skill_id == "agentic_web":
        if social:
            return f"Social / web search returned {n} {unit}"
        return f"Live search returned {n} {unit}"
    if skill_id == "page_open":
        return f"Opened and read {n} page{'s' if n != 1 else ''}"
    return f"Search returned {n} {unit}"


def source_preview_from_citations(citations: list[Any] | None, *, limit: int = 3) -> str | None:
    """Legacy joined preview. Prefer emitting source_activity per citation."""
    if not citations:
        return None
    titles: list[str] = []
    seen: set[str] = set()
    for citation in citations:
        title = None
        if isinstance(citation, dict):
            title = citation.get("title")
        else:
            title = getattr(citation, "title", None)
        cleaned = _clean_text(title, limit=80)
        if not cleaned or cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        titles.append(cleaned)
        if len(titles) >= limit:
            break
    if not titles:
        return None
    return " · ".join(titles)


def source_activities_from_citations(
    request_id: str,
    start: float,
    citations: list[Any] | None,
    *,
    operation_id: str | None = None,
    source_type: str = "official",
    sources_found: int | None = None,
    run_id: str | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    """Emit final cited sources as verify-phase evidence (not fake live reads)."""
    if not citations:
        return []
    events: list[dict[str, Any]] = []
    total = sources_found if isinstance(sources_found, int) else len(citations)
    for index, citation in enumerate(citations[:limit]):
        if isinstance(citation, dict):
            title = citation.get("title")
            url = citation.get("url")
        else:
            title = getattr(citation, "title", None)
            url = getattr(citation, "url", None)
        cleaned_title = _clean_text(title, limit=120)
        if not cleaned_title:
            continue
        host = None
        cleaned_url = _clean_public_url(url)
        if cleaned_url:
            try:
                host = urlparse(cleaned_url).hostname
            except ValueError:
                host = None
        payload = source_activity(
            request_id,
            start,
            source_title=cleaned_title,
            source_host=host,
            source_url=cleaned_url,
            source_type=source_type,
            source_status="cited",
            operation_id=operation_id,
            sources_found=total,
            sources_read=index + 1,
            run_id=run_id,
        )
        # Keep the reel, but do not pretend these were just opened mid-search.
        payload["message"] = f"Citing: {cleaned_title}"
        payload["phase"] = "verify"
        events.append(payload)
    return events
