"""Host adapters for companion and official retrieval.

Adapters fail closed and never bypass auth/CAPTCHA/bot protection.
"""

from __future__ import annotations

import asyncio
import re
from typing import Protocol
from urllib.parse import quote_plus, urlparse

from app.services.rccs.allowlist import is_allowed_url, normalize_url
from app.services.rccs.evidence import evidence_id_for, sanitize_evidence_text
from app.services.rccs.models import (
    CompanionSource,
    DetectedEntity,
    RetrievedEvidence,
    RetrievalPlan,
    utcnow,
)


class SourceAdapter(Protocol):
    def supports(self, source: CompanionSource) -> bool: ...

    async def retrieve(
        self,
        query: str,
        entity: DetectedEntity | None,
        source: CompanionSource,
        plan: RetrievalPlan,
    ) -> list[RetrievedEvidence]: ...


def _entity_query(entity: DetectedEntity | None, fallback: str) -> str:
    if entity and entity.normalized_name:
        return entity.normalized_name
    return fallback


def _resolve_companion_url(
    source: CompanionSource,
    query: str,
    entity: DetectedEntity | None,
) -> str:
    url = source.base_url or source.url_template
    if not url:
        return ""
    if "{q}" in url or "{entity}" in url:
        q = _entity_query(entity, query)
        url = url.replace("{q}", quote_plus(q)).replace("{entity}", quote_plus(q))
    return normalize_url(url) or url


def _link_only_evidence(
    source: CompanionSource,
    url: str,
    entity: DetectedEntity | None,
    *,
    fetch_note: str = "No post content was fetched.",
) -> list[RetrievedEvidence]:
    title = source.name
    who = entity.normalized_name if entity else "organization"
    # Include source_id + URL so near-dup text filters cannot collapse distinct profiles.
    text = (
        f"Registered {source.citation_label or 'social'} profile for {who}. "
        f"Source ID: {source.source_id}. URL: {url}. {fetch_note}"
    )
    return [
        RetrievedEvidence(
            evidence_id=evidence_id_for(url, title, "companion", 0),
            title=title,
            url=url,
            text=sanitize_evidence_text(text),
            source_id=source.source_id,
            source_name=source.name,
            source_tier="C",
            trust_level=source.trust_level or "social",
            category=source.category,
            retrieval_channel="companion",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=0.6,
            is_link_only=True,
            metadata={"citation_label": source.citation_label or "Social profile"},
        )
    ]


class LinkOnlyAdapter:
    """Curated social/profile URLs — never claim unread content."""

    def supports(self, source: CompanionSource) -> bool:
        return source.fetch_mode == "link_only"

    async def retrieve(
        self,
        query: str,
        entity: DetectedEntity | None,
        source: CompanionSource,
        plan: RetrievalPlan,
    ) -> list[RetrievedEvidence]:
        url = _resolve_companion_url(source, query, entity)
        if not url:
            return []
        if not is_allowed_url(
            url,
            channel="companion",
            plan=plan,
            matched_companions=[source],
        ):
            return []
        return _link_only_evidence(source, url, entity)


class HtmlFetchAdapter:
    """Curated McNeese-affiliated pages — crawl when web/social browse is on.

    Facebook/Instagram often serve login walls; on failure we still return the
    registered URL as link-only companion evidence (never invent posts).
    """

    def supports(self, source: CompanionSource) -> bool:
        return source.fetch_mode == "html_fetch"

    async def retrieve(
        self,
        query: str,
        entity: DetectedEntity | None,
        source: CompanionSource,
        plan: RetrievalPlan,
    ) -> list[RetrievedEvidence]:
        url = _resolve_companion_url(source, query, entity)
        if not url:
            return []
        if not is_allowed_url(
            url,
            channel="companion",
            plan=plan,
            matched_companions=[source],
        ):
            return []

        # Crawl only when the plan explicitly opens pages (content/activity asks).
        # Link-lookup plans set allow_open_web=False so Facebook/IG return instantly.
        should_fetch = bool(plan.allow_open_web and plan.max_pages_to_open > 0)
        if not should_fetch:
            return _link_only_evidence(
                source,
                url,
                entity,
                fetch_note=(
                    "Registered companion URL. Use this exact URL when the user asked "
                    "for the page/profile link."
                ),
            )

        page_text, title, ok = await self._fetch_safe(url)
        if not ok:
            return _link_only_evidence(
                source,
                url,
                entity,
                fetch_note=(
                    "Registered companion URL. Public page content could not be read "
                    "(login wall, bot protection, or empty response)."
                ),
            )

        body = (
            f"Companion page content from {source.citation_label or source.name} "
            f"(Tier C — not official academic policy).\n"
            f"URL: {url}\n\n"
            f"{sanitize_evidence_text(page_text, 3500)}"
        )
        return [
            RetrievedEvidence(
                evidence_id=evidence_id_for(url, title or source.name, "companion", 0),
                title=title or source.name,
                url=url,
                text=sanitize_evidence_text(body),
                source_id=source.source_id,
                source_name=source.name,
                source_tier="C",
                trust_level=source.trust_level or "social",
                category=source.category,
                retrieval_channel="companion",
                published_at=None,
                fetched_at=utcnow(),
                relevance_score=0.75,
                is_link_only=False,
                metadata={
                    "citation_label": source.citation_label or "Affiliated companion",
                    "page_fetched": True,
                },
            )
        ]

    async def _fetch_safe(self, url: str) -> tuple[str, str, bool]:
        try:
            from app.services.web_search import fetch_page_content

            page = await asyncio.wait_for(fetch_page_content(url), timeout=12.0)
            if page.success and page.content and len(page.content) > 40:
                return page.content, page.title or "", True
            return "", "", False
        except Exception:
            return "", "", False


