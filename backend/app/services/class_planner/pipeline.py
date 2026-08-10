"""McNeese Class Search transport, parser, validation, and synchronization."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import hashlib
import logging
import os
import re
import time
from typing import Iterable

from bs4 import BeautifulSoup, Tag
import httpx

from .models import (
    DatasetDiff,
    MeetingRecord,
    SectionRecord,
    SubjectOption,
    TermOption,
    ValidationReport,
)
from .store import ClassPlannerStore

LOGGER = logging.getLogger(__name__)
SOURCE_BASE_URL = "https://schedule.mcneese.edu/"
PARSER_VERSION = "mcneese-html-v1"
VALID_DAYS = frozenset("MTWRFSU")
CRN_PATTERN = re.compile(r"^\d{5}$")
TIME_PATTERN = re.compile(
    r"(?P<start>\d{1,2}:\d{2})\s*(?P<start_ampm>AM|PM)\s*-\s*"
    r"(?P<end>\d{1,2}:\d{2})\s*(?P<end_ampm>AM|PM)",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(
    r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*(?P<end>\d{2}/\d{2}/\d{4})"
)


class SourceContractError(RuntimeError):
    """The upstream page no longer matches the verified public contract."""


class ValidationFailure(RuntimeError):
    """A staged dataset is unsafe to publish."""


class SyncInProgress(RuntimeError):
    """Another process already owns the term synchronization lock."""


class McNeeseClassSearchAdapter:
    """Fixed-boundary public HTTP adapter; it never accepts arbitrary URLs."""

    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        max_attempts: int = 3,
        client: httpx.Client | None = None,
    ) -> None:
        timeout = timeout_seconds or float(os.getenv("CLASS_SOURCE_TIMEOUT_SECONDS", "180"))
        self._client = client or httpx.Client(
            base_url=SOURCE_BASE_URL,
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": os.getenv(
                    "CLASS_SOURCE_USER_AGENT",
                    "AskMcNeese-ClassPlanner/1.0 (+https://www.mcneese.edu/)",
                )
            },
        )
        self._owns_client = client is None
        self._max_attempts = max(1, max_attempts)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def fetch_terms_html(self) -> str:
        return self._request("GET", "/")

    def fetch_terms(self) -> list[TermOption]:
        return parse_terms(self.fetch_terms_html())

    def fetch_term_search_form(self, source_term_id: str) -> str:
        return self._request("POST", "/index.php", data={"term_code": source_term_id})

    def fetch_sections_html(
        self,
        source_term_id: str,
        *,
        subject: str = "",
        course_number: str = "",
        only_web: bool = False,
    ) -> str:
        # Values below are copied from the verified Fall 2026 form. Unchecked
        # checkboxes are intentionally omitted, matching browser form behavior.
        data = {
            "term_code": source_term_id,
            "fps": "0",
            "subject": subject,
            "course_number": course_number,
            "title": "",
            "schedule_type": "",
            "credit_hours1": "",
            "credit_hours2": "",
            "course_level": "",
            "part_of_term": "",
            "instructor": "",
            "start_hour": "00",
            "start_minute": "00",
            "start_ampm": "am",
            "end_hour": "00",
            "end_minute": "00",
            "end_ampm": "am",
        }
        if only_web:
            data["only_web"] = "on"
        return self._request("POST", "/index.php", data=data)

    def _request(self, method: str, path: str, **kwargs: object) -> str:
        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            try:
                response = self._client.request(method, path, **kwargs)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"upstream returned {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                if "text/html" not in response.headers.get("content-type", "").lower():
                    raise SourceContractError("McNeese Class Search returned non-HTML content")
                return response.text
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt + 1 < self._max_attempts:
                    time.sleep(2**attempt)
        raise SourceContractError(f"McNeese Class Search request failed: {last_error}") from last_error


def parse_terms(html: str) -> list[TermOption]:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.select_one('form[action="index.php"] select[name="term_code"]')
    if select is None:
        raise SourceContractError("term selector is missing")
    terms = [
        TermOption(str(option.get("value")), _clean(option.get_text(" ", strip=True)))
        for option in select.find_all("option")
        if option.get("value")
    ]
    if not terms:
        raise SourceContractError("term selector contains no selectable terms")
    return terms


def parse_subject_options(html: str) -> list[SubjectOption]:
    """Extract subject codes and source-owned names from the verified term form."""
    soup = BeautifulSoup(html, "html.parser")
    select = soup.select_one('form[action="index.php"] select[name="subject"]')
    if select is None:
        raise SourceContractError("subject selector is missing")
    subjects = [
        SubjectOption(
            code=str(option.get("value")).upper(),
            display_name=_subject_display_name(option),
        )
        for option in select.find_all("option")
        if option.get("value")
    ]
    if not subjects:
        raise SourceContractError("subject selector contains no selectable subjects")
    return subjects


def parse_subjects(html: str) -> list[str]:
    return [subject.code for subject in parse_subject_options(html)]


def parse_sections(html: str, source_term_id: str, *, allow_empty: bool = False) -> list[SectionRecord]:
    soup = BeautifulSoup(html, "html.parser")
    table = _find_results_table(soup, allow_missing=allow_empty)
    if table is None:
        return []
    rows = table.find_all("tr", recursive=False)
    sections: list[SectionRecord] = []
    for index, row in enumerate(rows):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 9:
            continue
        crn = _clean(cells[1].get_text(" ", strip=True))
        if not CRN_PATTERN.fullmatch(crn):
            continue
        if index + 1 >= len(rows):
            raise SourceContractError(f"section {crn} is missing its detail row")
        detail_cells = rows[index + 1].find_all("td", recursive=False)
        if len(detail_cells) < 6:
            raise SourceContractError(f"section {crn} has an incomplete detail row")
        sections.append(_parse_section(cells, detail_cells, source_term_id))
    if not sections and not allow_empty:
        raise SourceContractError("result table contains no recognizable section rows")
    return sections


def _find_results_table(soup: BeautifulSoup, *, allow_missing: bool = False) -> Tag | None:
    required = {"CRN", "Course", "Capacity", "Enrolled", "Available", "Meeting Time"}
    candidates: list[Tag] = []
    for table in soup.find_all("table"):
        direct_rows = table.find_all("tr", recursive=False)
        if len(direct_rows) < 3:
            continue
        header_text = {_clean(cell.get_text(" ", strip=True)) for row in direct_rows[:2] for cell in row.find_all("td", recursive=False)}
        if required.issubset(header_text):
            candidates.append(table)
    if not candidates:
        if allow_missing:
            return None
        raise SourceContractError("expected class result columns are missing")
    return min(candidates, key=lambda table: len(str(table)))


def _parse_section(cells: list[Tag], detail_cells: list[Tag], term_id: str) -> SectionRecord:
    crn = _clean(cells[1].get_text(" ", strip=True))
    course_parts = _clean(cells[2].get_text(" ", strip=True)).split()
    if len(course_parts) < 3:
        raise SourceContractError(f"section {crn} has malformed course identity")
    subject, course_number = course_parts[0].upper(), course_parts[1].upper()
    section_code = " ".join(course_parts[2:])
    capacity = _optional_int(cells[6])
    enrolled = _optional_int(cells[7])
    available = _optional_int(cells[8])
    raw_status = _clean(cells[0].get_text(" ", strip=True))
    locations = _parse_locations(detail_cells[2])
    instructors, registration_notes, corequisites, restrictions = _parse_instructors_and_notes(
        detail_cells[3]
    )
    attributes = tuple(_unique(_attribute_values(detail_cells[4])))
    meetings = _parse_meetings(detail_cells[5], locations)
    if not meetings:
        building, room = locations[0] if locations else (None, None)
        raw_location = " ".join(value for value in (building, room) if value)
        meetings = (
            MeetingRecord(
                days=(),
                start_time=None,
                end_time=None,
                start_date=None,
                end_date=None,
                building_code=building,
                room=room,
                is_online=_is_online_location(raw_location),
                is_tba=True,
                raw_days="",
                raw_time="",
                raw_dates="",
            ),
        )
    record = SectionRecord(
        id=f"{term_id}:{crn}",
        term_id=term_id,
        crn=crn,
        subject=subject,
        course_number=course_number,
        section_code=section_code,
        title=_clean(cells[3].get_text(" ", strip=True)),
        credits=float(_clean(cells[4].get_text(" ", strip=True))),
        level=_clean(cells[5].get_text(" ", strip=True)) or None,
        capacity=capacity,
        enrolled=enrolled,
        available=available,
        status="open" if available is not None and available > 0 else "closed",
        part_of_term=_clean(detail_cells[1].get_text(" ", strip=True)) or None,
        instructors=instructors,
        registration_notes=registration_notes,
        corequisites=corequisites,
        restrictions=restrictions,
        attributes=attributes,
        meetings=meetings,
        source_url=f"{SOURCE_BASE_URL}?scr=crse1&term={term_id}&crn={crn}",
        raw_status=raw_status,
    )
    return record.with_hash()


def _parse_meetings(cell: Tag, locations: list[tuple[str | None, str | None]]) -> tuple[MeetingRecord, ...]:
    table = cell.find("table")
    if table is None:
        return ()
    meetings: list[MeetingRecord] = []
    for index, row in enumerate(table.find_all("tr", recursive=False)):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        raw_days = _clean(cells[0].get_text(" ", strip=True)).upper()
        raw_time = _clean(cells[1].get_text(" ", strip=True)).upper()
        raw_dates = _clean(cells[2].get_text(" ", strip=True))
        if not raw_days and not raw_time and not raw_dates:
            continue
        days = tuple(character for character in raw_days if character in VALID_DAYS)
        time_match = TIME_PATTERN.search(raw_time)
        date_match = DATE_PATTERN.search(raw_dates)
        building, room = locations[index] if index < len(locations) else (locations[0] if locations else (None, None))
        meetings.append(
            MeetingRecord(
                days=days,
                start_time=_to_24_hour(time_match.group("start"), time_match.group("start_ampm")) if time_match else None,
                end_time=_to_24_hour(time_match.group("end"), time_match.group("end_ampm")) if time_match else None,
                start_date=_to_iso_date(date_match.group("start")) if date_match else None,
                end_date=_to_iso_date(date_match.group("end")) if date_match else None,
                building_code=building,
                room=room,
                is_online=_is_online_location(" ".join(value for value in (building, room) if value)),
                is_tba=time_match is None,
                raw_days=raw_days,
                raw_time=raw_time,
                raw_dates=raw_dates,
            )
        )
    return tuple(meetings)


def validate_sections(records: Iterable[SectionRecord]) -> ValidationReport:
    valid: list[SectionRecord] = []
    rejected: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in records:
        reason: str | None = None
        if record.id in seen_ids:
            reason = "duplicate section identifier"
        elif not CRN_PATTERN.fullmatch(record.crn):
            reason = "CRN does not match verified five-digit source format"
        elif not record.subject or not record.course_number or not record.title:
            reason = "required course identity is missing"
        elif any(value is not None and value < 0 for value in (record.capacity, record.enrolled)):
            # Available may be negative/blank in Banner for over-enrolled FULL sections.
            # Capacity and enrolled must remain non-negative when published.
            reason = "negative enrollment value"
        else:
            for meeting in record.meetings:
                if any(day not in VALID_DAYS for day in meeting.days):
                    reason = "invalid meeting day"
                    break
                if bool(meeting.start_time) != bool(meeting.end_time):
                    reason = "partial fixed meeting time"
                    break
                if meeting.start_time and meeting.end_time and meeting.start_time >= meeting.end_time:
                    reason = "meeting start is not before end"
                    break
        if reason:
            rejected.append({"id": record.id, "reason": reason})
        else:
            seen_ids.add(record.id)
            valid.append(record)
    return ValidationReport(tuple(valid), tuple(rejected))


def compare_datasets(previous: dict[str, str], records: Iterable[SectionRecord]) -> DatasetDiff:
    current = {record.id: record.normalized_hash for record in records}
    return DatasetDiff(
        added=len(current.keys() - previous.keys()),
        changed=sum(previous[key] != value for key, value in current.items() if key in previous),
        removed=len(previous.keys() - current.keys()),
        unchanged=sum(previous[key] == value for key, value in current.items() if key in previous),
    )


def enforce_anomaly_rules(
    records: tuple[SectionRecord, ...],
    report: ValidationReport,
    previous: dict[str, str],
    diff: DatasetDiff,
) -> None:
    minimum = int(os.getenv("CLASS_SYNC_MIN_SECTIONS", "100"))
    if len(records) < minimum:
        raise ValidationFailure(f"parsed section count {len(records)} is below safety floor {minimum}")
    total = len(records) + len(report.rejected)
    if total and len(report.rejected) / total > 0.05:
        raise ValidationFailure("more than 5% of parsed records failed validation")
    if previous and len(records) < len(previous) * 0.5:
        raise ValidationFailure("section count collapsed by more than 50%")
    if previous and diff.removed > len(previous) * 0.5:
        raise ValidationFailure("destructive section delta exceeds 50%")
    instructor_missing = sum(not record.instructors for record in records)
    meeting_missing = sum(not record.meetings for record in records)
    if instructor_missing / len(records) > 0.8:
        raise ValidationFailure("more than 80% of sections have no instructor")
    if meeting_missing / len(records) > 0.8:
        raise ValidationFailure("more than 80% of sections have no meeting representation")


def sync_mcneese_term(
    source_term_id: str,
    *,
    store: ClassPlannerStore | None = None,
    adapter: McNeeseClassSearchAdapter | None = None,
) -> dict[str, object]:
    store = store or ClassPlannerStore.from_environment()
    owns_adapter = adapter is None
    adapter = adapter or McNeeseClassSearchAdapter()
    lock_token = store.acquire_sync_lock(source_term_id)
    if not lock_token:
        raise SyncInProgress(f"sync already running for term {source_term_id}")
    sync_id = store.start_sync(source_term_id, SOURCE_BASE_URL, PARSER_VERSION)
    started = time.monotonic()
    try:
        terms = adapter.fetch_terms()
        term = next((item for item in terms if item.source_term_id == source_term_id), None)
        if term is None:
            raise SourceContractError(f"term {source_term_id} is not published by McNeese")
        # Unfiltered full-term POSTs hang/time out on McNeese's public Class Search.
        # The verified strategy is subject-by-subject POST using the published select list.
        search_form = adapter.fetch_term_search_form(source_term_id)
        subject_options = parse_subject_options(search_form)
        subject_codes = [item.code for item in subject_options]
        parsed: list[SectionRecord] = []
        subject_counts: dict[str, int] = {}
        polite_delay = max(0.0, float(os.getenv("CLASS_SOURCE_SUBJECT_DELAY_SECONDS", "1.0")))
        max_workers = max(1, min(8, int(os.getenv("CLASS_SYNC_MAX_CONCURRENCY", "4"))))

        def fetch_subject(subject: str) -> tuple[str, list[SectionRecord], str, float]:
            subject_started_at = datetime.now(UTC).isoformat()
            subject_started = time.monotonic()
            html = adapter.fetch_sections_html(source_term_id, subject=subject)
            records = parse_sections(html, source_term_id, allow_empty=True)
            return subject, records, subject_started_at, time.monotonic() - subject_started

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="class-sync") as pool:
            futures = {}
            for index, subject in enumerate(subject_codes):
                futures[pool.submit(fetch_subject, subject)] = (
                    subject, datetime.now(UTC).isoformat(), time.monotonic()
                )
                if polite_delay and index + 1 < len(subject_codes):
                    time.sleep(polite_delay)
            for future in as_completed(futures):
                queued_subject, queued_at, queued_clock = futures[future]
                try:
                    subject, subject_records, started_at, duration = future.result()
                except Exception as exc:
                    store.record_subject_sync(
                        sync_id, queued_subject, started_at=queued_at, status="failed",
                        section_count=0,
                        duration_ms=round((time.monotonic() - queued_clock) * 1000),
                        error=str(exc),
                    )
                    raise
                subject_hash = hashlib.sha256(
                    "".join(sorted(item.normalized_hash for item in subject_records)).encode()
                ).hexdigest()
                store.record_subject_sync(
                    sync_id, subject, started_at=started_at, status="success",
                    section_count=len(subject_records), duration_ms=round(duration * 1000),
                    content_hash=subject_hash,
                )
                subject_counts[subject] = len(subject_records)
                parsed.extend(subject_records)
                LOGGER.info("class planner subject %s -> %s sections in %.2fs", subject, len(subject_records), duration)
        # Deduplicate by section id while preserving first-seen order.
        unique: dict[str, SectionRecord] = {}
        for record in parsed:
            unique.setdefault(record.id, record)
        parsed = list(unique.values())
        report = validate_sections(parsed)
        previous = store.active_hashes(source_term_id)
        diff = compare_datasets(previous, report.valid)
        enforce_anomaly_rules(report.valid, report, previous, diff)
        fetched_at = datetime.now(UTC).isoformat()
        unchanged = bool(previous) and not (diff.added or diff.changed or diff.removed)
        if unchanged:
            # Keep the immutable dataset stable while advancing independently verified
            # metadata and availability clocks.
            store.update_availability(report.valid, fetched_at)
            store.mark_metadata_verified(source_term_id, fetched_at)
            dataset_id = store.active_dataset_id(source_term_id)
        else:
            dataset_id = store.publish(
                term=term,
                records=report.valid,
                fetched_at=fetched_at,
                source_url=SOURCE_BASE_URL,
                parser_version=PARSER_VERSION,
                subject_options=subject_options,
            )
        result = {
            "syncId": sync_id,
            "datasetId": dataset_id,
            "published": not unchanged,
            "term": source_term_id,
            "subjectsFetched": len(subject_codes),
            "subjectCounts": subject_counts,
            "recordsReceived": len(parsed),
            "recordsValid": len(report.valid),
            "recordsRejected": len(report.rejected),
            "added": diff.added,
            "changed": diff.changed,
            "removed": diff.removed,
            "unchanged": diff.unchanged,
            "fetchedAt": fetched_at,
            "durationSeconds": round(time.monotonic() - started, 3),
        }
        store.finish_sync(sync_id, "success", result)
        LOGGER.info("class planner sync success: %s", result)
        return result
    except Exception as exc:
        store.finish_sync(sync_id, "failed", {"error": str(exc)})
        LOGGER.exception("class planner sync failed for term %s", source_term_id)
        raise
    finally:
        store.release_sync_lock(source_term_id, lock_token)
        if owns_adapter:
            adapter.close()


def _clean(value: str) -> str:
    return " ".join(value.replace("\ufffd", " ").replace("\xa0", " ").split())


def _optional_int(cell: Tag) -> int | None:
    value = _clean(cell.get_text(" ", strip=True))
    return int(value) if value.isdigit() else None


def _element_values(cell: Tag) -> list[str]:
    links = [_clean(item.get_text(" ", strip=True)) for item in cell.find_all("a")]
    values = [value for value in links if value]
    if values:
        return values
    text = _clean(cell.get_text(" ", strip=True))
    return [text] if text and text.upper() not in {"TBA", "STAFF"} else []


def _subject_display_name(option: Tag) -> str:
    code = str(option.get("value", "")).upper()
    label = _clean(option.get_text(" ", strip=True))
    label = re.sub(rf"^{re.escape(code)}\s*[-:\u2013\u2014]?\s*", "", label, flags=re.IGNORECASE)
    return label or code


def _parse_instructors_and_notes(
    cell: Tag,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Separate people from Banner registration prose in the shared source cell."""
    linked = [
        _clean(link.get_text(" ", strip=True))
        for link in cell.find_all("a")
        if "scr=inst" in str(link.get("href", "")) or not link.get("href")
    ]
    lines = [
        _clean(line)
        for line in cell.get_text("\n", strip=True).splitlines()
        if _clean(line)
    ]
    instructors = _unique(linked)
    remaining = list(lines)
    for instructor in instructors:
        cleaned: list[str] = []
        for line in remaining:
            if line.casefold() == instructor.casefold():
                continue
            if line.casefold().startswith(instructor.casefold()):
                line = _clean(line[len(instructor):])
            if line:
                cleaned.append(line)
        remaining = cleaned
    if not instructors and remaining and remaining[0].upper() in {"STAFF", "TBA", "TO BE ANNOUNCED"}:
        instructors = [remaining.pop(0)]

    notes = _unique(remaining)
    corequisites = [note for note in notes if re.search(r"\b(COREQ|COREQUISITE|ALSO ENROLL)\b", note, re.I)]
    restrictions = [note for note in notes if re.search(r"\b(ONLY|MAJOR|PERMISSION|RESTRICT)\b", note, re.I)]
    return (
        tuple(instructors),
        tuple(notes),
        tuple(_unique(corequisites)),
        tuple(_unique(restrictions)),
    )


