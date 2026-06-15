"""Load and query the approved source registry.

The registry is the Content/Knowledge team's seed file at
``knowledge/source_registry_seed.csv``. The crawler must only fetch URLs that
appear in this registry AND are marked allowed for AI retrieval.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "source_registry_seed.csv"


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

    @property
    def crawl_allowed(self) -> bool:
        """True when Content marked the source allowed for AI retrieval."""
        return self.allowed_for_ai.strip().lower().startswith("yes")

    @property
    def pm_approved(self) -> bool:
        """True only when a PM has formally approved the source."""
        return self.approval_status.strip().lower() == "approved"


def _normalize(url: str) -> str:
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/").lower()
    return f"{netloc}{path}"


def load_registry(path: Path = REGISTRY_PATH) -> list[Source]:
    if not path.exists():
        raise FileNotFoundError(f"Source registry not found at {path}")
    sources: list[Source] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            sources.append(
                Source(
                    source_id=row.get("Source ID", "").strip(),
                    title=row.get("Source Name", "").strip(),
                    url=row.get("Source URL", "").strip(),
                    category=row.get("Information Category", "").strip(),
                    trust_tier=row.get("Trust Level", "").strip(),
                    last_checked_date=row.get("Last Checked Date", "").strip(),
                    approval_status=row.get("Approval Status", "").strip(),
                    allowed_for_ai=row.get("Allowed for AI Retrieval", "").strip(),
                    crawl_scope=row.get("Crawl Scope", "").strip(),
                )
            )
    return sources


def find_source(url: str, registry: list[Source] | None = None) -> Source | None:
    registry = registry if registry is not None else load_registry()
    target = _normalize(url)
    for source in registry:
        if _normalize(source.url) == target:
            return source
    return None


def crawl_allowed_sources(registry: list[Source] | None = None) -> list[Source]:
    registry = registry if registry is not None else load_registry()
    return [s for s in registry if s.crawl_allowed]
