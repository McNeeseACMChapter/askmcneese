"""Citation validation after generation — do not rely on the model alone."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.services.rccs.allowlist import is_allowed_url, normalize_url
from app.services.rccs.models import RetrievedEvidence, RetrievalPlan


def select_relevant_citation_evidence(
    question: str,
    evidence: list[RetrievedEvidence],
    *,
    max_citations: int = 5,
) -> list[RetrievedEvidence]:
    """Keep the strongest, query-relevant proof instead of every retrieved link."""
    from app.services.rccs.evidence import (
        is_employment_question,
        lexical_relevance,
        looks_like_job_vacancy,
    )

    ranked = list(evidence)
    from app.services.program_inventory import is_program_inventory_question

    if is_employment_question(question):
        def _job_cite_key(item: RetrievedEvidence) -> tuple[int, float, int]:
            vacancy = looks_like_job_vacancy(
                title=item.title,
                text=item.text,
                url=item.url or "",
            )
            lexical = float(
                item.metadata.get("query_relevance")
                if item.metadata.get("query_relevance") is not None
                else lexical_relevance(question, item)
            )
            return (
                0 if vacancy else 1,
                -lexical,
                0 if item.retrieval_channel == "web_live" else 1,
            )

        ranked = sorted(evidence, key=_job_cite_key)
    elif is_program_inventory_question(question):
        def _program_cite_key(item: RetrievedEvidence) -> tuple[int, int, float]:
            inventory = 0 if item.category == "program_inventory" else 1
            undergrad_hub = 0 if "/undergraduate-programs" in (item.url or "").lower() else 1
            lexical = float(
                item.metadata.get("query_relevance")
                if item.metadata.get("query_relevance") is not None
                else lexical_relevance(question, item)
            )
            return (inventory, undergrad_hub, -lexical)

        ranked = sorted(evidence, key=_program_cite_key)

    selected: list[RetrievedEvidence] = []
    per_host: dict[str, int] = {}
    for item in ranked:
        if not item.url:
            continue
        if is_employment_question(question):
            vacancy = looks_like_job_vacancy(
                title=item.title,
                text=item.text,
                url=item.url or "",
            )
            blob = f"{item.title} {item.text} {item.url}".lower()
            # Prefer concrete vacancies; keep only official employment portals as fallback hubs.
            portalish = bool(
                re.search(
                    r"/hr/employment|/division-of-business-affairs/employment|careers\.mcneese|/employment/?$",
                    (item.url or "").lower(),
                )
            )
            if not vacancy and not portalish:
                continue
            if (
                re.search(
                    r"performing arts|study abroad|libguides|music major|handbook|"
                    r"\.pdf(?:$|\?)|employment.?scam|protecting.yourself.from.employment",
                    blob,
                )
                and not vacancy
            ):
                continue
        if is_program_inventory_question(question):
            url_l = (item.url or "").lower()
            if item.category != "program_inventory" and "/undergraduate-programs" not in url_l:
                # Keep catalog/colleges as secondary only after the inventory citation.
                if not re.search(r"catalog\.mcneese\.edu|/academics/colleges", url_l):
                    continue
            if "/graduate-programs" in url_l:
                continue
        query_score = float(
            item.metadata.get("query_relevance")
            if item.metadata.get("query_relevance") is not None
            else lexical_relevance(question, item)
        )
        # Link-only records are useful only when the requested entity/platform is
        # reflected in the title/URL. Content evidence gets semantic-score leeway.
        if item.is_link_only:
            url_tokens = f"{item.title} {item.url}".lower()
            if query_score < 0.08 and not any(
                token in url_tokens
                for token in re.findall(r"[a-z0-9]+", question.lower())
                if len(token) > 3
            ):
                continue
        elif query_score < 0.04 and not (
            is_employment_question(question)
            and looks_like_job_vacancy(title=item.title, text=item.text, url=item.url or "")
        ):
            continue

        host = (urlparse(item.url).hostname or "").lower().removeprefix("www.")
        host_cap = 3 if host.endswith("mcneese.edu") else 2
        if per_host.get(host, 0) >= host_cap:
            continue
        per_host[host] = per_host.get(host, 0) + 1
        selected.append(item)
        if len(selected) >= max(1, max_citations):
            break

    if not selected:
        selected = [item for item in evidence if item.url][:1]
    return selected

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
