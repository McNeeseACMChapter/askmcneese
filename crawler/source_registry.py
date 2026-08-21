"""Backward-compatible adapter over the single governed registry reader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from governed_registry import REGISTRY_PATH, GovernedSource, load_governed_registry


@dataclass
class Source:
    source_id: str
    title: str
    url: str
    category: str
    trust_tier: str
    last_checked_date: str
    approval_status: str
    allowed_for_ai: str
    crawl_scope: str
    content_type: str = "html"
    source_group_ids: tuple[str, ...] = ()

    @property
    def crawl_allowed(self) -> bool:
        return self.allowed_for_ai.strip().lower().startswith(("yes", "true", "1"))

    @property
    def pm_approved(self) -> bool:
        return self.approval_status.strip().lower() == "approved"


def _normalize(url: str) -> str:
    parsed = urlparse(url.strip())
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"


def _legacy(source: GovernedSource) -> Source:
    return Source(
        source_id=source.source_id,
        title=source.title,
        url=source.url,
        category=source.category,
        trust_tier="A" if source.domain.endswith("mcneese.edu") else "B",
        last_checked_date=source.last_ingested_timestamp,
        approval_status=source.review_status,
        allowed_for_ai="Yes" if source.crawl_allowed else "No",
        crawl_scope=source.content_type,
        content_type=source.content_type,
        source_group_ids=source.source_group_ids,
    )


def load_registry(path: Path = REGISTRY_PATH) -> list[Source]:
    return [_legacy(source) for source in load_governed_registry(path)]


def find_source(url: str, registry: list[Source] | None = None) -> Source | None:
    target = _normalize(url)
    for source in registry if registry is not None else load_registry():
        if _normalize(source.url) == target:
            return source
    return None


def crawl_allowed_sources(registry: list[Source] | None = None) -> list[Source]:
    sources = registry if registry is not None else load_registry()
    return [source for source in sources if source.crawl_allowed]
