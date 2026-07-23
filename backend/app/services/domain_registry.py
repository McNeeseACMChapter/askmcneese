"""Governed registry for public McNeese-owned and McNeese-affiliated domains.

The registry is intentionally finite and auditable. Discovery may propose new
domains, but only enabled Tier A/B records become official retrieval targets.
Private hosts, authentication walls, and unreviewed partners remain excluded.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class DomainRecord:
    domain: str
    trust_tier: str
    relationship: str
    categories: frozenset[str] = field(default_factory=frozenset)
    crawl_policy: str = "targeted"
    enabled: bool = False
    discovered_from: str = ""
    notes: str = ""


_FALLBACK_DOMAINS = (
    "mcneese.edu",
    "catalog.mcneese.edu",
    "schedule.mcneese.edu",
    "mcneesesports.com",
    "mcneesecowboystore.com",
    "mcneesereslife.com",
    "mcneese.presence.io",
    "api.presence.io",
)

_CATEGORY_CUES: dict[str, set[str]] = {
    "athletics": {"athletics", "athletic", "athlete", "athletes", "sport", "sports", "football", "basketball", "baseball", "softball", "soccer", "volleyball", "track", "rodeo", "intramural", "roster", "game", "tickets", "cowboys", "cowgirls"},
    "bookstore": {"bookstore", "textbook", "textbooks", "merch", "merchandise", "apparel", "cowboy store"},
    "housing": {"housing", "residence", "reslife", "dorm", "dorms", "move-in", "floor plan"},
    "dining": {"dining", "food", "meal", "meals", "cafeteria", "menu"},
    "foundation": {"foundation", "donor", "donors", "giving", "donate", "endowment"},
    "alumni": {"alumni", "alumnus", "alumna", "membership"},
    "organizations": {"organization", "organizations", "club", "clubs", "engagement", "get involved"},
    "arts": {"banners", "arts", "cultural", "performance"},
    "radio": {"kbys", "radio"},
    "research": {"research", "economic", "economics", "drew center"},
    "policies": {"policy", "policies", "appeal", "suspension", "probation", "complaint", "ferpa", "governance"},
    "career": {"career", "handshake", "job", "jobs", "internship", "internships", "co-op", "resume", "employment"},
}


def _registry_path() -> Path:
    return Path(__file__).resolve().parents[3] / "knowledge" / "mcneese_domain_registry.csv"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "enabled"}


@lru_cache(maxsize=1)
def load_domain_registry() -> tuple[DomainRecord, ...]:
    path = _registry_path()
    records: list[DomainRecord] = []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                domain = (row.get("domain") or "").strip().lower().removeprefix("www.")
                tier = (row.get("trust_tier") or "").strip().upper()
                if not domain or tier not in {"A", "B", "C"}:
                    continue
                records.append(DomainRecord(
                    domain=domain,
                    trust_tier=tier,
                    relationship=(row.get("relationship") or "").strip(),
                    categories=frozenset(
                        item.strip().lower()
                        for item in (row.get("categories") or "").split("|")
                        if item.strip()
                    ),
                    crawl_policy=(row.get("crawl_policy") or "targeted").strip().lower(),
                    enabled=_truthy(row.get("enabled")),
                    discovered_from=(row.get("discovered_from") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                ))
    except OSError:
        return tuple(
            DomainRecord(d, "A" if d.endswith("mcneese.edu") else "B", "fallback", enabled=True)
            for d in _FALLBACK_DOMAINS
        )
    return tuple(records)


def host_matches_domain(host: str, domain: str) -> bool:
    host = (host or "").strip().lower().removeprefix("www.")
    domain = (domain or "").strip().lower().removeprefix("www.")
    return bool(host and domain and (host == domain or host.endswith("." + domain)))


def record_for_host(host: str) -> DomainRecord | None:
    candidates = [
        record for record in load_domain_registry()
        if record.enabled and host_matches_domain(host, record.domain)
    ]
    return max(candidates, key=lambda record: len(record.domain), default=None)


def record_for_url(url: str) -> DomainRecord | None:
    try:
        return record_for_host(urlparse(url).hostname or "")
    except Exception:
        return None


def official_domains(*, public_only: bool = False) -> list[str]:
    return [
        record.domain
        for record in load_domain_registry()
        if record.enabled
        and record.trust_tier in {"A", "B"}
        and (not public_only or record.crawl_policy == "public")
    ]


def domains_for_question(question: str) -> list[str]:
    """Return a small intent-ordered domain set for provider search."""
    q = (question or "").lower()
    tokens = set(re.findall(r"[a-z0-9-]+", q))
    wanted: set[str] = set()
    for category, cues in _CATEGORY_CUES.items():
        if any((" " in cue and cue in q) or cue in tokens for cue in cues):
            wanted.add(category)

    records = [r for r in load_domain_registry() if r.enabled and r.trust_tier in {"A", "B"}]
    scoped = [r.domain for r in records if wanted.intersection(r.categories)]
    core = ["mcneese.edu", "catalog.mcneese.edu", "schedule.mcneese.edu"]
    ordered: list[str] = []
    for domain in scoped + core:
        if domain not in ordered and record_for_host(domain):
            ordered.append(domain)
    return ordered


def trust_tier_for_url(url: str, default: str = "B") -> str:
    record = record_for_url(url)
    return record.trust_tier if record else default
