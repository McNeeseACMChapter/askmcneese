"""Canonical Class Planner records independent of McNeese HTML and storage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class TermOption:
    source_term_id: str
    display_name: str


@dataclass(frozen=True)
class MeetingRecord:
    days: tuple[str, ...]
    start_time: str | None
    end_time: str | None
    start_date: str | None
    end_date: str | None
    building_code: str | None
    room: str | None
    is_online: bool
    is_tba: bool
    raw_days: str
    raw_time: str
    raw_dates: str


@dataclass(frozen=True)
class SectionRecord:
    id: str
    term_id: str
    crn: str
    subject: str
    course_number: str
    section_code: str
    title: str
    credits: float
    level: str | None
    capacity: int | None
    enrolled: int | None
    available: int | None
    status: str
    part_of_term: str | None
    instructors: tuple[str, ...]
    attributes: tuple[str, ...]
    meetings: tuple[MeetingRecord, ...]
    source_url: str
    raw_status: str = ""
    normalized_hash: str = field(default="", compare=False)

    @property
    def course_id(self) -> str:
        return f"{self.term_id}:{self.subject}:{self.course_number}"

    def with_hash(self) -> "SectionRecord":
        payload = asdict(self)
        payload.pop("normalized_hash", None)
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return replace(self, normalized_hash=digest)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    valid: tuple[SectionRecord, ...]
    rejected: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class DatasetDiff:
    added: int
    changed: int
    removed: int
    unchanged: int

