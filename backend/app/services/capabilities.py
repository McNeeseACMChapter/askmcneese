"""Runtime capability snapshot for AskMcNeese (non-secret)."""

from __future__ import annotations

from app.services.rccs import config as cfg


def retrieval_capabilities() -> dict:
    """Safe capability snapshot for health/stats (no secrets)."""
    rccs = cfg.rccs_enabled()
    hybrid = rccs and cfg.hybrid_enabled()
    companions = rccs and cfg.companions_enabled()
    # Official live web is always available via legacy path OR RCCS.
    official_web = True
    try:
        from app.services.search_providers import provider_status, web_browsing_enabled

        browsing = web_browsing_enabled()
        providers = provider_status()
    except Exception:
        browsing = True
        providers = {}
    try:
        from app.services.perplexity_embeddings import embeddings_enabled
        from app.services.perplexity_agentic import agentic_enabled

        pplx_embed = embeddings_enabled() and bool(providers.get("perplexity_configured"))
        pplx_agent = agentic_enabled() and bool(providers.get("perplexity_configured"))
    except Exception:
        pplx_embed = False
        pplx_agent = False
    try:
        from app.services.orchestrator.config import supervisor_enabled as _supervisor_on

        supervisor_on = rccs and _supervisor_on()
    except Exception:
        supervisor_on = False
    return {
        "knowledge_search_available": True,
        "official_web_search_available": official_web,
        "web_browsing_enabled": browsing,
        "hybrid_retrieval_available": hybrid,
        "companion_search_available": companions,
        "rmp_available": companions and cfg.rmp_enabled(),
        "social_links_available": companions and cfg.social_links_enabled(),
        "rccs_enabled": rccs,
        "supervisor_enabled": supervisor_on,
        "perplexity_embeddings_enabled": pplx_embed,
        "perplexity_agentic_enabled": pplx_agent,
        "search_providers": {
            "tavily": bool(providers.get("tavily_configured")),
            "serper": bool(providers.get("serper_configured")),
            "serpapi": bool(providers.get("serpapi_configured")),
            "perplexity": bool(providers.get("perplexity_configured")),
            "preferred": providers.get("preferred_provider") or "auto",
        },
    }


def _humanize_domain(domain_id: str) -> str:
    special = {
        "general_campus": "General university information",
        "student_finance": "Tuition, fees, accounts, and payments",
        "wellbeing": "Health, counseling, and accessibility",
        "academic_support": "Library, tutoring, and academic support",
        "international_services": "International student services",
        "degree_requirements": "Degree requirements",
        "capability_discovery": "AskMcNeese help and source transparency",
    }
    return special.get(domain_id, domain_id.replace("_", " ").title())


def capability_answer_text(*, use_web_search: bool = False) -> str:
    """Render truthful self-knowledge from enabled domain packs and runtime flags."""
    from app.services.campus_intelligence.registry import capability_snapshot

    runtime = retrieval_capabilities()
    snapshot = capability_snapshot(runtime=runtime)
    status_labels = [
        ("fully_supported", "Configured structured coverage"),
        ("live_official", "Configured live-official coverage"),
        ("limited", "Limited support"),
        ("authenticated_only", "Requires authenticated access"),
        ("unavailable", "Not currently available"),
    ]
    sections: list[str] = [
        "Yes. Ask in your own words. I am strongest when your question needs a McNeese date, course, form, office, contact, published requirement, or step-by-step campus process.",
        "**Strongest verified workflows**\n"
        "- Fall 2026 class listings and schedule-conflict checks\n"
        "- Registrar location and published hours\n"
        "- Student ID replacement, academic-advisor, campus-health, international-student, and parking-appeal guidance\n"
        "- Academic deadlines when the term and year are clear",
        "**Source choices**\n"
        "- **Automatic:** recommended for almost every question; chooses the appropriate source path\n"
        "- **McNeese sources only:** restricts evidence to approved, governed campus sources; best for policy, dates, forms, and offices\n"
        "- **Web research:** adds current broader-web context when your question genuinely needs it",
    ]
    grouped = snapshot["domains_by_status"]
    for status, label in status_labels:
        domains = grouped.get(status) or []
        if not domains:
            if status in {"limited", "authenticated_only", "unavailable"}:
                if status == "authenticated_only":
                    sections.append(f"**{label}**\n- Personal application, account, billing, grades, transcript, and degree-progress status.")
                else:
                    sections.append(f"**{label}**\n- None declared by the active domain-pack configuration.")
            continue
        names = ", ".join(_humanize_domain(item["domain_id"]) for item in domains)
        sections.append(f"**{label}**\n- {names}")
    examples = [
        '"How do I find my academic advisor?"',
        '"Where is the Office of the Registrar, and what time does it close today?"',
        '"How do I replace my McNeese ID card?"',
        '"How do I appeal a parking citation?"',
    ]
    sections.append("**Questions you can try**\n" + "\n".join(f"- {item}" for item in examples))
    limitations = list(snapshot.get("limitations") or [])
    limitations.insert(0, "Grades, balances, application status, transcripts, degree progress, and other personal records stay in authenticated McNeese systems.")
    limitations.insert(1, "Registration, course drops, form submission, and university decisions remain with official McNeese systems and staff.")
    limitations.insert(2, "Configured topic coverage is not a guarantee that every wording or every page has complete evidence.")
    if not runtime.get("official_web_search_available"):
        limitations.append("Live official retrieval is disabled in this runtime, so live and term-based answers may be limited.")
    if use_web_search:
        limitations.append("Web research is selected for this conversation; outside sources are context, not authority for McNeese policy.")
    sections.append("**Boundaries**\n" + "\n".join(f"- {item}" for item in limitations))
    return "\n\n".join(sections)


def is_capability_question(question: str) -> bool:
    """Detect explicit product self-knowledge without fuzzy domain inference."""
    try:
        from app.services.campus_intelligence.compiler import is_product_self_knowledge_question

        return is_product_self_knowledge_question(question)
    except Exception:
        # Configuration failure must not create an expensive or unsafe fallback.
        import re

        q = re.sub(r"\s+", " ", (question or "").strip().lower())
        return bool(re.search(
            r"\bwhat can you (?:answer|do)\b|\bwhat can i ask\b|"
            r"\bshow (?:me )?(?:your )?capabilit|"
            r"\bcan you (?:do|use) (?:a |the )?(?:web |internet )?(?:search|browsing)\b|"
            r"\bdo you have (?:internet|web|browsing) access\b",
            q,
        ))


