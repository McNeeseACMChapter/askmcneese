"""Build an executable RetrievalPlan from classification + feature flags."""

from __future__ import annotations

from app.services.rccs import config as cfg
from urllib.parse import urlparse

from app.services.rccs.classify import (
    INTENT_ACADEMIC_CALENDAR,
    INTENT_COURSE_SCHEDULE,
    INTENT_DEGREE_PLAN,
    INTENT_FACULTY_IDENTITY,
    INTENT_FACULTY_RATINGS,
    INTENT_ORG_ACTIVITY,
    INTENT_ORG_IDENTITY,
    INTENT_SOCIAL_PROFILE,
    INTENT_TERM_DEFINITION,
    looks_social_link_lookup,
)
from app.services.rccs.browse_plan import build_browse_target
from app.services.rccs.companion_registry import get_companion, match_companions
from app.services.rccs.models import RetrievalClassification, RetrievalPlan

# Platform search hubs â€” never the answer for "what is the Facebook page for X".
_PLATFORM_HUB_IDS = {
    "SRC-C-FACEBOOK-001",
    "SRC-C-INSTAGRAM-001",
    "SRC-C-LINKEDIN-001",
}
_PRESENCE_ID = "SRC-C-PRESENCE-001"


def build_retrieval_plan(
    classification: RetrievalClassification,
    *,
    use_web_search: bool = False,
    question: str = "",
    campus_query=None,
) -> RetrievalPlan:
    """Translate classification into concrete retrieval operations."""
    use_kb = classification.use_kb
    use_official = classification.use_official_live
    compiled = None
    compiled_query: dict = {}
    route_policy: dict = {}
    source_group_ids: list[str] = []
    allow_agentic_web = False
    try:
        from app.services.campus_intelligence.config import enabled as campus_intelligence_enabled
        from app.services.campus_intelligence.compiler import compile_campus_query
        from app.services.campus_intelligence.route_policy import resolve_route_policy

        if campus_intelligence_enabled():
            compiled = campus_query or compile_campus_query(question)
            compiled_query = compiled.to_dict()
            resolved = resolve_route_policy(compiled)
            route_policy = resolved.to_dict()
            source_group_ids = list(compiled.required_source_groups)
            kb_state = resolved.channels["indexed_kb"].state
            official_state = resolved.channels["governed_official_fetch"].state
            use_kb = kb_state in {"PRIMARY", "REQUIRED"} or (
                kb_state == "FALLBACK" and classification.use_kb
            )
            use_official = official_state in {"PRIMARY", "REQUIRED"}
            allow_agentic_web = resolved.channels["agentic_web"].state not in {
                "FORBIDDEN", "NOT_APPLICABLE"
            }
            if compiled.action == "navigate" and compiled.requires_live_discovery:
                # Current destinations and product availability must be verified
                # live. A broad cached-KB wave adds stale, sibling-domain noise.
                use_kb = False
                use_official = True
    except Exception:
        # Configuration is additive. Legacy behavior is the safe rollback.
        compiled = None

    if classification.primary_intent == INTENT_TERM_DEFINITION:
        # Preserve the existing deterministic definition fast path. A topical
        # domain inference must not turn a vocabulary question into live lookup.
        use_kb = True
        use_official = False
        allow_agentic_web = False
    elif classification.primary_intent == INTENT_COURSE_SCHEDULE:
        # The validated Class Planner dataset owns meeting-time computation.
        # Generic RAG/live search is not an acceptable substitute.
        use_kb = False
        use_official = False
        allow_agentic_web = False

    # Feature flags (read live)
    if not cfg.hybrid_enabled():
        if use_web_search:
            use_kb = False
            use_official = True
        else:
            use_kb = True
            use_official = False

    # Explicit Web Search forces official live â€” except term definitions, which
    # stay KB-first (hybrid may escalate once if KB is thin).
    if use_web_search and classification.primary_intent != INTENT_TERM_DEFINITION:
        use_official = True

    link_lookup = looks_social_link_lookup(question)
    # Known social URL questions: companions only â€” skip slow official/agentic stacks.
    if link_lookup:
        use_official = False
        use_kb = False

    # Org identity / club questions: Presence JSON directory is enough.
    # Avoid KB noise + official SERP junk that used to wipe the answer path.
    org_presence_fast = (
        classification.primary_intent
        in {INTENT_ORG_IDENTITY, INTENT_ORG_ACTIVITY, INTENT_SOCIAL_PROFILE}
        and cfg.companions_enabled()
    )
    if org_presence_fast and not link_lookup:
        use_kb = False
        use_official = False
        if "social" not in classification.companion_categories:
            # ensure companion matching runs for Presence
            pass

    companion_ids: list[str] = []
    companion_categories: list[str] = []

    cats: list[str] = list(classification.companion_categories)
    has_faculty_entity = any(
        e.entity_type == "faculty_or_staff" for e in classification.entities
    )
    if link_lookup and "social" not in cats:
        cats.append("social")

    if org_presence_fast and "social" not in cats:
        cats.append("social")

    # Intent already requested companions (e.g. faculty ratings, org social).
    want_companions = (
        cfg.companions_enabled()
        and (classification.use_companions or link_lookup or org_presence_fast)
        and bool(cats)
    )

    # Web Search + faculty: also browse Rate My Professors (labeled student ratings).
    # Skip for term definitions â€” "assistant professor means" is not a person lookup.
    if (
        use_web_search
        and cfg.companions_enabled()
        and cfg.rmp_enabled()
        and classification.primary_intent != INTENT_TERM_DEFINITION
        and (
            classification.primary_intent == INTENT_FACULTY_RATINGS
            or (
                classification.primary_intent == INTENT_FACULTY_IDENTITY
                and has_faculty_entity
            )
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
            # Cap social fan-out â€” serial FB crawls of 12 hosts were ~35s each query.
            max_comp = 3 if link_lookup else (4 if "social" in filtered_cats else 4)
            matched = match_companions(
                question or " ".join(classification.registry_topics),
                categories=filtered_cats,
                entity_types=entity_types,
                max_sources=max_comp + (4 if link_lookup else 0),
            )
            if link_lookup:
                curated = [
                    m
                    for m in matched
                    if m.source_id not in _PLATFORM_HUB_IDS
                    and (urlparse(m.base_url or "").path or "").strip("/")
                ]
                matched = (curated or matched)[:3]
            else:
                matched = matched[:max_comp]
            companion_ids = [m.source_id for m in matched]
            companion_categories = filtered_cats

    # Org questions: Presence directory is the primary structured source.
    org_intent = classification.primary_intent in {
        INTENT_ORG_IDENTITY,
        INTENT_ORG_ACTIVITY,
        INTENT_SOCIAL_PROFILE,
    }
    if (
        org_intent
        and cfg.companions_enabled()
        and (classification.use_companions or link_lookup)
    ):
        presence = get_companion(_PRESENCE_ID)
        if (
            presence
            and presence.enabled
            and presence.allowed_for_ai_retrieval
        ):
            companion_ids = [_PRESENCE_ID] + [
                x for x in companion_ids if x != _PRESENCE_ID
            ]
            if "social" not in companion_categories:
                companion_categories.append("social")
            # Keep Presence + at most 2 curated socials (avoid FB crawl fan-out).
            if not link_lookup:
                companion_ids = companion_ids[:3]

    # Knowledge-mode faculty identity: official McNeese only (no RMP).
    if classification.primary_intent == INTENT_FACULTY_IDENTITY and not use_web_search:
        companion_ids = []
        companion_categories = []

    # Admissions/policy: no companions
    if classification.primary_intent in {
        "admissions_policy",
        "academic_programs",
        INTENT_DEGREE_PLAN,
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

    # Whole-registry routing: every question maps to matched seed sources.
    from app.services.source_registry import match_registry

    registry_match = match_registry(question or "", max_sources=5)
    official_ids = list(registry_match.source_ids)
    if source_group_ids:
        try:
            from app.services.campus_intelligence.registry import get_source_group

            configured_ids: list[str] = []
            for group_id in source_group_ids:
                group = get_source_group(group_id) or {}
                configured_ids.extend(group.get("source_ids") or [])
            # A compiled source group is an execution boundary, not merely a
            # ranking hint.  Mixing fuzzy whole-registry matches back into a
            # resolved bookstore/form/jobs route caused unrelated pages to be
            # opened and cited.  Fall back to fuzzy registry matches only when
            # the configured groups genuinely have no registered sources.
            if configured_ids:
                official_ids = list(dict.fromkeys(configured_ids))
        except Exception:
            pass

    # Academic date questions must lead with the Registrar schedule, even when
    # broad registry wording also resembles admissions or the main website.
    if classification.primary_intent == INTENT_ACADEMIC_CALENDAR:
        official_ids = ["SRC-012"]
    elif classification.primary_intent == "academic_programs":
        preferred = ["SRC-007", "SRC-011"]
        official_ids = preferred + [sid for sid in official_ids if sid not in preferred]
    elif classification.primary_intent == INTENT_DEGREE_PLAN:
        preferred = ["SRC-011", "SRC-007"]
        official_ids = preferred + [sid for sid in official_ids if sid not in preferred]


    # Keep specialty overlays as *additions* on top of registry matches.
    if classification.primary_intent in {
        INTENT_FACULTY_IDENTITY,
        INTENT_FACULTY_RATINGS,
    }:
        for sid in ("SRC-019", "SRC-034", "SRC-010"):
            if sid not in official_ids:
                official_ids.append(sid)
    elif classification.primary_intent in {
        INTENT_ORG_IDENTITY,
        INTENT_ORG_ACTIVITY,
        INTENT_SOCIAL_PROFILE,
    }:
        for sid in ("SRC-029", "SRC-026", "SRC-016"):
            if sid not in official_ids:
                official_ids.append(sid)

    max_per = max(
        cfg.max_kb_results(),
        cfg.max_official_results(),
        cfg.max_companion_results(),
    )

    reason_parts = [classification.routing_reason]
    if link_lookup:
        reason_parts.append("social_link_fast_path")
    if org_presence_fast:
        reason_parts.append("org_presence_fast_path")
    if companion_ids:
        reason_parts.append(f"companions={','.join(companion_ids)}")
    else:
        reason_parts.append("companions=none")
    if official_ids:
        reason_parts.append(f"registry={','.join(official_ids[:5])}")

    preferred_browse_domains = list(registry_match.browse_domains)
    if classification.primary_intent == INTENT_ACADEMIC_CALENDAR:
        # An unrelated historical/alumni registry hit must never expand a
        # Registrar query onto an affiliate domain.
        preferred_browse_domains = [
            "mcneese.edu", "www.mcneese.edu", "catalog.mcneese.edu", "schedule.mcneese.edu"
        ]
    browse = build_browse_target(
        question or "",
        classification,
        use_web_search=use_web_search,
        social_link_lookup=link_lookup,
        preferred_domains=preferred_browse_domains,
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
        compiled_query=compiled_query,
        route_policy=route_policy,
        source_group_ids=source_group_ids,
        answer_shape=(compiled.answer_shape if compiled else ""),
        required_fields=(list(compiled.required_fields) if compiled else []),
        allow_agentic_web=allow_agentic_web,
    )


