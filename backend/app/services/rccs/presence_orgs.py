"""McNeese Presence / Involve public org API client.

Public JSON (no auth):
  GET https://api.presence.io/mcneese/v1/organizations
  GET https://api.presence.io/mcneese/v1/organizations/{uri}

Used to answer student-organization questions with description + social handles
from the official campus engagement directory.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from html import unescape
from typing import Any

import httpx

API_BASE = "https://api.presence.io/mcneese/v1"
PORTAL_ORG = "https://mcneese.presence.io/organization"
LIST_CACHE_TTL_SEC = 6 * 3600

_HTML_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_HANDLE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")


@dataclass
class PresenceOrgSummary:
    name: str
    uri: str
    description: str
    categories: list[str] = field(default_factory=list)
    meeting_time: str = ""
    meeting_location: str = ""
    member_count: int | None = None


@dataclass
class PresenceOrgDetail(PresenceOrgSummary):
    facebook: str = ""
    twitter: str = ""
    contact_name: str = ""
    portal_url: str = ""
    social_urls: list[tuple[str, str]] = field(default_factory=list)


_list_cache: list[PresenceOrgSummary] | None = None
_list_cache_at: float = 0.0


def clear_presence_cache() -> None:
    global _list_cache, _list_cache_at
    _list_cache = None
    _list_cache_at = 0.0


def strip_html(raw: str) -> str:
    text = unescape(_HTML_TAG.sub(" ", raw or ""))
    return _WS.sub(" ", text).strip()


def portal_url_for(uri: str) -> str:
    return f"{PORTAL_ORG}/{uri.strip('/')}"


def _social_url(platform: str, value: str) -> str | None:
    v = (value or "").strip()
    if not v:
        return None
    if v.startswith("http://") or v.startswith("https://"):
        return v
    # Display names with spaces are not safe vanity URLs
    if " " in v or not _HANDLE.match(v.replace(" ", "")):
        if " " in v:
            return None
    handle = v.lstrip("@")
    if not _HANDLE.match(handle):
        return None
    if platform == "facebook":
        return f"https://www.facebook.com/{handle}"
    if platform == "twitter":
        return f"https://x.com/{handle}"
    return None


def summary_from_api(row: dict[str, Any]) -> PresenceOrgSummary | None:
    name = (row.get("name") or "").strip()
    uri = (row.get("uri") or "").strip()
    if not name or not uri:
        return None
    mc = row.get("memberCount")
    try:
        member_count = int(mc) if mc is not None else None
    except (TypeError, ValueError):
        member_count = None
    return PresenceOrgSummary(
        name=name,
        uri=uri,
        description=strip_html(row.get("description") or ""),
        categories=[str(c) for c in (row.get("categories") or []) if c],
        meeting_time=(row.get("regularMeetingTime") or "").strip(),
        meeting_location=(row.get("regularMeetingLocation") or "").strip(),
        member_count=member_count,
    )


def detail_from_api(row: dict[str, Any]) -> PresenceOrgDetail | None:
    base = summary_from_api(row)
    if not base:
        return None
    facebook = (row.get("facebook") or "").strip()
    twitter = (row.get("twitter") or "").strip()
    socials: list[tuple[str, str]] = []
    fb_url = _social_url("facebook", facebook)
    if fb_url:
        socials.append(("Facebook", fb_url))
    elif facebook:
        socials.append(("Facebook (as listed on Presence)", facebook))
    tw_url = _social_url("twitter", twitter)
    if tw_url:
        socials.append(("X/Twitter", tw_url))
    elif twitter:
        socials.append(("X/Twitter (as listed on Presence)", twitter))
    return PresenceOrgDetail(
        name=base.name,
        uri=base.uri,
        description=base.description,
        categories=base.categories,
        meeting_time=base.meeting_time,
        meeting_location=base.meeting_location,
        member_count=base.member_count,
        facebook=facebook,
        twitter=twitter,
        contact_name=(row.get("contactName") or "").strip(),
        portal_url=portal_url_for(base.uri),
        social_urls=socials,
    )


async def fetch_organization_list(
    *,
    client: httpx.AsyncClient | None = None,
    force: bool = False,
) -> list[PresenceOrgSummary]:
    global _list_cache, _list_cache_at
    now = time.monotonic()
    if (
        not force
        and _list_cache is not None
        and (now - _list_cache_at) < LIST_CACHE_TTL_SEC
    ):
        return _list_cache

    async def _load(c: httpx.AsyncClient) -> list[PresenceOrgSummary]:
        r = await c.get(f"{API_BASE}/organizations", timeout=12.0)
        r.raise_for_status()
        rows = r.json()
        out: list[PresenceOrgSummary] = []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    s = summary_from_api(row)
                    if s:
                        out.append(s)
        return out

    if client is not None:
        orgs = await _load(client)
    else:
        async with httpx.AsyncClient(
            timeout=12.0,
            headers={"Accept": "application/json", "User-Agent": "AskMcNeese/1.0"},
        ) as c:
            orgs = await _load(c)

    _list_cache = orgs
    _list_cache_at = time.monotonic()
    return orgs


async def fetch_organization_detail(
    uri: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> PresenceOrgDetail | None:
    uri = (uri or "").strip().strip("/")
    if not uri:
        return None

    async def _load(c: httpx.AsyncClient) -> PresenceOrgDetail | None:
        r = await c.get(f"{API_BASE}/organizations/{uri}", timeout=10.0)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            return None
        return detail_from_api(data)

    if client is not None:
        return await _load(client)
    async with httpx.AsyncClient(
        timeout=10.0,
        headers={"Accept": "application/json", "User-Agent": "AskMcNeese/1.0"},
    ) as c:
        return await _load(c)


def score_org(org: PresenceOrgSummary, query: str, entity_name: str | None = None) -> int:
    q = (query or "").lower()
    name = org.name.lower()
    uri = org.uri.lower().replace("-", " ")
    score = 0
    if entity_name:
        en = entity_name.lower().strip()
        # Ignore junk entities like "at" from bad extractors
        if en and len(en) > 2 and en not in {"at", "of", "the", "club", "org"}:
            if en == name or en in name or name in en:
                score += 14
            en_tokens = [t for t in re.split(r"\s+", en) if len(t) > 2]
            if en_tokens and all(t in name for t in en_tokens):
                score += 10
            # "association for computing machinery" ↔ ACM
            if en.replace(" ", "") in name.replace(" ", ""):
                score += 6
    # Phrase / token overlap
    if name in q:
        score += 12
    name_tokens = [t for t in re.split(r"[^a-z0-9]+", name) if len(t) > 2]
    q_tokens = {t for t in re.split(r"[^a-z0-9]+", q) if len(t) > 2}
    # Drop ultra-common tokens that inflate Alumni Association matches
    q_tokens -= {"mcneese", "university", "state", "club", "student", "the", "what", "about"}
    overlap = sum(1 for t in name_tokens if t in q_tokens)
    score += overlap * 3
    if uri and any(t in uri for t in q_tokens if len(t) > 3):
        score += 3
    # Acronym: NSA, ACM, ASME — also from query phrase initials
    initials = "".join(t[0] for t in name_tokens if t)
    for tok in q_tokens:
        if len(tok) >= 2 and tok == initials.lower():
            score += 11
    # Strong content words unique to ACM
    if "computing" in q and "computing" in name:
        score += 8
    if "machinery" in q and "machinery" in name:
        score += 8
    if "nepalese" in q and "nepalese" in name:
        score += 10
    return score


def match_organizations(
    orgs: list[PresenceOrgSummary],
    query: str,
    *,
    entity_name: str | None = None,
    max_results: int = 5,
    min_score: int = 4,
) -> list[tuple[int, PresenceOrgSummary]]:
    scored = [(score_org(o, query, entity_name), o) for o in orgs]
    scored = [(s, o) for s, o in scored if s >= min_score]
    scored.sort(key=lambda x: (-x[0], x[1].name.lower()))
    return scored[:max_results]


def format_org_evidence(detail: PresenceOrgDetail) -> str:
    lines = [
        f"Organization: {detail.name}",
        f"Presence page: {detail.portal_url}",
    ]
    if detail.categories:
        lines.append("Categories: " + ", ".join(detail.categories))
    if detail.member_count is not None:
        lines.append(f"Listed members: {detail.member_count}")
    if detail.meeting_time:
        lines.append(f"Meeting time: {detail.meeting_time}")
    if detail.meeting_location:
        lines.append(f"Meeting location: {detail.meeting_location}")
    if detail.contact_name:
        lines.append(f"Contact (as listed): {detail.contact_name}")
    if detail.social_urls:
        lines.append("Social links from Presence:")
        for label, url in detail.social_urls:
            lines.append(f"  - {label}: {url}")
    elif detail.facebook or detail.twitter:
        lines.append("Social handles listed on Presence (could not form a clean URL):")
        if detail.facebook:
            lines.append(f"  - Facebook field: {detail.facebook}")
        if detail.twitter:
            lines.append(f"  - Twitter/X field: {detail.twitter}")
    else:
        lines.append("No Facebook/X handles were listed on this Presence profile.")
    if detail.description:
        lines.append("")
        lines.append("Description:")
        lines.append(detail.description[:3500])
    lines.append("")
    lines.append(
        "Source: McNeese Presence / Involve public organization directory "
        "(api.presence.io). Treat as campus engagement listing, not academic catalog policy."
    )
    return "\n".join(lines)


def format_list_evidence(
    matches: list[tuple[int, PresenceOrgSummary]],
    *,
    query: str,
) -> str:
    lines = [
        f"McNeese Presence organizations matching “{query.strip() or 'student organizations'}”:",
        f"Directory: https://mcneese.presence.io/organizations",
        "",
    ]
    for score, org in matches:
        lines.append(f"- {org.name}")
        lines.append(f"  Presence: {portal_url_for(org.uri)}")
        if org.categories:
            lines.append(f"  Categories: {', '.join(org.categories)}")
        snippet = (org.description or "")[:280]
        if snippet:
            lines.append(f"  Summary: {snippet}")
        lines.append(f"  match_score: {score}")
    lines.append("")
    lines.append(
        "Open an organization card on Presence for full description and social links."
    )
    return "\n".join(lines)
