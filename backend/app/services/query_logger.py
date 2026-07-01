"""Query logging service (BE-07).

Appends each /ask request to a JSONL file for later analysis.
Tracks the full pipeline: retrieval → generation → complete.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from app.services.retrieval import RetrievedChunk

load_dotenv()

QUERY_LOG_PATH = os.getenv("QUERY_LOG_PATH", "backend/logs/query_logs.jsonl")


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
) -> None:
    """
    Log a complete query with full pipeline details.
    """
    log_path = _get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
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
            details={"error": error_message}
        ))
    
    total_ms = retrieval_ms + (generation_ms or 0)
    
    log_entry = QueryLog(
        query_id=query_id,
        timestamp=now,
        question_text=question,
        pipeline_steps=[asdict(s) for s in steps],
        retrieved_chunk_ids=[c.chunk_id for c in chunks],
        top_source_urls=list(dict.fromkeys(c.source_url for c in chunks)),
        num_results=len(chunks),
        answer_generated=answer_model is not None,
        answer_model=answer_model,
        answer_tokens=answer_tokens,
        total_latency_ms=total_ms,
        final_status=final_status,
    )
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(log_entry)) + "\n")


def log_query(
    question: str,
    chunks: list["RetrievedChunk"],
    latency_ms: int,
    status: str = "success",
) -> str:
    """
    Legacy log function for backward compatibility.
    """
    query_id = create_query_id()
    log_full_query(
        query_id=query_id,
        question=question,
        chunks=chunks,
        retrieval_ms=latency_ms,
        final_status=status,
    )
    return query_id


def get_recent_queries(limit: int = 10) -> list[dict]:
    """Get the most recent queries from the log."""
    log_path = _get_log_path()
    
    if not log_path.exists():
        return []
    
    queries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
    
    return queries[-limit:][::-1]


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