class PresenceOrgAdapter:
    """McNeese Presence / Involve org directory via public JSON API.

    List + detail endpoints yield description, meeting info, and social handles
    without rendering the Angular SPA.
    """

    def supports(self, source: CompanionSource) -> bool:
        domains = " ".join(source.domain_allowlist).lower()
        return source.fetch_mode == "structured_adapter" and (
            source.source_id == "SRC-C-PRESENCE-001"
            or "presence.io" in domains
            or "api.presence.io" in domains
        )

    async def retrieve(
        self,
        query: str,
        entity: DetectedEntity | None,
        source: CompanionSource,
        plan: RetrievalPlan,
    ) -> list[RetrievedEvidence]:
        from app.services.rccs import presence_orgs as po

        entity_name = entity.normalized_name if entity else None
        list_url = "https://api.presence.io/mcneese/v1/organizations"
        if not is_allowed_url(
            list_url,
            channel="companion",
            plan=plan,
            matched_companions=[source],
        ):
            return _link_only_evidence(
                source,
                source.base_url or "https://mcneese.presence.io/organizations",
                entity,
                fetch_note="Presence API host not authorized for this plan.",
            )

        try:
            orgs = await po.fetch_organization_list()
        except Exception as e:
            print(f"Presence org list failed: {e}")
            return _link_only_evidence(
                source,
                "https://mcneese.presence.io/organizations",
                entity,
                fetch_note="Presence organization directory could not be loaded.",
            )

        if not orgs:
            return _link_only_evidence(
                source,
                "https://mcneese.presence.io/organizations",
                entity,
                fetch_note="Presence returned no public organizations.",
            )

        matches = po.match_organizations(
            orgs,
            query,
            entity_name=entity_name,
            max_results=5,
            min_score=6,
        )
        # Keep only a clear winner (+ optional close runner-up)
        if matches:
            best = matches[0][0]
            matches = [(s, o) for s, o in matches if s >= best - 3][:2]
        # Broad "what clubs / organizations" — return directory matches, not one detail.
        qlow = (query or "").lower()
        list_intent = any(
            p in qlow
            for p in (
                "list of",
                "what clubs",
                "what organizations",
                "which clubs",
                "which organizations",
                "student organizations",
                "get involved",
                "all organizations",
            )
        ) and not entity_name

        evidence: list[RetrievedEvidence] = []
        if list_intent or not matches:
            # If no strong match, still show best-effort top hits for discovery.
            show = matches or [
                (po.score_org(o, query, entity_name), o)
                for o in sorted(orgs, key=lambda x: x.name.lower())[:8]
            ]
            show = [(s, o) for s, o in show if s > 0][:8] or [
                (1, o) for o in orgs[:8]
            ]
            body = po.format_list_evidence(show, query=query)
            portal = "https://mcneese.presence.io/organizations"
            evidence.append(
                RetrievedEvidence(
                    evidence_id=evidence_id_for(portal, "McNeese Presence organizations", "companion", 0),
                    title="McNeese Presence — Student Organizations",
                    url=portal,
                    text=sanitize_evidence_text(body),
                    source_id=source.source_id,
                    source_name=source.name,
                    source_tier="C",
                    trust_level="campus_live",
                    category=source.category or "social",
                    retrieval_channel="companion",
                    published_at=None,
                    fetched_at=utcnow(),
                    relevance_score=0.85,
                    is_link_only=False,
                    metadata={
                        "citation_label": source.citation_label or "McNeese Presence",
                        "presence_mode": "list",
                        "org_count": len(orgs),
                    },
                )
            )
            if list_intent:
                return evidence

        # Detail for best match (+ optional runner-up if close)
        top = matches[:2] if matches else []
        for i, (score, summary) in enumerate(top):
            try:
                detail = await po.fetch_organization_detail(summary.uri)
            except Exception as e:
                print(f"Presence org detail failed ({summary.uri}): {e}")
                detail = None
            if not detail:
                # Fall back to list-card summary
                detail = po.PresenceOrgDetail(
                    name=summary.name,
                    uri=summary.uri,
                    description=summary.description,
                    categories=summary.categories,
                    meeting_time=summary.meeting_time,
                    meeting_location=summary.meeting_location,
                    member_count=summary.member_count,
                    portal_url=po.portal_url_for(summary.uri),
                )
            body = po.format_org_evidence(detail)
            evidence.append(
                RetrievedEvidence(
                    evidence_id=evidence_id_for(
                        detail.portal_url, detail.name, "companion", i
                    ),
                    title=f"{detail.name} — McNeese Presence",
                    url=detail.portal_url,
                    text=sanitize_evidence_text(body),
                    source_id=source.source_id,
                    source_name=source.name,
                    source_tier="C",
                    trust_level="campus_live",
                    category=source.category or "social",
                    retrieval_channel="companion",
                    published_at=None,
                    fetched_at=utcnow(),
                    relevance_score=min(0.95, 0.7 + score * 0.02),
                    is_link_only=False,
                    metadata={
                        "citation_label": source.citation_label or "McNeese Presence",
                        "presence_mode": "detail",
                        "presence_uri": detail.uri,
                        "social_urls": [u for _, u in detail.social_urls],
                    },
                )
            )
        return evidence[:3]


