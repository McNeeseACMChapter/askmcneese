"""Human-readable test-case trail recorder for AskMcNeese.

Appends each /ask run (activity events + backend retrieval data + match check)
to a plain text file under backend/test_case_runs/ — outside app code/logs.

Enable with TEST_CASE_RECORDING_ENABLED=1 (default on when unset in local .env).
"""

from __future__ import annotations

import os
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def recording_enabled() -> bool:
    return os.getenv("TEST_CASE_RECORDING_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _backend_root() -> Path:
    # .../backend/app/services/this.py → parents[2] = backend
    return Path(__file__).resolve().parents[2]


def trail_log_path() -> Path:
    override = (os.getenv("TEST_CASE_TRAIL_PATH") or "").strip()
    if override:
        p = Path(override)
        return p if p.is_absolute() else _backend_root() / p
    return _backend_root() / "test_case_runs" / "test_case_trail.txt"


def index_path() -> Path:
    return trail_log_path().with_name("test_case_index.txt")


_lock = threading.Lock()
_case_counter = 0


def _next_case_number() -> int:
    """Persist a running case number across process reloads via index file."""
    global _case_counter
    with _lock:
        path = index_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if _case_counter <= 0 and path.exists():
            try:
                raw = path.read_text(encoding="utf-8").strip()
                _case_counter = int(raw) if raw.isdigit() else 0
            except Exception:
                _case_counter = 0
        _case_counter += 1
        path.write_text(str(_case_counter), encoding="utf-8")
        return _case_counter


@dataclass
class ActivityLine:
    event: str
    message: str
    elapsed_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseRun:
    case_number: int
    query_id: str
    question: str
    use_web_search: bool
    started_at: str
    activity: list[ActivityLine] = field(default_factory=list)
    stream: bool = False


_current: ContextVar[TestCaseRun | None] = ContextVar("test_case_run", default=None)


def begin_run(
    *,
    query_id: str,
    question: str,
    use_web_search: bool = False,
    stream: bool = False,
) -> TestCaseRun | None:
    if not recording_enabled():
        return None
    run = TestCaseRun(
        case_number=_next_case_number(),
        query_id=query_id,
        question=question or "",
        use_web_search=bool(use_web_search),
        started_at=datetime.now(timezone.utc).isoformat(),
        stream=stream,
    )
    _current.set(run)
    return run


def note_activity(payload: dict[str, Any] | None) -> None:
    """Hook from activity_payload — records the exact SSE activity dict."""
    if not recording_enabled() or not payload:
        return
    run = _current.get()
    if run is None:
        return
    # Only record events for this run's request_id when present
    rid = str(payload.get("request_id") or "")
    if rid and rid != run.query_id:
        return
    meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    run.activity.append(
        ActivityLine(
            event=str(payload.get("event") or ""),
            message=str(payload.get("message") or ""),
            elapsed_ms=int(payload.get("elapsed_ms") or 0),
            metadata=dict(meta),
        )
    )


def _hosts_from_urls(urls: list[str]) -> set[str]:
    hosts: set[str] = set()
    for u in urls:
        try:
            h = (urlparse(u).hostname or "").lower().removeprefix("www.")
            if h:
                hosts.add(h)
        except Exception:
            continue
    return hosts


def _social_cue_in_messages(messages: list[str]) -> bool:
    blob = " ".join(messages).lower()
    return any(
        x in blob
        for x in (
            "social",
            "linkedin",
            "instagram",
            "facebook",
            "public profiles",
            "companion",
        )
    )


def _match_report(
    *,
    activity: list[ActivityLine],
    source_urls: list[str],
    citation_urls: list[str],
    used_companions: list[str],
    channels: list[str],
) -> tuple[str, list[str]]:
    """Return (verdict, notes) comparing live trail copy to backend data."""
    notes: list[str] = []
    messages = [a.message for a in activity]
    trail_social = _social_cue_in_messages(messages)
    data_urls = list(dict.fromkeys([*citation_urls, *source_urls]))
    hosts = _hosts_from_urls(data_urls)
    social_hosts = {
        "linkedin.com",
        "instagram.com",
        "facebook.com",
        "x.com",
        "twitter.com",
        "joinhandshake.com",
    }
    data_has_social = bool(hosts & social_hosts) or any(
        (c or "").upper().startswith("SRC-C-") and "RMP" not in (c or "").upper()
        for c in used_companions
    )
    companion_channel = "companion" in (channels or [])

    # Previews claimed in activity metadata
    previews = [
        str(a.metadata.get("source_preview") or "")
        for a in activity
        if a.metadata.get("source_preview")
    ]
    if previews and not data_urls:
        notes.append("Activity source_preview present but no source/citation URLs in backend data")

    if trail_social and not data_has_social and not companion_channel:
        notes.append(
            "Activity trail mentions social/companion search but backend data has no social URLs "
            "and companion channel was not activated"
        )
    if data_has_social and not trail_social:
        notes.append(
            "Backend data includes social URLs but activity trail never mentioned social/companion browse"
        )

    # Source counts
    completed = next((a for a in reversed(activity) if a.event == "retrieval.completed"), None)
    if completed is not None:
        claimed = completed.metadata.get("sources_found")
        if isinstance(claimed, int) and data_urls and claimed != len(source_urls):
            # citations may be subset of chunks — warn only on zero vs nonzero mismatch
            if claimed > 0 and len(source_urls) == 0:
                notes.append(
                    f"Activity claimed sources_found={claimed} but backend source list is empty"
                )

    if not notes:
        return "MATCH", ["Activity trail and backend source data are consistent enough for this run"]
    if any("but no" in n or "never mentioned" in n or "empty" in n for n in notes):
        return "MISMATCH", notes
    return "PARTIAL", notes


def finalize_run(
    *,
    answer: str = "",
    answer_type: str | None = None,
    model: str | None = None,
    num_results: int | None = None,
    retrieval_mode: str | None = None,
    retrieval_channels: list[str] | None = None,
    used_companion_sources: list[str] | None = None,
    checked_source_categories: list[str] | None = None,
    freshness_status: str | None = None,
    web_search_executed: bool | None = None,
    classification: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    flags: dict[str, Any] | None = None,
    sources: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
    error: str | None = None,
    total_ms: int | None = None,
) -> Path | None:
    """Write one test-case block and clear the active run."""
    run = _current.get()
    if run is None or not recording_enabled():
        return None

    sources = sources or []
    citations = citations or []
    source_urls = [
        str(s.get("url") or s.get("source_url") or "")
        for s in sources
        if (s.get("url") or s.get("source_url"))
    ]
    citation_urls = [str(c.get("url") or "") for c in citations if c.get("url")]
    channels = list(retrieval_channels or [])
    companions = list(used_companion_sources or [])

    verdict, match_notes = _match_report(
        activity=run.activity,
        source_urls=source_urls,
        citation_urls=citation_urls,
        used_companions=companions,
        channels=channels,
    )

    lines: list[str] = []
    lines.append("=" * 88)
    lines.append(
        f"TEST CASE #{run.case_number} | {run.started_at} | "
        f"{'stream' if run.stream else 'non-stream'}"
    )
    lines.append(f"query_id: {run.query_id}")
    lines.append(f"use_web_search: {run.use_web_search}")
    lines.append("question:")
    lines.append(f"  {run.question}")
    lines.append("")

    lines.append("--- FLAGS ---")
    if flags:
        for k in sorted(flags.keys()):
            lines.append(f"  {k}: {flags[k]}")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("--- CLASSIFICATION / PLAN ---")
    if classification:
        for k, v in classification.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (not captured)")
    if plan:
        lines.append("  plan:")
        for k, v in plan.items():
            lines.append(f"    {k}: {v}")
    lines.append("")

    lines.append("--- ACTIVITY TRAIL (SSE order) ---")
    if run.activity:
        for i, a in enumerate(run.activity, 1):
            meta_bits = []
            for key in ("sources_found", "num_results", "mode", "skill", "source_preview", "channel"):
                if key in a.metadata and a.metadata[key] is not None:
                    meta_bits.append(f"{key}={a.metadata[key]}")
            meta_s = f" {{{', '.join(meta_bits)}}}" if meta_bits else ""
            lines.append(f"  {i:02d}. [{a.elapsed_ms}ms] {a.event} | {a.message}{meta_s}")
    else:
        lines.append("  (no activity events recorded — non-stream path or recording started late)")
    lines.append("")

    lines.append("--- BACKEND DATA ---")
    lines.append(f"  retrieval_mode: {retrieval_mode}")
    lines.append(f"  retrieval_channels: {channels}")
    lines.append(f"  used_companion_sources: {companions}")
    lines.append(f"  checked_source_categories: {checked_source_categories}")
    lines.append(f"  freshness_status: {freshness_status}")
    lines.append(f"  web_search_executed: {web_search_executed}")
    lines.append(f"  num_results: {num_results}")
    lines.append(f"  model: {model}")
    lines.append(f"  answer_type: {answer_type}")
    lines.append(f"  total_ms: {total_ms}")
    lines.append(f"  sources ({len(sources)}):")
    if sources:
        for s in sources:
            url = s.get("url") or s.get("source_url") or ""
            title = s.get("title") or ""
            ch = s.get("retrieval_channel") or s.get("category") or ""
            tier = s.get("source_tier") or ""
            trust = s.get("trust_level") or ""
            lines.append(f"    - [{ch}|tier={tier}|trust={trust}] {title} | {url}")
    else:
        lines.append("    (none)")
    lines.append(f"  citations ({len(citations)}):")
    if citations:
        for c in citations:
            lines.append(
                f"    - [{c.get('retrieval_channel')}|tier={c.get('source_tier')}|"
                f"trust={c.get('trust_level')}] {c.get('title')} | {c.get('url')}"
            )
    else:
        lines.append("    (none)")
    lines.append("")

    lines.append("--- TRAIL vs DATA MATCH ---")
    lines.append(f"  verdict: {verdict}")
    for n in match_notes:
        lines.append(f"  - {n}")
    lines.append("")

    lines.append("--- ANSWER ---")
    if error:
        lines.append(f"  ERROR: {error}")
    ans = (answer or "").strip()
    if ans:
        # Keep full answer for test review (trim extreme length)
        if len(ans) > 6000:
            ans = ans[:6000] + "\n  …[truncated]"
        for row in ans.splitlines() or [ans]:
            lines.append(f"  {row}")
    else:
        lines.append("  (empty)")
    lines.append("")
    lines.append("=" * 88)
    lines.append("")

    path = trail_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

    _current.set(None)
    return path


def synthesize_activity_from_meta(
    *,
    query_id: str,
    mode: str,
    sources_found: int,
    social: bool = False,
) -> None:
    """For non-stream asks: write a minimal expected trail so the log still has stages."""
    if not recording_enabled():
        return
    run = _current.get()
    if run is None:
        return
    # Only synthesize if nothing was recorded (non-stream has no SSE)
    if run.activity:
        return
    from app.services.activity_events import (
        ANSWER_COMPLETED,
        ANSWER_GENERATING,
        CITATIONS_VALIDATING,
        QUERY_ANALYZING,
        REQUEST_ACCEPTED,
        RETRIEVAL_COMPLETED,
        RETRIEVAL_SOURCE_FOUND,
        RETRIEVAL_STARTED,
        layman_message,
        skill_result_message,
        skill_start_message,
    )

    seq: list[tuple[str, str, dict[str, Any]]] = [
        (REQUEST_ACCEPTED, layman_message(REQUEST_ACCEPTED), {}),
        (QUERY_ANALYZING, layman_message(QUERY_ANALYZING), {}),
        (
            RETRIEVAL_STARTED,
            layman_message(RETRIEVAL_STARTED, mode=mode),
            {"mode": mode},
        ),
    ]
    if social:
        seq.append(
            (
                RETRIEVAL_SOURCE_FOUND,
                skill_start_message("agentic_web", social=True),
                {"skill": "agentic_web"},
            )
        )
        seq.append(
            (
                RETRIEVAL_SOURCE_FOUND,
                skill_result_message("agentic_web", sources_found, social=True),
                {"sources_found": sources_found, "skill": "agentic_web"},
            )
        )
    seq.extend(
        [
            (
                RETRIEVAL_COMPLETED,
                layman_message(RETRIEVAL_COMPLETED, sources_found=sources_found),
                {"sources_found": sources_found, "mode": mode},
            ),
            (
                CITATIONS_VALIDATING,
                layman_message(CITATIONS_VALIDATING),
                {"sources_found": sources_found},
            ),
            (
                ANSWER_GENERATING,
                layman_message(ANSWER_GENERATING, sources_found=sources_found),
                {"sources_found": sources_found},
            ),
            (
                ANSWER_COMPLETED,
                layman_message(ANSWER_COMPLETED),
                {"sources_found": sources_found},
            ),
        ]
    )
    for i, (event, message, meta) in enumerate(seq):
        run.activity.append(
            ActivityLine(event=event, message=message, elapsed_ms=i * 10, metadata=meta)
        )


def classification_snapshot(question: str, use_web_search: bool = False) -> tuple[dict, dict]:
    """Best-effort classify+plan capture for the trail log."""
    try:
        from app.services.rccs.classify import classify_retrieval, with_user_web_preference
        from app.services.rccs.plan import build_retrieval_plan

        c = with_user_web_preference(classify_retrieval(question), use_web_search)
        p = build_retrieval_plan(c, use_web_search=use_web_search, question=question)
        class_d = {
            "primary_intent": c.primary_intent,
            "freshness": c.freshness,
            "use_kb": c.use_kb,
            "use_official_live": c.use_official_live,
            "use_companions": c.use_companions,
            "companion_categories": c.companion_categories,
            "registry_topics": c.registry_topics,
            "routing_reason": c.routing_reason,
            "entities": [
                f"{e.normalized_name} ({e.entity_type})" for e in (c.entities or [])
            ],
            "confidence": c.confidence,
        }
        plan_d = {
            "companion_source_ids": p.companion_source_ids,
            "companion_categories": p.companion_categories,
            "browse_social": p.browse_social,
            "browse_domains": p.browse_domains,
            "allow_open_web": p.allow_open_web,
            "use_kb": p.use_kb,
            "use_official_live": p.use_official_live,
            "reason": p.reason,
        }
        return class_d, plan_d
    except Exception as exc:
        return {"error": str(exc)}, {}
