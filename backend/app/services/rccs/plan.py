"""Build an executable RetrievalPlan from classification + feature flags."""

from __future__ import annotations

from app.services.rccs import config as cfg
from app.services.rccs.classify import (
    INTENT_FACULTY_IDENTITY,
    INTENT_FACULTY_RATINGS,
    INTENT_ORG_ACTIVITY,
    INTENT_ORG_IDENTITY,
    INTENT_SOCIAL_PROFILE,
    INTENT_TERM_DEFINITION,
)
from app.services.rccs.browse_plan import build_browse_target
from app.services.rccs.companion_registry import match_companions
from app.services.rccs.models import RetrievalClassification, RetrievalPlan


def build_retrieval_plan(
    classification: RetrievalClassification,
    *,
    use_web_search: bool = False,
    question: str = "",
) -> RetrievalPlan:
    """Translate classification into concrete retrieval operations."""
    use_kb = classification.use_kb
    use_official = classification.use_official_live

    # Feature flags (read live)
    if not cfg.hybrid_enabled():
        if use_web_search:
            use_kb = False
            use_official = True
        else:
            use_kb = True
            use_official = False

    # Explicit Web Search forces official live — except term definitions, which
    # stay KB-first (hybrid may escalate once if KB is thin).
    if use_web_search and classification.primary_intent != INTENT_TERM_DEFINITION:
        use_official = True

    companion_ids: list[str] = []
    companion_categories: list[str] = []

    cats: list[str] = list(classification.companion_categories)
    has_faculty_entity = any(
        e.entity_type == "faculty_or_staff" for e in classification.entities
    )

    # Intent already requested companions (e.g. faculty ratings, org social).
    want_companions = (
        cfg.companions_enabled()
        and classification.use_companions
        and bool(cats)
    )

    # Web Search + faculty: also browse Rate My Professors (labeled student ratings).
    # Skip for term definitions — "assistant professor means" is not a person lookup.
    if (
        use_web_search
        and cfg.companions_enabled()
        and cfg.rmp_enabled()
        and classification.primary_intent != INTENT_TERM_DEFINITION
        and (
            classification.primary_intent
            in {INTENT_FACULTY_IDENTITY, INTENT_FACULTY_RATINGS}
            or has_faculty_entity
        )
    ):
        want_companions = True
        if "student_rating" not in cats:
            cats.append("student_rating")

    if want_companions and cats:
        filtered_cats: list[str] = []
        qlow = (question or "").lower()
        explicit_social = any(
            x in qlow
            for x in ("linkedin", "instagram", "facebook", "twitter", "handshake", "social media")
        )
        for c in cats:
            if c == "student_rating" and not cfg.rmp_enabled():
                continue
            # Global social flag off still allows social when the user named a platform.
            if c == "social" and not cfg.social_links_enabled() and not explicit_social:
                continue
            filtered_cats.append(c)

        if filtered_cats:
            entity_types = list({e.entity_type for e in classification.entities})
            if not entity_types and "student_rating" in filtered_cats:
                entity_types = ["faculty_or_staff"]
            if not entity_types and "social" in filtered_cats:
                entity_types = ["faculty_or_staff", "campus_organization", "student"]
            matched = match_companions(
                question or " ".join(classification.registry_topics),
                categories=filtered_cats,
                entity_types=entity_types,
            )
            companion_ids = [m.source_id for m in matched]
            companion_categories = filtered_cats

    # Knowledge-mode faculty identity: official McNeese only (no RMP).
    if classification.primary_intent == INTENT_FACULTY_IDENTITY and not use_web_search:
        companion_ids = []
        companion_categories = []

    # Admissions/policy: no companions
    if classification.primary_intent in {
        "admissions_policy",
        "academic_programs",
    }:
        companion_ids = []
        companion_categories = []

    entity_queries = [e.normalized_name for e in classification.entities]
    search_queries = [question] if question else []
    for e in classification.entities:
        search_queries.append(f"{e.normalized_name} McNeese")
        for alias in e.aliases:
            search_queries.append(f"{alias} McNeese")

    # Multi-intent decompose: expand search queries for who+ratings compounds
    try:
        from app.services.rccs.decompose import decompose_question

        decomposed = decompose_question(question or "")
        for sq in decomposed.subquestions:
            if sq.text and sq.text not in search_queries:
                search_queries.append(sq.text)
    except Exception:
        pass

    official_ids: list[str] = []
    if classification.primary_intent in {
        INTENT_FACULTY_IDENTITY,
        INTENT_FACULTY_RATINGS,
    }:
        official_ids = ["SRC-019", "SRC-034", "SRC-010"]
    elif classification.primary_intent in {
        INTENT_ORG_IDENTITY,
        INTENT_ORG_ACTIVITY,
        INTENT_SOCIAL_PROFILE,
    }:
        official_ids = ["SRC-029", "SRC-026", "SRC-016"]

    max_per = max(
        cfg.max_kb_results(),
        cfg.max_official_results(),
        cfg.max_companion_results(),
    )

    reason_parts = [classification.routing_reason]
    if companion_ids:
        reason_parts.append(f"companions={','.join(companion_ids)}")
    else:
        reason_parts.append("companions=none")

    browse = build_browse_target(
        question or "",
        classification,
        use_web_search=use_web_search,
    )
    if browse.reason:
        reason_parts.append(f"browse={browse.reason}")

    return RetrievalPlan(
        use_kb=use_kb,
        use_official_live=use_official,
        companion_source_ids=companion_ids,
        official_source_ids=official_ids,
        search_queries=search_queries,
        entity_queries=entity_queries,
        freshness=classification.freshness,
        max_results_per_channel=max_per,
        reason=" | ".join(reason_parts),
        companion_categories=companion_categories,
        primary_intent=classification.primary_intent,
        browse_domains=list(browse.domains),
        allow_open_web=browse.allow_open_web,
        browse_social=browse.social,
        max_pages_to_open=browse.max_pages_to_open,
    )
