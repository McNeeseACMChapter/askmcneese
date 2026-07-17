"""Sanitized live-activity events for AskMcNeese SSE streams.

Emits user-facing pipeline progress without secrets, stack traces, prompts,
file paths, or database internals.
"""

from __future__ import annotations

import time
from typing import Any


# Canonical event names (frontend ActivityTimeline)
REQUEST_ACCEPTED = "request.accepted"
QUERY_ANALYZING = "query.analyzing"
QUERY_REWRITTEN = "query.rewritten"
RETRIEVAL_STARTED = "retrieval.started"
RETRIEVAL_SOURCE_FOUND = "retrieval.source_found"
RETRIEVAL_COMPLETED = "retrieval.completed"
RERANKING_STARTED = "reranking.started"
RERANKING_COMPLETED = "reranking.completed"
ANSWER_GENERATING = "answer.generating"
CITATIONS_VALIDATING = "citations.validating"
ANSWER_COMPLETED = "answer.completed"
REQUEST_FAILED = "request.failed"

# Layman-readable defaults (ask.py / supervisor may pass richer message= overrides).
SAFE_MESSAGES = {
    REQUEST_ACCEPTED: "Got your question — starting now",
    QUERY_ANALYZING: "Reading your question to decide what to search",
    QUERY_REWRITTEN: "Clarified the search terms for better results",
    RETRIEVAL_STARTED: "Searching McNeese-approved sources",
    RETRIEVAL_SOURCE_FOUND: "Found useful sources",
    RETRIEVAL_COMPLETED: "Finished collecting sources",
    RERANKING_STARTED: "Checking whether we have enough good sources",
    RERANKING_COMPLETED: "Sources look ready for an answer",
    ANSWER_GENERATING: "Writing your answer from those sources",
    CITATIONS_VALIDATING: "Double-checking the source links",
    ANSWER_COMPLETED: "Answer ready",
    REQUEST_FAILED: "Something went wrong — please try again",
}


def layman_message(event: str, *, sources_found: int | None = None, mode: str | None = None) -> str:
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
        if mode_key in {"web_search", "web", "adaptive", "supervisor_rccs", "rccs_hybrid"}:
            return "Searching McNeese-approved campus sources (including live pages when needed)"
        if mode_key in {"knowledge_base", "knowledge"}:
            return "Searching the McNeese knowledge base"
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
        "kb_retrieve": "Searching the McNeese knowledge base…",
        "official_web": "Searching approved McNeese websites…",
        "companion": "Checking approved companion sources (for example professor ratings)…",
        "agentic_web": "Searching live sources the question needs…",
        "page_open": "Opening selected pages to read full content…",
    }.get(skill_id, "Searching approved sources…")


def skill_result_message(skill_id: str, count: int, *, social: bool = False) -> str:
    """Plain-language line after a supervisor skill returns results."""
    n = max(0, int(count))
    unit = "result" if n == 1 else "results"
    if skill_id == "kb_retrieve":
        return f"Knowledge base returned {n} {unit}"
    if skill_id == "official_web":
        return f"Campus website search found {n} {unit}"
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
    """Build a short ·-joined title preview for live activity metadata."""
    if not citations:
        return None
    titles: list[str] = []
    for item in citations:
        title = ""
        if isinstance(item, dict):
            title = str(item.get("title") or "").strip()
        elif hasattr(item, "title"):
            title = str(getattr(item, "title") or "").strip()
        if not title or title in titles:
            continue
        titles.append(title[:60])
        if len(titles) >= limit:
            break
    return " · ".join(titles) if titles else None


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def safe_metadata(meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Allow only non-sensitive numeric/boolean/string metadata keys."""
    if not meta:
        return {}
    allowed = {
        "sources_found",
        "num_results",
        "mode",
        "duration_ms",
        "status",
        "channel",
        "provider",
        "skill",
        "source_preview",
    }
    out: dict[str, Any] = {}
    for key, value in meta.items():
        if key not in allowed:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            # Strip path-like strings
            if isinstance(value, str) and ("\\" in value or value.startswith("/")):
                continue
            out[key] = value
    return out


def activity_payload(
    request_id: str,
    event: str,
    start: float,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    meta = safe_metadata(metadata)
    sources = meta.get("sources_found")
    if not isinstance(sources, int):
        sources = meta.get("num_results") if isinstance(meta.get("num_results"), int) else None
    mode = meta.get("mode") if isinstance(meta.get("mode"), str) else None
    resolved = message or layman_message(event, sources_found=sources, mode=mode)
    payload: dict[str, Any] = {
        "request_id": request_id,
        "event": event,
        "message": resolved,
        "elapsed_ms": elapsed_ms(start),
        "metadata": meta,
    }
    if run_id:
        payload["run_id"] = run_id
    # Test-case trail: record the same dict the SSE client sees.
    try:
        from app.services.test_case_recorder import note_activity

        note_activity(payload)
    except Exception:
        pass
    return payload
