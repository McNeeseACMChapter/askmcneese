"""SQLite last-known-good store with transactional dataset publication."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import sqlite3
from typing import Iterable
from uuid import uuid4

from .models import SectionRecord, TermOption


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_term_id TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    section_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS terms (
    source_term_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    active_dataset_id INTEGER REFERENCES datasets(id),
    last_synced_at TEXT
);
CREATE TABLE IF NOT EXISTS courses (
    id TEXT NOT NULL,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    source_term_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    course_number TEXT NOT NULL,
    title TEXT NOT NULL,
    PRIMARY KEY (dataset_id, id)
);
CREATE TABLE IF NOT EXISTS sections (
    id TEXT NOT NULL,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    course_id TEXT NOT NULL,
    source_term_id TEXT NOT NULL,
    crn TEXT NOT NULL,
    section_code TEXT NOT NULL,
    credits REAL NOT NULL,
    level TEXT,
    capacity INTEGER,
    enrolled INTEGER,
    available INTEGER,
    status TEXT NOT NULL,
    part_of_term TEXT,
    source_url TEXT NOT NULL,
    raw_status TEXT NOT NULL,
    normalized_hash TEXT NOT NULL,
    attributes_json TEXT NOT NULL,
    PRIMARY KEY (dataset_id, id)
);
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    days_json TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    start_date TEXT,
    end_date TEXT,
    building_code TEXT,
    room TEXT,
    is_online INTEGER NOT NULL,
    is_tba INTEGER NOT NULL,
    raw_days TEXT NOT NULL,
    raw_time TEXT NOT NULL,
    raw_dates TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS instructors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    UNIQUE(dataset_id, source_name)
);
CREATE TABLE IF NOT EXISTS section_instructors (
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES instructors(id) ON DELETE CASCADE,
    PRIMARY KEY(dataset_id, section_id, instructor_id)
);
CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_term_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_locks (
    source_term_id TEXT PRIMARY KEY,
    acquired_at TEXT NOT NULL,
    owner_token TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_courses_lookup ON courses(dataset_id, subject, course_number);
CREATE INDEX IF NOT EXISTS idx_courses_title ON courses(dataset_id, title);
CREATE INDEX IF NOT EXISTS idx_sections_crn ON sections(dataset_id, crn);
CREATE INDEX IF NOT EXISTS idx_sections_status ON sections(dataset_id, status);
CREATE INDEX IF NOT EXISTS idx_meetings_section ON meetings(dataset_id, section_id);
CREATE INDEX IF NOT EXISTS idx_instructors_name ON instructors(dataset_id, display_name);
"""


class ClassPlannerStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.executescript(SCHEMA)
            self._ensure_sync_lock_schema(connection)

    @classmethod
    def from_environment(cls) -> "ClassPlannerStore":
        default = Path(__file__).resolve().parents[3] / "class_planner.sqlite3"
        return cls(os.getenv("CLASS_PLANNER_DB_PATH", str(default)))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _ensure_sync_lock_schema(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(sync_locks)").fetchall()
        }
        if "owner_token" not in columns:
            connection.execute(
                "ALTER TABLE sync_locks ADD COLUMN owner_token TEXT NOT NULL DEFAULT ''"
            )

    def acquire_sync_lock(self, term_id: str) -> str | None:
        cutoff = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        now = datetime.now(UTC).isoformat()
        token = uuid4().hex
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM sync_locks WHERE acquired_at < ?", (cutoff,))
            try:
                connection.execute(
                    "INSERT INTO sync_locks(source_term_id, acquired_at, owner_token) VALUES (?, ?, ?)",
                    (term_id, now, token),
                )
            except sqlite3.IntegrityError:
                connection.rollback()
                return None
            connection.commit()
            return token

    def release_sync_lock(self, term_id: str, owner_token: str | None = None) -> None:
        with closing(self._connect()) as connection, connection:
            if owner_token is None:
                connection.execute("DELETE FROM sync_locks WHERE source_term_id = ?", (term_id,))
                return
            connection.execute(
                "DELETE FROM sync_locks WHERE source_term_id = ? AND owner_token = ?",
                (term_id, owner_token),
            )

    def start_sync(self, term_id: str, source_url: str, parser_version: str) -> int:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """
                INSERT INTO sync_runs(
                    source_term_id, source_url, parser_version, started_at, status, details_json
                ) VALUES (?, ?, ?, ?, 'running', '{}')
                """,
                (term_id, source_url, parser_version, datetime.now(UTC).isoformat()),
            )
            return int(cursor.lastrowid)

    def finish_sync(self, sync_id: int, status: str, details: dict[str, object]) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE sync_runs
                SET status = ?, finished_at = ?, details_json = ?
                WHERE id = ?
                """,
                (status, datetime.now(UTC).isoformat(), json.dumps(details, sort_keys=True), sync_id),
            )

    def active_hashes(self, term_id: str) -> dict[str, str]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT s.id, s.normalized_hash
                FROM sections s
                JOIN terms t ON t.active_dataset_id = s.dataset_id
                WHERE t.source_term_id = ?
                """,
                (term_id,),
            ).fetchall()
        return {str(row["id"]): str(row["normalized_hash"]) for row in rows}

    def publish(
        self,
        *,
        term: TermOption,
        records: Iterable[SectionRecord],
        fetched_at: str,
        source_url: str,
        parser_version: str,
    ) -> int:
        staged = tuple(records)
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO datasets(
                        source_term_id, fetched_at, source_url, parser_version, section_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        term.source_term_id,
                        fetched_at,
                        source_url,
                        parser_version,
                        len(staged),
                        datetime.now(UTC).isoformat(),
                    ),
                )
                dataset_id = int(cursor.lastrowid)
                courses: dict[str, SectionRecord] = {}
                for record in staged:
                    courses.setdefault(record.course_id, record)
                connection.executemany(
                    """
                    INSERT INTO courses(
                        id, dataset_id, source_term_id, subject, course_number, title
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            course_id,
                            dataset_id,
                            record.term_id,
                            record.subject,
                            record.course_number,
                            record.title,
                        )
                        for course_id, record in courses.items()
                    ],
                )
                for record in staged:
                    connection.execute(
                        """
                        INSERT INTO sections(
                            id, dataset_id, course_id, source_term_id, crn, section_code,
                            credits, level, capacity, enrolled, available, status, part_of_term,
                            source_url, raw_status, normalized_hash, attributes_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.id,
                            dataset_id,
                            record.course_id,
                            record.term_id,
                            record.crn,
                            record.section_code,
                            record.credits,
                            record.level,
                            record.capacity,
                            record.enrolled,
                            record.available,
                            record.status,
                            record.part_of_term,
                            record.source_url,
                            record.raw_status,
                            record.normalized_hash,
                            json.dumps(record.attributes),
                        ),
                    )
                    for sequence, meeting in enumerate(record.meetings):
                        connection.execute(
                            """
                            INSERT INTO meetings(
                                dataset_id, section_id, sequence, days_json, start_time, end_time,
                                start_date, end_date, building_code, room, is_online, is_tba,
                                raw_days, raw_time, raw_dates
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                dataset_id,
                                record.id,
                                sequence,
                                json.dumps(meeting.days),
                                meeting.start_time,
                                meeting.end_time,
                                meeting.start_date,
                                meeting.end_date,
                                meeting.building_code,
                                meeting.room,
                                int(meeting.is_online),
                                int(meeting.is_tba),
                                meeting.raw_days,
                                meeting.raw_time,
                                meeting.raw_dates,
                            ),
                        )
                    for instructor in record.instructors:
                        connection.execute(
                            """
                            INSERT INTO instructors(dataset_id, source_name, display_name)
                            VALUES (?, ?, ?)
                            ON CONFLICT(dataset_id, source_name) DO NOTHING
                            """,
                            (dataset_id, instructor, instructor),
                        )
                        instructor_id = connection.execute(
                            "SELECT id FROM instructors WHERE dataset_id = ? AND source_name = ?",
                            (dataset_id, instructor),
                        ).fetchone()["id"]
                        connection.execute(
                            """
                            INSERT INTO section_instructors(dataset_id, section_id, instructor_id)
                            VALUES (?, ?, ?)
                            """,
                            (dataset_id, record.id, instructor_id),
                        )
                connection.execute(
                    """
                    INSERT INTO terms(source_term_id, display_name, active_dataset_id, last_synced_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_term_id) DO UPDATE SET
                        display_name = excluded.display_name,
                        active_dataset_id = excluded.active_dataset_id,
                        last_synced_at = excluded.last_synced_at
                    """,
                    (term.source_term_id, term.display_name, dataset_id, fetched_at),
                )
                connection.commit()
                return dataset_id
            except Exception:
                connection.rollback()
                raise

    def list_terms(self) -> list[dict[str, object]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT t.source_term_id, t.display_name, t.last_synced_at,
                       d.section_count, d.source_url, d.fetched_at
                FROM terms t
                JOIN datasets d ON d.id = t.active_dataset_id
                ORDER BY t.source_term_id DESC
                """
            ).fetchall()
        return [
            {
                "id": row["source_term_id"],
                "label": row["display_name"],
                "sectionCount": row["section_count"],
                "fetchedAt": row["fetched_at"],
                "sourceUrl": row["source_url"],
            }
            for row in rows
        ]

    def search_courses(
        self,
        term_id: str,
        *,
        query: str = "",
        open_only: bool = False,
        online_only: bool = False,
        days: tuple[str, ...] = (),
        time_of_day: str = "any",
    ) -> list[dict[str, object]]:
        sections = self._load_sections(term_id)
        needle = query.strip().lower()
        filtered = []
        for section in sections:
            searchable = " ".join(
                [
                    section["subject"],
                    section["courseNumber"],
                    section["title"],
                    " ".join(section["instructors"]),
                ]
            ).lower()
            meeting_days = {day for meeting in section["meetings"] for day in meeting["days"]}
            if needle and needle not in searchable:
                continue
            if open_only and section["status"] != "open":
                continue
            if online_only and section["modality"] not in {"Online", "Hybrid"}:
                continue
            if days and not set(days).issubset(meeting_days):
                continue
            starts = [
                int(meeting["startTime"][:2]) * 60 + int(meeting["startTime"][3:])
                for meeting in section["meetings"]
                if meeting["startTime"]
            ]
            if time_of_day == "morning" and not any(start < 720 for start in starts):
                continue
            if time_of_day == "afternoon" and not any(720 <= start < 1020 for start in starts):
                continue
            if time_of_day == "evening" and not any(start >= 1020 for start in starts):
                continue
            filtered.append(section)
        grouped: dict[str, dict[str, object]] = {}
        for section in filtered:
            course = grouped.setdefault(
                section["courseId"],
                {
                    "id": section["courseId"],
                    "subject": section["subject"],
                    "courseNumber": section["courseNumber"],
                    "title": section["title"],
                    "credits": section["credits"],
                    "sections": [],
                },
            )
            course["sections"].append(_public_section(section))
        return sorted(grouped.values(), key=lambda item: (item["subject"], item["courseNumber"]))

    def get_course(self, term_id: str, course_id: str) -> dict[str, object] | None:
        return next(
            (course for course in self.search_courses(term_id) if course["id"] == course_id),
            None,
        )

    def get_section(self, section_id: str) -> dict[str, object] | None:
        term_id = section_id.split(":", 1)[0]
        section = next(
            (item for item in self._load_sections(term_id) if item["id"] == section_id),
            None,
        )
        return _public_section(section) if section else None

    def freshness(self, term_id: str) -> dict[str, object] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT d.fetched_at, d.source_url, d.section_count, d.parser_version
                FROM terms t JOIN datasets d ON d.id = t.active_dataset_id
                WHERE t.source_term_id = ?
                """,
                (term_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "name": "McNeese Class Search",
            "url": row["source_url"],
            "fetchedAt": row["fetched_at"],
            "sectionCount": row["section_count"],
            "parserVersion": row["parser_version"],
            "mode": os.getenv("CLASS_DATA_MODE", "staging"),
        }

    def _load_sections(self, term_id: str) -> list[dict[str, object]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT s.*, c.subject, c.course_number, c.title, d.fetched_at
                FROM sections s
                JOIN terms t ON t.active_dataset_id = s.dataset_id
                JOIN datasets d ON d.id = s.dataset_id
                JOIN courses c ON c.dataset_id = s.dataset_id AND c.id = s.course_id
                WHERE t.source_term_id = ?
                ORDER BY c.subject, c.course_number, s.section_code
                """,
                (term_id,),
            ).fetchall()
            result = []
            for row in rows:
                meetings = connection.execute(
                    """
                    SELECT * FROM meetings
                    WHERE dataset_id = ? AND section_id = ?
                    ORDER BY sequence
                    """,
                    (row["dataset_id"], row["id"]),
                ).fetchall()
                instructors = connection.execute(
                    """
                    SELECT i.display_name
                    FROM instructors i
                    JOIN section_instructors si ON si.instructor_id = i.id
                    WHERE si.dataset_id = ? AND si.section_id = ?
                    ORDER BY i.display_name
                    """,
                    (row["dataset_id"], row["id"]),
                ).fetchall()
                meeting_data = [
                    {
                        "type": "Online" if meeting["is_online"] else "Class",
                        "days": json.loads(meeting["days_json"]),
                        "startTime": meeting["start_time"],
                        "endTime": meeting["end_time"],
                        "startDate": meeting["start_date"],
                        "endDate": meeting["end_date"],
                        "building": meeting["building_code"],
                        "room": meeting["room"],
                        "isOnline": bool(meeting["is_online"]),
                        "isTba": bool(meeting["is_tba"]),
                    }
                    for meeting in meetings
                ]
                is_online = [meeting["isOnline"] for meeting in meeting_data]
                result.append(
                    {
                        "id": row["id"],
                        "courseId": row["course_id"],
                        "termId": row["source_term_id"],
                        "crn": row["crn"],
                        "sectionNumber": row["section_code"],
                        "subject": row["subject"],
                        "courseNumber": row["course_number"],
                        "title": row["title"],
                        "credits": row["credits"],
                        "level": row["level"],
                        "capacity": row["capacity"],
                        "enrolled": row["enrolled"],
                        "available": row["available"],
                        "seatsRemaining": row["available"],
                        "status": row["status"],
                        "partOfTerm": row["part_of_term"],
                        "instructors": [item["display_name"] for item in instructors],
                        "instructor": ", ".join(item["display_name"] for item in instructors) or None,
                        "meetings": meeting_data,
                        "modality": "Online" if is_online and all(is_online) else "Hybrid" if any(is_online) else "In person",
                        "updatedAt": row["fetched_at"],
                        "sourceUrl": row["source_url"],
                    }
                )
        return result


def _public_section(section: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in section.items()
        if key != "instructors"
    }

