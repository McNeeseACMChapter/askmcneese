"""Shared specialist for governed source/action records.

This adapter never turns a registered URL into a factual claim. It supplies
typed owner/action evidence so fetch failures can still produce an exact
destination, while date/status/availability claims remain gated by freshness.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from app.services.rccs.models import RetrievedEvidence, utcnow
from app.services.source_registry import load_registry
from .models import CampusQuery
from .registry import load_source_group_registry, source_groups_for


_MANIFEST = Path(__file__).resolve().parents[4] / "knowledge" / "index_manifest.json"
_STOP = {
    "what", "where", "when", "which", "about", "mcneese", "state", "university",
    "please", "find", "need", "available", "right", "now", "with", "from", "that",
    "this", "does", "have", "into", "your", "their", "student",
}
_WEAK_TITLE_TERMS = {
    "parking", "student", "campus", "office", "university", "health",
    "services", "mcneese", "state", "the", "and", "for",
}


def _record_title_fits_question(question: str, title: str) -> bool:
    """Reject office snapshots whose distinctive title is not what was asked."""
    distinctive = {
        token
        for token in (_terms(title) - _STOP - _WEAK_TITLE_TERMS)
        if len(token) >= 4
    }
    if not distinctive:
        return True
    query = _terms(question)
    if distinctive.intersection(query):
        return True
    for token in distinctive:
        for other in query:
            if min(len(token), len(other)) >= 4 and (
                token.startswith(other) or other.startswith(token)
            ):
                return True
    return False


def _terms(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2 and token not in _STOP
    }


@lru_cache(maxsize=1)
def _manifest_by_source() -> dict[str, dict]:
    try:
        payload = json.loads(_MANIFEST.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(item.get("source_id") or ""): item
        for item in payload.get("sources") or []
        if item.get("source_id")
    }


def _content_type(url: str, configured: str = "") -> str:
    if configured:
        return configured
    path = urlparse(url).path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if any(host in (urlparse(url).hostname or "").lower() for host in ("handshake.com", "schooljobs.com", "governmentjobs.com")):
        return "portal"
    return "html"


def retrieve_registry_records(
    question: str,
    campus_query: CampusQuery,
    *,
    limit: int = 5,
) -> list[RetrievedEvidence]:
    # Calendar dates are material, term-specific facts. Registry pointers cannot
    # prove them, and broad lexical matching previously promoted honor-roll/news
    # pages as if they were schedule records. The governed live-fetch channel
    # resolves and reads the term page instead.
    if campus_query.domain == "academic_calendar":
        return []

    required = set(campus_query.required_source_groups)
    group_registry = load_source_group_registry()["groups"]
    manifest = _manifest_by_source()
    query_terms = _terms(question)
    candidates: list[tuple[float, RetrievedEvidence]] = []
    compatible = {campus_query.intent}
    if campus_query.intent == "locate":
        compatible.add("find_contact")
    if campus_query.intent == "find_contact":
        compatible.add("locate")

    # Runtime answers use registry entries only as governed destinations. Facts
    # must come from pages opened for this request, so a manually curated record
    # cannot make one demonstration question stronger than another campus query.

    for source in load_registry():
        manifest_row = manifest.get(source.source_id) or {}
        groups = set(manifest_row.get("source_group_ids") or [])
        if not groups:
            groups = set(source_groups_for(source_id=source.source_id, url=source.url))
        if not groups.intersection(required):
            continue
        allowed_for_operation = any(
            (
                campus_query.domain in (group_registry[group_id].get("owner_domains") or [])
                or group_id == "official_directory"
            )
            and bool(compatible.intersection(group_registry[group_id].get("allowed_intents") or []))
            for group_id in groups.intersection(required)
        )
        if not allowed_for_operation:
            continue
        if not _record_title_fits_question(question, source.name or ""):
            continue

        # A registry-only employment leaf is not proof that a vacancy is still
        # open. Keep stable portal/category destinations, but suppress unverified
        # listing-looking URLs until live fetch/search confirms them.
        if campus_query.domain == "employment":
            source_path = urlparse(source.url).path.rstrip("/").lower()
            leaf = source_path.rsplit("/", 1)[-1]
            listing_like = source_path.startswith("/hr/employment/") and leaf not in {"student"}
            if (
                listing_like
                and not manifest_row.get("last_verified")
                and str(manifest_row.get("fetch_status") or "").lower() in {"registered", "pending", "error", ""}
            ):
                continue

        source_terms = _terms(
            f"{source.name} {source.category} {urlparse(source.url).path.replace('-', ' ')}"
        )
        overlap = len(query_terms.intersection(source_terms))
        direct_group_bonus = len(groups.intersection(required))
        verified = manifest_row.get("last_verified")
        action_expected = any(
            group_registry[group_id].get("action_links_expected")
            for group_id in groups.intersection(required)
        )
        score = 0.48 + min(overlap, 5) * 0.07 + min(direct_group_bonus, 3) * 0.05
        if source.source_id in {
            sid for group_id in required
            for sid in (group_registry.get(group_id, {}).get("source_ids") or [])
        }:
            score += 0.18

        descriptor = (
            "Governed campus source record. "
            f"Official owner/destination: {source.name}. "
            f"Category: {source.category or campus_query.domain}. "
            f"URL: {source.url}. "
            "Use this destination to review requirements and follow its official action links. "
            "This registry record verifies the approved destination, not changing facts such as "
            "current openings, deadlines, availability, or personal status."
        )
        evidence = RetrievedEvidence(
            evidence_id=f"ev-registry-{source.source_id}",
            title=source.name or "McNeese official destination",
            url=source.url,
            text=descriptor,
            source_id=source.source_id,
            source_name=source.name or source.source_id,
            source_tier=source.trust_tier,
            trust_level="official" if source.trust_tier == "A" else "campus_live",
            category=source.category or campus_query.domain,
            retrieval_channel="structured_specialist",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=min(score, 0.96),
            is_link_only=True,
            metadata={
                "citation_label": "Governed campus source registry",
                "source_groups": sorted(groups),
                "content_type": _content_type(source.url, manifest_row.get("content_type") or ""),
                "registry_status": manifest_row.get("registry_status") or "allowed",
                "fetch_status": manifest_row.get("fetch_status") or "registered",
                "last_verified": verified,
                "action_links": (
                    [{"label": source.name or "Official destination", "url": source.url}]
                    if action_expected else []
                ),
                "claim_boundary": "destination_only",
            },
        )
        candidates.append((score, evidence))

    candidates.sort(key=lambda pair: (-pair[0], pair[1].source_id))
    return [evidence for _, evidence in candidates[:limit]]
def clear_specialist_caches() -> None:
    _manifest_by_source.cache_clear()