def _attribute_values(cell: Tag) -> list[str]:
    values = [_clean(image.get("alt", "")) for image in cell.find_all("img")]
    text = _clean(cell.get_text(" ", strip=True))
    if text:
        values.append(text)
    return [value for value in values if value]


def _parse_locations(cell: Tag) -> list[tuple[str | None, str | None]]:
    links = [_clean(link.get_text(" ", strip=True)) for link in cell.find_all("a")]
    values = [value for value in links if value]
    if not values:
        raw = _clean(cell.get_text(" ", strip=True))
        values = raw.split() if raw else []
    locations: list[tuple[str | None, str | None]] = []
    for index in range(0, len(values), 2):
        locations.append((values[index] or None, values[index + 1] if index + 1 < len(values) else None))
    return locations


def _is_online_location(value: str) -> bool:
    upper = value.upper()
    return any(token in upper for token in ("WEB", "ONLINE", "INTERNET"))


def _to_24_hour(value: str, ampm: str) -> str:
    hours, minutes = (int(part) for part in value.split(":"))
    if ampm.upper() == "AM":
        hours = 0 if hours == 12 else hours
    else:
        hours = hours if hours == 12 else hours + 12
    return f"{hours:02d}:{minutes:02d}"


def _to_iso_date(value: str) -> str:
    return datetime.strptime(value, "%m/%d/%Y").date().isoformat()


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize validated McNeese Class Search data")
    parser.add_argument("--term", required=True, help="Verified source term ID, e.g. 202660")
    args = parser.parse_args()
    print(sync_mcneese_term(args.term))


if __name__ == "__main__":
    main()
