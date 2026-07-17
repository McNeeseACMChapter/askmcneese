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


def capability_answer_text(*, use_web_search: bool = False) -> str:
    """Truthful reply for meta-questions about search ability."""
    caps = retrieval_capabilities()
    if not caps["official_web_search_available"]:
        return (
            "Official web search is currently disabled in this runtime. "
            "I can still answer from the McNeese knowledge base when Knowledge mode is selected."
        )
    mode_note = (
        "You currently have **Web search** selected, so I will search approved McNeese and campus "
        "web sources for this conversation."
        if use_web_search
        else "Select **Web search** in Sources to run live approved-page retrieval for a question; "
        "**McNeese knowledge** uses the indexed knowledge base."
    )
    companion_note = ""
    if caps.get("rmp_available"):
        companion_note = (
            "\n\nFor professor questions, I can also check **approved companion platforms** "
            "(currently Rate My Professors for McNeese) and label those results as student ratings — "
            "not official university records."
        )
    elif caps.get("companion_search_available"):
        companion_note = (
            "\n\nApproved companion sources may supplement official McNeese evidence when relevant."
        )
    return (
        "Yes. In **Web search** mode I can search **approved McNeese and campus-related web sources** "
        "(registry-matched pages plus live search filtered to trusted McNeese domains) and cite the "
        "pages I use. This is **not** unrestricted whole-web browsing.\n\n"
        f"{mode_note}"
        f"{companion_note}"
    )


def is_capability_question(question: str) -> bool:
    """Detect questions about the assistant's search/browse abilities."""
    import re

    q = re.sub(r"\s+", " ", (question or "").strip().lower())
    patterns = [
        r"\bcan you (?:do |perform |use )?web search\b",
        r"\bdo you (?:have |support |offer )?web search\b",
        r"\bcan you (?:browse|search) (?:the )?(?:web|internet|online)\b",
        r"\bdo you (?:have |have an )?internet\b",
        r"\bcan you (?:go online|look online|search online)\b",
        r"\bare you (?:able to |allowed to )?search the web\b",
        r"\bweb search (?:mode|available|enabled)\b",
        r"\blive (?:web )?search\b",
    ]
    return any(re.search(p, q) for p in patterns)
