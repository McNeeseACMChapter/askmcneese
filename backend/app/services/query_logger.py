"""Query logging service (BE-07).

Appends each /ask request to a JSONL file for later analysis.
Tracks the full pipeline: retrieval â†’ generation â†’ complete.
"""

from __future__ import annotations

import json
import os
import uuid
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from app.services.safe_errors import redact_sensitive

if TYPE_CHECKING:
    from app.services.retrieval import RetrievedChunk

load_dotenv()

QUERY_LOG_PATH = os.getenv("QUERY_LOG_PATH", "backend/logs/query_logs.jsonl")
_log_lock = threading.Lock()


@dataclass
class PipelineStep:
    name: str
    status: str  # "started", "completed", "failed"
    timestamp: str
    duration_ms: int | None = None
    details: dict | None = None


@dataclass
class QueryLog:
    query_id: str
    timestamp: str
    question_text: str
    pipeline_steps: list[PipelineStep]
    retrieved_chunk_ids: list[str]
    top_source_urls: list[str]
    num_results: int
    answer_generated: bool
    answer_model: str | None
    answer_tokens: int | None
    total_latency_ms: int
    final_status: str  # "success", "partial", "no_results", "error"
    # Debug-trace fields (only written when ASKMCNEESE_DEBUG_TRACE=1). They stay
    # None in normal operation and are stripped from the JSON output entirely so
    # the default log stays minimal.
    intent: str | None = None
    persona: str | None = None
    expanded_queries: list[str] | None = None
    rerank_scores: list[float] | None = None
    mode: str | None = None
    route_trace: dict | None = None
    task_type: str | None = None
    release_decision: dict | None = None
    field_resolution_statuses: dict[str, str] | None = None
    contradiction_count: int | None = None
    claim_count: int | None = None
    recovery_attempted: bool | None = None


# Fields recorded only when the debug-trace flag is on.
_DEBUG_TRACE_FIELDS = ("intent", "persona", "expanded_queries", "rerank_scores", "mode")


def debug_trace_enabled() -> bool:
    """True when ASKMCNEESE_DEBUG_TRACE is set to "1"."""
    return os.getenv("ASKMCNEESE_DEBUG_TRACE", "0") == "1"


def _get_log_path() -> Path:
    return Path(__file__).resolve().parents[3] / QUERY_LOG_PATH


def create_query_id() -> str:
    """Generate a new query ID."""
    return str(uuid.uuid4())


def log_full_query(
    query_id: str,
    question: str,
    chunks: list["RetrievedChunk"],
    retrieval_ms: int,
    generation_ms: int | None = None,
    answer_model: str | None = None,
    answer_tokens: int | None = None,
    final_status: str = "success",
    error_step: str | None = None,
    error_message: str | None = None,
    intent: str | None = None,
    persona: str | None = None,
    expanded_queries: list[str] | None = None,
    rerank_scores: list[float] | None = None,
    mode: str | None = None,
    route_trace: dict | None = None,
    task_type: str | None = None,
    release_decision: dict | None = None,
    field_resolution_statuses: dict[str, str] | None = None,
    contradiction_count: int | None = None,
    claim_count: int | None = None,
    recovery_attempted: bool | None = None,
) -> None:
    """
    Log a complete query with full pipeline details.

    The ``intent`` / ``persona`` / ``expanded_queries`` / ``rerank_scores`` /
    ``mode`` arguments are debug-trace extras. They are only written to the log
    when ``ASKMCNEESE_DEBUG_TRACE=1``; otherwise the keys are omitted entirely so
    the default log format is unchanged.
    """
    log_path = _get_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    
    now = datetime.now(timezone.utc).isoformat()
    
    steps = [
        PipelineStep(
            name="retrieval",
            status="completed" if chunks else "no_results",
            timestamp=now,
            duration_ms=retrieval_ms,
            details={"chunks_found": len(chunks)}
        )
    ]
    
    if generation_ms is not None:
        steps.append(PipelineStep(
            name="generation",
            status="completed" if answer_model else "skipped",
            timestamp=now,
            duration_ms=generation_ms,
            details={"model": answer_model, "tokens": answer_tokens}
        ))
    
    if error_step:
        steps.append(PipelineStep(
            name=error_step,
            status="failed",
            timestamp=now,
            details={"error": redact_sensitive(error_message)}
        ))
    
    total_ms = retrieval_ms + (generation_ms or 0)

    debug_on = debug_trace_enabled()

    log_entry = QueryLog(
        query_id=query_id,
        timestamp=now,
        question_text=(
            question[:4000]
            if os.getenv("ASKMCNEESE_LOG_QUESTION_TEXT", "0") == "1"
            else f"[redacted; length={len(question or '')}]"
        ),
        pipeline_steps=[asdict(s) for s in steps],
        retrieved_chunk_ids=[c.chunk_id for c in chunks],
        top_source_urls=list(
            dict.fromkeys(redact_sensitive(c.source_url, max_length=1000) for c in chunks)
        ),
        num_results=len(chunks),
        answer_generated=answer_model is not None,
        answer_model=answer_model,
        answer_tokens=answer_tokens,
        total_latency_ms=total_ms,
        final_status=final_status,
        intent=intent if debug_on else None,
        persona=persona if debug_on else None,
        expanded_queries=expanded_queries if debug_on else None,
        rerank_scores=rerank_scores if debug_on else None,
        mode=mode if debug_on else None,
        route_trace=route_trace,
        task_type=task_type,
        release_decision=release_decision,
        field_resolution_statuses=field_resolution_statuses,
        contradiction_count=contradiction_count,
        claim_count=claim_count,
        recovery_attempted=recovery_attempted,
    )

    entry_dict = asdict(log_entry)
    if not debug_on:
        for field in _DEBUG_TRACE_FIELDS:
            entry_dict.pop(field, None)

    try:
        with _log_lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry_dict) + "\n")
    except OSError:
        # Observability is best-effort; it must not take down /ask.
        return

def get_recent_queries(limit: int = 10) -> list[dict]:
    """Get the most recent queries from the log."""
    log_path = _get_log_path()
    
    if not log_path.exists():
        return []
    
    parsed: list[dict] = []
    try:
        with _log_lock:
            with open(log_path, "rb") as f:
                f.seek(0, 2)
                position = f.tell()
                data = b""
                # Statistics never need to scan an unbounded analytics file.
                while position > 0 and data.count(b"\n") <= limit and len(data) < 1024 * 1024:
                    take = min(64 * 1024, position)
                    position -= take
                    f.seek(position)
                    data = f.read(take) + data
        for raw in data.splitlines()[-max(1, limit):]:
            try:
                item = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(item, dict):
                parsed.append(item)
    except OSError:
        return []

    return list(reversed(parsed))


def get_pipeline_stats() -> dict:
    """Get aggregate statistics about the pipeline."""
    queries = get_recent_queries(100)
    
    if not queries:
        return {"total_queries": 0}
    
    total = len(queries)
    successful = sum(1 for q in queries if q.get("final_status") == "success")
    with_generation = sum(1 for q in queries if q.get("answer_generated"))
    avg_latency = sum(q.get("total_latency_ms", 0) for q in queries) / total
    
    return {
        "total_queries": total,
        "successful": successful,
        "success_rate": round(successful / total * 100, 1),
        "with_llm_generation": with_generation,
        "avg_latency_ms": round(avg_latency),
    }

