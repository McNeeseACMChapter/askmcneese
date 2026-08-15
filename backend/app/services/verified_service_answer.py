"""Deterministic answers from governed, date-stamped campus service records."""

from __future__ import annotations

import re


_STOP = {
    "what", "where", "when", "which", "with", "from", "that", "this", "mcneese",
    "student", "office", "please", "need", "want", "have", "does", "should",
}


def _terms(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2 and token not in _STOP
    }


def direct_verified_service_answer(
    question: str,
    chunks: list[dict],
    retrieval_status: dict | None = None,
) -> str | None:
    """Release only the strongest substantive snapshot, never a registry pointer."""
    question_terms = _terms(question)
    sufficiency = (retrieval_status or {}).get("evidence_sufficiency") or {}
    resolutions = sufficiency.get("field_resolutions") or {}
    support_counts: dict[str, int] = {}
    for resolution in resolutions.values():
        if not isinstance(resolution, dict) or resolution.get("status") != "RESOLVED":
            continue
        for evidence_id in set(resolution.get("evidence_ids") or []):
            key = str(evidence_id)
            support_counts[key] = support_counts.get(key, 0) + 1
    ranked: list[tuple[int, float, dict]] = []
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        if not metadata.get("curated_snapshot"):
            continue
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        title = str(chunk.get("title") or "")
        title_overlap = len(question_terms & _terms(title))
        content_overlap = len(question_terms & _terms(text))
        support_score = 20 * support_counts.get(str(chunk.get("chunk_id") or ""), 0)
        ranked.append((support_score + title_overlap * 3 + content_overlap, float(chunk.get("score") or 0), chunk))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1]))
    if question_terms and ranked[0][0] <= 0:
        return None
    source = ranked[0][2]
    title = str(source.get("title") or "McNeese campus service").strip()
    text = str(source.get("text") or "").strip()
    url = str(source.get("source_url") or "").strip()
    answer = f"**{title}**\n\n{text}"
    if url:
        answer += f"\n\nSource: [{title}]({url})"
    return answer
