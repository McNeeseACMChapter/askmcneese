"""Companion registry loader — Tier C external sources only.

Official sources remain in knowledge/source_registry_seed.csv.
Companions are never ingested into ChromaDB.
"""

from __future__ import annotations

import csv
import os
from functools import lru_cache
from urllib.parse import urlparse

from app.services.rccs.models import CompanionSource


def _companions_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    # rccs -> services -> app -> backend -> askmcneese -> knowledge
    repo_ask = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    return os.path.join(repo_ask, "knowledge", "source_registry_companions.csv")


def _split_list(raw: str) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in re_split(raw) if p.strip()]


def re_split(raw: str) -> list[str]:
    # Support | or ; or comma separators
    for sep in ("|", ";"):
        if sep in raw:
            return raw.split(sep)
    return [p.strip() for p in raw.split(",") if p.strip()] if raw else []


def _truthy(raw: str) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def load_companions() -> list[CompanionSource]:
    path = _companions_path()
    if not os.path.exists(path):
        alt = os.path.join(os.getcwd(), "knowledge", "source_registry_companions.csv")
        path = alt if os.path.exists(alt) else path
    if not os.path.exists(path):
        return []

    out: list[CompanionSource] = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = (row.get("source_id") or "").strip()
                if not sid:
                    continue
                # Tier C must never allow chroma ingest regardless of CSV typos
                allow_chroma = _truthy(row.get("allow_chroma_ingest") or "")
                if (row.get("source_tier") or "C").strip().upper() == "C":
                    allow_chroma = False

                keywords = {
                    k.lower()
                    for k in _split_list(row.get("topic_keywords") or "")
                }
                aliases = _split_list(row.get("aliases") or "")
                domains = [d.lower() for d in _split_list(row.get("domain_allowlist") or "")]

                out.append(
                    CompanionSource(
                        source_id=sid,
                        name=(row.get("name") or "").strip(),
                        description=(row.get("description") or "").strip(),
                        content_type=(row.get("content_type") or "external_companion").strip(),
                        source_tier=(row.get("source_tier") or "C").strip().upper(),
                        category=(row.get("category") or "").strip(),
                        base_url=(row.get("base_url") or "").strip(),
                        url_template=(row.get("url_template") or "").strip(),
                        domain_allowlist=domains,
                        query_template=(row.get("query_template") or "").strip(),
                        fetch_mode=(row.get("fetch_mode") or "link_only").strip(),
                        trust_level=(row.get("trust_level") or "third_party_context").strip(),
                        entity_types=[e.lower() for e in _split_list(row.get("entity_types") or "")],
                        topic_keywords=keywords,
                        aliases=aliases,
                        enabled=_truthy(row.get("enabled") or "false"),
                        allowed_for_ai_retrieval=_truthy(
                            row.get("allowed_for_ai_retrieval") or "false"
                        ),
                        allow_chroma_ingest=allow_chroma,
                        citation_label=(row.get("citation_label") or "").strip(),
                        notes=(row.get("notes") or "").strip(),
                    )
                )
    except Exception as e:
        print(f"Companion registry load error: {e}")
        return []
    return out


def match_companions(
    query: str,
    categories: list[str] | None = None,
    entity_types: list[str] | None = None,
    max_sources: int = 4,
) -> list[CompanionSource]:
    """Return enabled companions matching category/entity/keywords."""
    registry = [c for c in load_companions() if c.enabled and c.allowed_for_ai_retrieval]
    if not registry:
        return []

    cats = {c.lower() for c in (categories or [])}
    etypes = {e.lower() for e in (entity_types or [])}
    q = (query or "").lower()
    q_words = {w.strip(".:;()?!") for w in q.split() if len(w) > 1}

    scored: list[tuple[int, CompanionSource]] = []
    for src in registry:
        if cats and src.category.lower() not in cats:
            continue
        if etypes and src.entity_types and not (set(src.entity_types) & etypes):
            # Allow if no entity type filter match but keywords hit strongly
            pass

        score = 0
        if cats and src.category.lower() in cats:
            score += 5
        if etypes and set(src.entity_types) & etypes:
            score += 3
        for kw in src.topic_keywords:
            if " " in kw and kw in q:
                score += 4
            elif kw in q_words:
                score += 2
        for alias in src.aliases:
            if alias.lower() in q:
                score += 5
        # Prefer curated org/profile URLs over platform search hubs
        path = (urlparse(src.base_url or "").path or "").strip("/")
        if path and src.fetch_mode == "html_fetch":
            score += 3
        if score > 0:
            scored.append((score, src))

    # If category filter provided but nothing scored, still return category matches
    if not scored and cats:
        for src in registry:
            if src.category.lower() in cats:
                scored.append((1, src))

    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:max_sources]]


def get_companion(source_id: str) -> CompanionSource | None:
    for c in load_companions():
        if c.source_id == source_id:
            return c
    return None


def clear_companion_cache() -> None:
    load_companions.cache_clear()
    try:
        from app.services.rccs.presence_orgs import clear_presence_cache

        clear_presence_cache()
    except Exception:
        pass
