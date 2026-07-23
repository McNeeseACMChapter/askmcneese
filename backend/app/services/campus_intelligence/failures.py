"""Useful public failures shared across every campus domain."""

from __future__ import annotations

from .models import CampusQuery, EvidenceSufficiencyResult, ResolvedRoutePolicy
from .registry import load_failure_taxonomy


def render_precise_failure(
    query: CampusQuery,
    result: EvidenceSufficiencyResult,
    *,
    policy: ResolvedRoutePolicy | None = None,
    attempted_routes: list[str] | None = None,
) -> str:
    """Render a useful response without leaking retrieval internals."""
    if query.clarification_required and query.ambiguities:
        return query.ambiguities[0]
    if query.freshness == "personal":
        return (
            "That answer depends on your private McNeese record. I can explain the public process "
            "or point you to the correct sign-in page, but I cannot see your personal account."
        )
    if query.domain == "directory":
        person = str(query.entities.get("person") or "").strip()
        if person:
            return (
                f"I could not confidently match {person.title()} to one McNeese faculty or staff profile. "
                "Please share the department, course, or a more complete spelling and I will narrow it down."
            )
        return (
            "I could not verify the requested McNeese leadership record yet. "
            "Please include the full department or college name so I can distinguish current and former roles."
        )
    if query.domain == "employment":
        return (
            "I could not verify a current list of matching openings right now. "
            "Tell me whether you want on-campus student work, graduate assistantships, internships, "
            "or faculty/staff positions and I will search that live category directly."
        )
    if query.domain == "academic_calendar":
        return (
            "I could not verify that date on the current McNeese academic schedule. "
            "Please include the term, year, and session if you know it (for example, Regular Session)."
        )

    taxonomy = load_failure_taxonomy().get("failures") or {}
    codes = result.failure_codes or ["EVIDENCE_BELOW_THRESHOLD"]
    primary = codes[0]
    fallback = (taxonomy.get(primary) or {}).get(
        "user_message", "I could not verify a reliable answer yet."
    )
    return {
        "NO_MATCHING_RECORDS": "I could not find a confident match yet.",
        "INSUFFICIENT_FIELD_COVERAGE": "I found related information, but not enough to answer accurately yet.",
        "EVIDENCE_BELOW_THRESHOLD": "I found related information, but it did not directly answer your question.",
        "SOURCE_GROUP_NOT_CONFIGURED": "I could not reach the right public McNeese information for this question yet.",
    }.get(primary, fallback)