"""Portable Class Planner database metadata and strict runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Index, Integer, MetaData, String, Table,
    Text, UniqueConstraint, create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)

datasets = Table(
    "datasets", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_term_id", String(32), nullable=False),
    Column("fetched_at", String(64), nullable=False),
    Column("source_url", Text, nullable=False),
    Column("parser_version", String(80), nullable=False),
    Column("section_count", Integer, nullable=False),
    Column("content_hash", String(64), nullable=False, default=""),
    Column("lifecycle", String(24), nullable=False, default="active"),
    Column("created_at", String(64), nullable=False),
)

terms = Table(
    "terms", metadata,
    Column("source_term_id", String(32), primary_key=True),
    Column("display_name", String(160), nullable=False),
    Column("active_dataset_id", Integer, ForeignKey("datasets.id")),
    Column("last_synced_at", String(64)),
    Column("availability_verified_at", String(64)),
)

subjects = Table(
    "subjects", metadata,
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
    Column("code", String(24), primary_key=True),
    Column("display_name", String(160), nullable=False),
    Column("normalized_name", String(160), nullable=False),
)

courses = Table(
    "courses", metadata,
    Column("id", String(128), primary_key=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
    Column("source_term_id", String(32), nullable=False),
    Column("subject", String(24), nullable=False),
    Column("course_number", String(24), nullable=False),
    Column("title", String(300), nullable=False),
    Column("normalized_code", String(80), nullable=False),
    Column("normalized_title", String(300), nullable=False),
)

sections = Table(
    "sections", metadata,
    Column("id", String(128), primary_key=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", String(128), nullable=False),
    Column("source_term_id", String(32), nullable=False),
    Column("crn", String(16), nullable=False),
    Column("section_code", String(32), nullable=False),
    Column("credits", Float, nullable=False),
    Column("level", String(32)),
    Column("capacity", Integer),
    Column("enrolled", Integer),
    Column("available", Integer),
    Column("status", String(24), nullable=False),
    Column("part_of_term", String(120)),
    Column("source_url", Text, nullable=False),
    Column("raw_status", Text, nullable=False),
    Column("normalized_hash", String(64), nullable=False),
    Column("attributes_json", Text, nullable=False, default="[]"),
)

meetings = Table(
    "meetings", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
    Column("section_id", String(128), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("days_json", Text, nullable=False),
    Column("start_time", String(16)), Column("end_time", String(16)),
    Column("start_date", String(16)), Column("end_date", String(16)),
    Column("building_code", String(80)), Column("room", String(80)),
    Column("is_online", Boolean, nullable=False), Column("is_tba", Boolean, nullable=False),
    Column("raw_days", Text, nullable=False), Column("raw_time", Text, nullable=False),
    Column("raw_dates", Text, nullable=False),
    UniqueConstraint("dataset_id", "section_id", "sequence"),
)

instructors = Table(
    "instructors", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
    Column("source_name", String(240), nullable=False),
    Column("display_name", String(240), nullable=False),
    Column("normalized_name", String(240), nullable=False),
    UniqueConstraint("dataset_id", "source_name"),
)

section_instructors = Table(
    "section_instructors", metadata,
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
    Column("section_id", String(128), primary_key=True),
    Column("instructor_id", Integer, ForeignKey("instructors.id", ondelete="CASCADE"), primary_key=True),
)

section_notes = Table(
    "section_notes", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
    Column("section_id", String(128), nullable=False),
    Column("category", String(32), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("text", Text, nullable=False),
    UniqueConstraint("dataset_id", "section_id", "category", "sequence"),
)

availability_overlays = Table(
    "availability_overlays", metadata,
    Column("source_term_id", String(32), primary_key=True),
    Column("section_id", String(128), primary_key=True),
    Column("capacity", Integer), Column("enrolled", Integer), Column("available", Integer),
    Column("status", String(24), nullable=False),
    Column("verified_at", String(64), nullable=False),
    Column("verification_status", String(32), nullable=False, default="verified"),
    Column("source_url", Text, nullable=False),
)

sync_runs = Table(
    "sync_runs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_term_id", String(32), nullable=False),
    Column("source_url", Text, nullable=False),
    Column("parser_version", String(80), nullable=False),
    Column("started_at", String(64), nullable=False), Column("finished_at", String(64)),
    Column("status", String(32), nullable=False), Column("details_json", Text, nullable=False),
)

sync_subjects = Table(
    "sync_subjects", metadata,
    Column("sync_id", Integer, ForeignKey("sync_runs.id", ondelete="CASCADE"), primary_key=True),
    Column("subject", String(24), primary_key=True),
    Column("started_at", String(64), nullable=False), Column("finished_at", String(64)),
    Column("status", String(32), nullable=False), Column("section_count", Integer, nullable=False, default=0),
    Column("content_hash", String(64), nullable=False, default=""), Column("duration_ms", Integer),
    Column("error", Text),
)

sync_locks = Table(
    "sync_locks", metadata,
    Column("lock_key", String(180), primary_key=True),
    Column("acquired_at", String(64), nullable=False),
    Column("owner_token", String(64), nullable=False),
)

course_activity = Table(
    "course_activity", metadata,
    Column("source_term_id", String(32), primary_key=True),
    Column("course_id", String(128), primary_key=True),
    Column("last_opened_at", String(64), nullable=False),
)

Index("idx_datasets_term_created", datasets.c.source_term_id, datasets.c.created_at)
Index("idx_courses_lookup", courses.c.dataset_id, courses.c.subject, courses.c.course_number)
Index("idx_courses_search", courses.c.dataset_id, courses.c.normalized_code, courses.c.normalized_title)
Index("idx_sections_course", sections.c.dataset_id, sections.c.course_id, sections.c.section_code)
Index("idx_sections_crn", sections.c.dataset_id, sections.c.crn)
Index("idx_sections_status", sections.c.dataset_id, sections.c.status)
Index("idx_meetings_section", meetings.c.dataset_id, meetings.c.section_id)
Index("idx_instructors_name", instructors.c.dataset_id, instructors.c.normalized_name)
Index("idx_notes_section", section_notes.c.dataset_id, section_notes.c.section_id)
Index("idx_activity_recent", course_activity.c.source_term_id, course_activity.c.last_opened_at)


def normalize_database_url(value: str) -> str:
    value = value.strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    return value


def database_url_from_environment() -> str:
    mode = os.getenv("CLASS_DATA_MODE", "staging").strip().lower()
    configured = os.getenv("DATABASE_URL", "").strip()
    if mode == "live":
        if not configured:
            raise RuntimeError("CLASS_DATA_MODE=live requires DATABASE_URL for managed PostgreSQL")
        normalized = normalize_database_url(configured)
        if not normalized.startswith("postgresql+psycopg://"):
            raise RuntimeError("CLASS_DATA_MODE=live requires a PostgreSQL DATABASE_URL")
        return normalized
    if configured:
        return normalize_database_url(configured)
    backend_dir = Path(__file__).resolve().parents[3]
    configured_path = os.getenv("CLASS_PLANNER_DB_PATH", "class_planner_v2.sqlite3")
    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = backend_dir / path
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def make_engine(url: str, *, initialize_local: bool = True) -> Engine:
    normalized = normalize_database_url(url)
    kwargs: dict[str, object] = {"pool_pre_ping": True, "future": True}
    if normalized.startswith("sqlite:"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        kwargs["poolclass"] = NullPool
    engine = create_engine(normalized, **kwargs)
    if initialize_local and engine.dialect.name == "sqlite":
        metadata.create_all(engine)
    return engine
