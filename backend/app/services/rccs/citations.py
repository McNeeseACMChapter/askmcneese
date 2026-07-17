"""Citation validation after generation — do not rely on the model alone."""

from __future__ import annotations

import re
from typing import Any

from app.services.rccs.allowlist import is_allowed_url, normalize_url
from app.services.rccs.models import RetrievedEvidence, RetrievalPlan


def validate_citations(
    answer: str,
    evidence: list[RetrievedEvidence],
    plan: RetrievalPlan | None = None,
) -> dict[str, Any]:
    """Validate citation integrity against the evidence set.

    Returns a result dict with cleaned citations and issues found.
    Does not re-call the LLM; callers may strip bad citations from metadata.
    """
    by_id = {e.evidence_id: e for e in evidence}
    by_url = {}
    for e in evidence:
        if e.url:
            by_url[normalize_url(e.url) or e.url] = e

    issues: list[str] = []
    valid_citations: list[dict[str, Any]] = []

    # Collect citation-like references in answer (optional — soft)
    mentioned_ids = set(re.findall(r"\bev-[a-z]+-[a-f0-9]+\b", answer or ""))
    for mid in mentioned_ids:
        if mid not in by_id:
            issues.append(f"unknown_evidence_id:{mid}")

    def _companions_for_evidence(ev: RetrievedEvidence) -> list:
        """Resolve registry companions for Tier C URLs (including agentic-tagged ones)."""
        from app.services.rccs.companion_registry import get_companion, load_companions

        companions = []
        direct = get_companion(ev.source_id)
        if direct:
            companions.append(direct)

        # Agentic / remapped evidence may keep source_id=PPLX_AGENTIC while URL is RMP.
        # Resolve from the active plan and/or domain allowlists so Sources can list them.
        plan_ids = set(plan.companion_source_ids) if plan else set()
        for src in load_companions():
            if not src.enabled or not src.allowed_for_ai_retrieval:
                continue
            if plan_ids and src.source_id not in plan_ids:
                continue
            if plan and plan.companion_categories and src.category not in plan.companion_categories:
                # Still allow if plan explicitly listed this companion id
                if src.source_id not in plan_ids:
                    continue
            if ev.url and any(
                d and d.lower() in (ev.url or "").lower() for d in (src.domain_allowlist or [])
            ):
                if src not in companions:
                    companions.append(src)
        return companions

    for ev in evidence:
        # Link-only must not be used as content proof — flag in metadata only
        cite = ev.to_citation()
        if ev.url:
            channel = "companion" if ev.source_tier == "C" else "official_live"
            # Full pages opened by the page-open agent after classification.
            if ev.metadata.get("page_fetched") and ev.trust_level in {
                "web_live",
                "campus_live",
                "social",
                "student_rating",
            }:
                ok = True
                if ev.trust_level == "web_live":
                    cite["citation_label"] = cite.get("citation_label") or "Opened web page"
            elif ev.source_tier == "C":
                companions = _companions_for_evidence(ev)
                ok = is_allowed_url(
                    ev.url,
                    channel="companion",
                    plan=plan,
                    matched_companions=companions,
                )
                if not ok and companions:
                    ok = is_allowed_url(
                        ev.url,
                        channel="companion",
                        plan=None,
                        matched_companions=companions,
                    )
                if ok and companions:
                    cite["source_id"] = companions[0].source_id
                    cite["citation_label"] = companions[0].citation_label or cite.get(
                        "citation_label"
                    )
            else:
                ok = is_allowed_url(ev.url, channel="official_live")
            if not ok:
                issues.append(f"blocked_url:{ev.url}")
                continue

        # Tier C must keep student_rating/social trust labels
        if ev.source_tier == "C" and ev.trust_level == "official":
            issues.append(f"tier_c_marked_official:{ev.evidence_id}")
            cite["trust_level"] = "third_party_context"

        valid_citations.append(cite)

    # Policy checks for answer text (soft warnings)
    low = (answer or "").lower()
    has_rating_claim = bool(
        re.search(r"\b(?:rated|rating|difficulty|would take again)\b", low)
    )
    has_rating_evidence = any(e.trust_level == "student_rating" and not e.metadata.get("fetch_failed") for e in evidence)
    if has_rating_claim and not has_rating_evidence:
        # If only link-only / failed RMP, warn
        if not any(e.trust_level == "student_rating" for e in evidence):
            issues.append("rating_claim_without_rating_evidence")

    has_official_claim_cues = bool(
        re.search(r"\b(?:department|associate professor|email|@mcneese\.edu|office)\b", low)
    )
    has_official_evidence = any(e.source_tier in {"A", "B"} for e in evidence)
    if has_official_claim_cues and not has_official_evidence:
        issues.append("official_claim_without_official_evidence")

    return {
        "ok": len([i for i in issues if not i.startswith("rating_claim")]) == 0
        or not any(i.startswith("blocked_") or i.startswith("unknown_") for i in issues),
        "issues": issues,
        "citations": valid_citations,
        "evidence_count": len(evidence),
    }


def evidence_to_chunk_responses(evidence: list[RetrievedEvidence]) -> list[dict[str, Any]]:
    """Map evidence to ChunkResponse-compatible dicts (required fields preserved)."""
    out = []
    for ev in evidence:
        out.append(
            {
                "chunk_id": ev.evidence_id,
                "text": ev.text[:500] if ev.text else "",
                "source_url": ev.url or "",
                "title": ev.title,
                "category": ev.category,
                "score": float(ev.relevance_score or 0.0),
                # Additive optional fields
                "source_tier": ev.source_tier,
                "trust_level": ev.trust_level,
                "retrieval_channel": ev.retrieval_channel,
                "is_link_only": ev.is_link_only,
                "source_id": ev.source_id,
            }
        )
    return out
