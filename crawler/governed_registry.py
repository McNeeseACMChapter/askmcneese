"""One governed registry reader for every crawler/ingestion entrypoint."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "knowledge" / "source_registry_merged.csv"
SOURCE_GROUP_PATH = REPO_ROOT / "knowledge" / "campus_intelligence" / "source_groups.json"
_AUTO_DISCOVERY = {"seed", "sitemap_xml", "catalog_browse", "catalog_inventory", "ecosystem_sitemap"}
_OFFICIAL_HOSTS = {"mcneese.edu", "www.mcneese.edu", "catalog.mcneese.edu", "schedule.mcneese.edu"}


@dataclass(frozen=True)
class GovernedSource:
    source_id: str
    title: str
    url: str
    domain: str
    content_type: str
    category: str
    parent_source_id: str
    catalog_year: str
    priority: str
    review_status: str
    allowed_for_ai: str
    last_ingested_timestamp: str
    content_hash: str
    discovered_from: str
    notes: str
    source_group_ids: tuple[str, ...]

    @property
    def explicitly_allowed(self) -> bool:
        value = self.allowed_for_ai.strip().lower()
        return value.startswith("yes") or value in {"true", "1"}

    @property
    def crawl_allowed(self) -> bool:
        if self.explicitly_allowed:
            return True
        host = (urlparse(self.url).hostname or "").lower()
        return host in _OFFICIAL_HOSTS and self.discovered_from.strip().lower() in _AUTO_DISCOVERY


def _value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def load_registry_rows(path: Path = REGISTRY_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def save_registry_rows(rows: list[dict[str, str]], path: Path = REGISTRY_PATH) -> None:
    if not rows:
        return
    fieldnames = list(rows[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def is_row_allowed(row: dict[str, str], *, include_pending: bool = False) -> bool:
    allowed = _value(row, "Allowed_for_AI_Retrieval", "Allowed for AI Retrieval").lower()
    if allowed.startswith("yes") or allowed in {"true", "1"}:
        return True
    status = _value(row, "PM_Review_Status", "Approval Status").lower()
    if status == "approved":
        return True
    host = (urlparse(_value(row, "url", "Source URL")).hostname or "").lower()
    discovered = _value(row, "discovered_from").lower()
    if host in _OFFICIAL_HOSTS and discovered in _AUTO_DISCOVERY:
        return True
    return bool(include_pending and host in _OFFICIAL_HOSTS and status in {"pending_review", "pending"})


@lru_cache(maxsize=1)
def _source_groups() -> list[dict]:
    data = json.loads(SOURCE_GROUP_PATH.read_text(encoding="utf-8-sig"))
    return list(data.get("groups") or [])


_GROUP_KEYWORDS: dict[str, tuple[str, ...]] = {
    "official_admissions": ("admission", "freshman", "applicant"),
    "international_admissions": ("international admission", "international applicant"),
    "graduate_admissions": ("graduate admission", "graduate school"),
    "official_catalog": ("catalog", "course description", "prerequisite"),
    "official_programs": ("program", "degree", "college", "department"),
    "official_calendar": ("academic calendar", "academic schedule", "semester", "final exam"),
    "registration": ("registration", "add/drop", "withdrawal"),
    "official_policies": ("policy", "procedure", "governance"),
    "academic_standing": ("suspension", "probation", "academic standing"),
    "official_forms": ("form", "appeal", "request", ".pdf"),
    "official_directory": ("directory", "faculty", "staff", "contact"),
    "official_employment": ("employment", "jobs", "hiring"),
    "career_center": ("handshake", "career", "internship", "co-op"),
    "financial_aid": ("financial aid", "fafsa", "scholarship", "grant", "loan"),
    "tuition_and_fees": ("tuition", "fees", "cost of attendance"),
    "student_accounts": ("student account", "payment", "pay tuition"),
    "housing": ("housing", "residence", "dorm"),
    "dining": ("dining", "meal plan"),
    "health_services": ("health", "clinic"),
    "counseling": ("counsel", "mental health"),
    "accessibility": ("accessibility", "accommodation", "disability"),
    "international_services": ("international student", "visa", "i-20", "sevis"),
    "technology_support": ("technology", "password", "canvas", "wifi", "information technology"),
    "student_organizations": ("organization", "club", "presence"),
    "campus_events": ("event", "calendar of events"),
    "news_announcements": ("news", "announcement"),
    "athletics": ("athletics", "sports", "football", "basketball", "roster"),
    "maps_and_locations": ("map", "directions", "location", "building"),
    "parking_transportation": ("parking", "transportation"),
    "campus_safety": ("safety", "police", "emergency"),
    "library": ("library", "librarian"),
    "academic_support": ("tutoring", "academic support", "student success"),
    "student_records": ("transcript", "graduation", "diploma", "student record"),
    "bookstore": ("bookstore", "textbook", "merchandise"),
}


def assign_source_groups(row: dict[str, str]) -> list[str]:
    source_id = _value(row, "source_id", "Source ID")
    url = _value(row, "url", "Source URL")
    category = _value(row, "category", "Information Category")
    # Ecosystem discovery assigned one broad eight-topic category to thousands
    # of unrelated pages. It is governance metadata, not routing evidence.
    category_for_match = category if category.count("|") <= 2 else ""
    blob = " ".join((
        _value(row, "source_name", "Source Name"),
        category_for_match,
        _value(row, "notes", "Primary Use Case"),
        url.lower().replace("-", "_"),
    )).lower()
    assigned: list[str] = []
    for group in _source_groups():
        group_id = group["source_group_id"]
        if source_id and source_id in (group.get("source_ids") or []):
            assigned.append(group_id)
            continue
        if url and any(url.rstrip("/").lower().startswith(prefix.rstrip("/").lower()) for prefix in (group.get("url_prefixes") or []) if prefix):
            assigned.append(group_id)
    for group_id, keywords in _GROUP_KEYWORDS.items():
        if any(keyword in blob for keyword in keywords):
            assigned.append(group_id)
    if not assigned:
        host = (urlparse(url).hostname or "").lower()
        if "mcneesesports.com" in host:
            assigned.append("athletics")
        elif "mcneesereslife.com" in host:
            assigned.append("housing")
        elif "sodexomyway.com" in host:
            assigned.append("dining")
        elif "presence.io" in host:
            assigned.append("student_organizations")
        else:
            assigned.append("general_official")
    return list(dict.fromkeys(assigned))


def to_governed_source(row: dict[str, str]) -> GovernedSource:
    url = _value(row, "url", "Source URL")
    return GovernedSource(
        source_id=_value(row, "source_id", "Source ID"),
        title=_value(row, "source_name", "Source Name"),
        url=url,
        domain=_value(row, "domain") or (urlparse(url).hostname or ""),
        content_type=_value(row, "content_type") or ("pdf" if url.lower().split("?")[0].endswith(".pdf") else "html"),
        category=_value(row, "category", "Information Category"),
        parent_source_id=_value(row, "parent_source_id"),
        catalog_year=_value(row, "catalog_year"),
        priority=_value(row, "priority_for_ingest") or "medium",
        review_status=_value(row, "PM_Review_Status", "Approval Status"),
        allowed_for_ai=_value(row, "Allowed_for_AI_Retrieval", "Allowed for AI Retrieval"),
        last_ingested_timestamp=_value(row, "last_ingested_timestamp"),
        content_hash=_value(row, "content_hash"),
        discovered_from=_value(row, "discovered_from"),
        notes=_value(row, "notes", "Primary Use Case"),
        source_group_ids=tuple(assign_source_groups(row)),
    )


def load_governed_registry(
    path: Path = REGISTRY_PATH,
    *,
    include_pending: bool = False,
    allowed_only: bool = True,
) -> list[GovernedSource]:
    rows = load_registry_rows(path)
    if allowed_only:
        rows = [row for row in rows if is_row_allowed(row, include_pending=include_pending)]
    return [to_governed_source(row) for row in rows]


def clear_registry_cache() -> None:
    _source_groups.cache_clear()