class RateMyProfessorsAdapter:
    """McNeese-scoped student ratings companion (school id 587).

    Uses template URL and/or DDG filtered to ratemyprofessors.com.
    Never fabricates ratings; never treats results as official.
    """

    def supports(self, source: CompanionSource) -> bool:
        return (
            source.category == "student_rating"
            and "ratemyprofessors.com" in " ".join(source.domain_allowlist)
        )

    async def retrieve(
        self,
        query: str,
        entity: DetectedEntity | None,
        source: CompanionSource,
        plan: RetrievalPlan,
    ) -> list[RetrievedEvidence]:
        name = _entity_query(entity, "")
        if not name:
            return []

        evidence: list[RetrievedEvidence] = []
        search_q = (
            f"{name} McNeese Rate My Professors rating difficulty "
            f"number of ratings would take again"
        )

        # 1) Paid search APIs scoped to ratemyprofessors.com (snippets often have ratings)
        try:
            from app.services.search_providers import search_web

            hits = await search_web(
                search_q,
                max_results=6,
                include_domains=["ratemyprofessors.com", "www.ratemyprofessors.com"],
                providers=["tavily", "serper", "serpapi", "perplexity", "ddg"],
            )
# Prefer professor profile pages matching the faculty name
            ranked = sorted(
                hits,
                key=lambda h: (
                    0 if "/professor/" in (h.url or "") else 1,
                    0 if name.lower() in f"{h.title} {h.snippet}".lower() else 1,
                ),
            )
            for i, hit in enumerate(ranked):
                blob = f"{hit.title}\n{hit.snippet}"
                if hit.url and not is_allowed_url(
                    hit.url,
                    channel="companion",
                    plan=plan,
                    matched_companions=[source],
                ):
                    continue
                if hit.snippet and not self._name_appears(name, blob) and hit.url:
                    # Keep search hit if URL is professor page for McNeese school
                    if "/professor/" not in (hit.url or "") and "search/professors" not in (hit.url or ""):
                        continue
                    if not self._name_appears(name, hit.title or ""):
                        continue
                extracted = self._extract_rating_bits(blob)
                # If snippet lacks numbers but we have a professor URL, try page fetch
                page_extra = ""
                if "Verified fields:" not in extracted and hit.url and "/professor/" in hit.url:
                    page_text, title, ok = await self._fetch_safe(hit.url)
                    if ok:
                        blob2 = f"{title}\n{page_text}"
                        if self._name_appears(name, blob2):
                            extracted = self._extract_rating_bits(blob2)
                            page_extra = sanitize_evidence_text(page_text, 2000)
                body = (
                    f"Student-submitted ratings context for {name} (NOT official McNeese data).\n"
                    f"Provider: {hit.provider}\n"
                    f"{extracted}\n"
                    f"Search snippet:\n{sanitize_evidence_text(hit.snippet or hit.title, 2500)}\n"
                )
                if page_extra:
                    body += f"Page excerpt:\n{page_extra}\n"
                body += "Only use numbers that appear above. Do not invent ratings or review counts."
                has_nums = "Verified fields:" in extracted
                evidence.append(
                    RetrievedEvidence(
                        evidence_id=evidence_id_for(
                            hit.url or f"rmp-{name}-{i}", hit.title or source.name, "companion", i
                        ),
                        title=hit.title or f"Rate My Professors — {name}",
                        url=hit.url or None,
                        text=sanitize_evidence_text(body),
                        source_id=source.source_id,
                        source_name=source.name,
                        source_tier="C",
                        trust_level="student_rating",
                        category="student_rating",
                        retrieval_channel="companion",
                        published_at=None,
                        fetched_at=utcnow(),
                        relevance_score=0.9 if has_nums else 0.65,
                        is_link_only=not bool(hit.snippet),
                        metadata={
                            "citation_label": source.citation_label
                            or "Student ratings (Rate My Professors)",
                            "provider": hit.provider,
                            "fetch_failed": not has_nums,
                        },
                    )
                )
        except Exception as e:
            print(f"RMP provider search failed: {e}")

        if any(not e.metadata.get("fetch_failed") for e in evidence):
            return evidence[:3]

        # 2) Fallback: template URL + HTML fetch
        urls: list[str] = []
        if source.url_template:
            urls.append(
                source.url_template.replace("{q}", quote_plus(name)).replace(
                    "{entity}", quote_plus(name)
                )
            )

        for i, url in enumerate(urls[:2]):
            nu = normalize_url(url) or url
            if not is_allowed_url(
                nu, channel="companion", plan=plan, matched_companions=[source]
            ):
                continue
            page_text, title, ok = await self._fetch_safe(nu)
            if ok and self._name_appears(name, f"{title}\n{page_text}"):
                extracted = self._extract_rating_bits(page_text)
                body = (
                    f"Student-submitted ratings context for {name} (NOT official McNeese data).\n"
                    f"{extracted}\n"
                    f"Source excerpt:\n{sanitize_evidence_text(page_text, 2500)}"
                )
                evidence.append(
                    RetrievedEvidence(
                        evidence_id=evidence_id_for(nu, title or source.name, "companion", 10 + i),
                        title=title or f"Rate My Professors — {name}",
                        url=nu,
                        text=sanitize_evidence_text(body),
                        source_id=source.source_id,
                        source_name=source.name,
                        source_tier="C",
                        trust_level="student_rating",
                        category="student_rating",
                        retrieval_channel="companion",
                        published_at=None,
                        fetched_at=utcnow(),
                        relevance_score=0.8,
                        is_link_only=False,
                        metadata={
                            "citation_label": source.citation_label
                            or "Student ratings (Rate My Professors)",
                        },
                    )
                )

        return evidence[:4]
    async def _fetch_safe(self, url: str) -> tuple[str, str, bool]:
        try:
            from app.services.web_search import fetch_page_content

            page = await asyncio.wait_for(fetch_page_content(url), timeout=12.0)
            if page.success and page.content and len(page.content) > 40:
                return page.content, page.title or "", True
            return "", "", False
        except Exception:
            return "", "", False

    @staticmethod
    def _name_appears(name: str, blob: str) -> bool:
        parts = [p for p in re.split(r"\s+", name.strip()) if p]
        if not parts:
            return False
        low = blob.lower()
        # Require last token (surname) and prefer full name
        if parts[-1].lower() not in low:
            return False
        if len(parts) >= 2:
            return parts[0].lower() in low or name.lower() in low
        return True

    @staticmethod
    def _extract_rating_bits(text: str) -> str:
        bits: list[str] = []
        # Conservative regexes — only report numbers that appear in text/snippets
        patterns = [
            ("quality", r"(?:quality|overall|rating)[^\d]{0,24}(\d(?:\.\d)?)\s*(?:/\s*5)?"),
            ("quality", r"(\d(?:\.\d)?)\s*/\s*5"),
            ("difficulty", r"difficulty[^\d]{0,24}(\d(?:\.\d)?)"),
            ("ratings_count", r"(\d+)\s*ratings?"),
            ("would_take_again", r"(\d{1,3})%\s*would take again"),
        ]
        seen_labels: set[str] = set()
        for label, pat in patterns:
            if label in seen_labels:
                continue
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                bits.append(f"{label}: {m.group(1)}")
                seen_labels.add(label)
        if not bits:
            return "No structured rating fields could be verified from the page content."
        return "Verified fields: " + "; ".join(bits)


ADAPTERS: list[SourceAdapter] = [
    PresenceOrgAdapter(),
    RateMyProfessorsAdapter(),
    HtmlFetchAdapter(),
    LinkOnlyAdapter(),
]


async def retrieve_from_companion(
    source: CompanionSource,
    query: str,
    entity: DetectedEntity | None,
    plan: RetrievalPlan,
) -> list[RetrievedEvidence]:
    for adapter in ADAPTERS:
        if adapter.supports(source):
            return await adapter.retrieve(query, entity, source, plan)
    # Default: link_only fallback if base_url present
    return await LinkOnlyAdapter().retrieve(query, entity, source, plan)
