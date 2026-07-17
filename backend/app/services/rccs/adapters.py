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
        url = source.base_url or source.url_template
        if not url:
            return []
        # Optional template fill
        if "{q}" in url or "{entity}" in url:
            q = _entity_query(entity, query)
            url = url.replace("{q}", quote_plus(q)).replace("{entity}", quote_plus(q))

        url = normalize_url(url) or url
        if not is_allowed_url(
            url,
            channel="companion",
            plan=plan,
            matched_companions=[source],
        ):
            return []

        title = source.name
        text = (
            f"Registered {source.citation_label or 'social'} profile link for "
            f"{entity.normalized_name if entity else 'organization'}. "
            f"No post content was fetched."
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
    LinkOnlyAdapter(),
    RateMyProfessorsAdapter(),
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
