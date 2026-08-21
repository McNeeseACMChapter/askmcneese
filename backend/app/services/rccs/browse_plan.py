"""Classification-driven browse targets: where AskMcNeese may search and open pages.

The user prompt is classified first; this module turns that into domain filters
and whether the page-open agent may fetch full page HTML (not snippets only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.domain_registry import domains_for_question

from app.services.rccs.classify import (
    INTENT_FACULTY_RATINGS,
    INTENT_SOCIAL_PROFILE,
    RetrievalClassification,
)

_RMP = ["ratemyprofessors.com", "www.ratemyprofessors.com"]

_SOCIAL = [
    "linkedin.com",
    "www.linkedin.com",
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "issuu.com",
    "www.issuu.com",
    "joinhandshake.com",
    "app.joinhandshake.com",
]

# Hosts we never open (auth walls / noise), even in open-web mode.
_BLOCK_OPEN = {
    "accounts.google.com",
    "login.microsoftonline.com",
    "auth0.com",
    "okta.com",
    "chrome.google.com",
}

_OPEN_WEB_CUES = [
    r"\bgoogle\b",
    r"\bsearch (?:the )?(?:web|internet|online)\b",
    r"\bon the internet\b",
    r"\bonline\b",
    r"\bweb search\b",
    r"\bbrowse\b",
    r"\blook up\b",
    r"\bfind (?:online|on the web)\b",
]

_PERSON_CUES = [
    r"\bwho is\b",
    r"\blinkedin\b",
    r"\bprofile\b",
    r"\bfind .* (?:person|student|alumni)\b",
]


@dataclass
class BrowseTarget:
    """Where retrieval may search and which pages the open-agent may fetch."""

    domains: list[str] = field(default_factory=list)
    allow_open_web: bool = False
    max_pages_to_open: int = 4
    social: bool = False
    reason: str = ""


def wants_open_web(question: str) -> bool:
    q = (question or "").lower()
    return any(re.search(p, q) for p in _OPEN_WEB_CUES)


def wants_person_lookup(question: str) -> bool:
    q = (question or "").lower()
    return any(re.search(p, q) for p in _PERSON_CUES)


def host_blocked_for_open(host: str) -> bool:
    h = (host or "").lower().removeprefix("www.")
    if not h:
        return True
    if h in _BLOCK_OPEN or any(h.endswith("." + b) for b in _BLOCK_OPEN):
        return True
    return False


def build_browse_target(
    question: str,
    classification: RetrievalClassification,
    *,
    use_web_search: bool = False,
    social_link_lookup: bool = False,
    preferred_domains: list[str] | None = None,
) -> BrowseTarget:
    """Decide search/open scope from the classified prompt (+ UI web mode)."""
    domains = domains_for_question(question)
    social = False
    allow_open = False
    reasons: list[str] = []

    cats = set(classification.companion_categories or [])
    intent = classification.primary_intent or ""

    # Intent domains lead; registry matches may supplement but cannot poison scope.
    if preferred_domains:
        domains = domains + list(preferred_domains)
        reasons.append("intent domains before registry supplements")

    if intent == INTENT_FACULTY_RATINGS or "student_rating" in cats:
        domains.extend(_RMP)
        reasons.append("faculty ratings → Rate My Professors + McNeese")

    if intent == INTENT_SOCIAL_PROFILE or "social" in cats or wants_person_lookup(question):
        social = True
        domains.extend(_SOCIAL)
        reasons.append("social/person lookup → LinkedIn/social + McNeese")

    # Curated "what is the Facebook page" — cite registry URLs; do not open 4–5 pages.
    if social_link_lookup:
        social = True
        domains.extend(_SOCIAL)
        reasons.append("social link lookup → companions only (no page-open)")
        return BrowseTarget(
            domains=_dedupe_domains(domains),
            allow_open_web=False,
            max_pages_to_open=0,
            social=True,
            reason="; ".join(reasons),
        )

    # User selected Web mode or asked to search the open web.
    if use_web_search or wants_open_web(question):
        allow_open = True
        reasons.append("web mode / open-web cues → may open selected SERP pages")

    # Open pages when live channels need full HTML — not merely because social=True.
    if classification.use_official_live or use_web_search:
        allow_open = True

    max_pages = 3 if allow_open else 0
    if social and allow_open:
        max_pages = min(max(max_pages, 2), 3)

    return BrowseTarget(
        domains=_dedupe_domains(domains),
        allow_open_web=allow_open,
        max_pages_to_open=max_pages,
        social=social,
        reason="; ".join(reasons) or "McNeese-only browse",
    )


def _dedupe_domains(domains: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for d in domains:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def url_in_browse_domains(url: str, domains: list[str]) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(url).netloc or "").lower()
    if not host or host_blocked_for_open(host):
        return False
    for d in domains:
        d = d.lower().removeprefix("www.")
        h = host.removeprefix("www.")
        if h == d or h.endswith("." + d):
            return True
    return False
