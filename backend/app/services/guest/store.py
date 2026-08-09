"""SQLite-backed anonymous guest sessions and tour progress."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Any

TOUR_VERSION = 1
COOKIE_NAME = "askmcneese_guest"
TOKEN_HEADER = "X-Guest-Token"
DEFAULT_MAX_AGE_SECONDS = 60 * 60 * 24 * 60  # 60 days
DEFAULT_QUESTION_LIMIT = 10

# Ordered tour steps for validation / progression.
VALID_STEP_IDS: tuple[str, ...] = (
    "welcome",
    "ask",
    "ask_input",
    "menu",  # legacy mobile-only counted step; still accepted for resume
    "class_planner",
    "planner_week",
    "planner_find",
    "about",
    "about_scroll",  # legacy
    "about_reading",
    "updates",
    "usage",
    "conversations",
    "home_banner",
    "settings",
    "feedback",
    "complete",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_guest_id TEXT NOT NULL UNIQUE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    tour_version INTEGER NOT NULL DEFAULT 1,
    tour_current_step TEXT,
    tour_started_at TEXT,
    tour_completed_at TEXT,
    questions_used INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_guest_token ON guest_sessions(token_hash);

CREATE TABLE IF NOT EXISTS guest_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_session_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    page_url TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guest_feedback_created ON guest_feedback(created_at DESC);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_id() -> str:
    return f"guest_{secrets.token_hex(12)}"


def _display_alias(public_guest_id: str) -> str:
    """Short non-secret label for UI (never the cookie token)."""
    raw = public_guest_id.removeprefix("guest_").replace("-", "")
    digest = hashlib.sha256(public_guest_id.encode("utf-8")).hexdigest()[:4].upper()
    # Prefer a stable 4-char code derived from the public id hash.
    return digest if digest else (raw[:4].upper() if raw else "GUEST")


def _raw_token() -> str:
    return secrets.token_urlsafe(32)


class GuestStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.executescript(SCHEMA)
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(guest_sessions)").fetchall()
            }
            if "questions_used" not in columns:
                connection.execute(
                    "ALTER TABLE guest_sessions ADD COLUMN questions_used INTEGER NOT NULL DEFAULT 0"
                )

    @classmethod
    def from_environment(cls) -> "GuestStore":
        default = Path(__file__).resolve().parents[3] / "guest_sessions.sqlite3"
        return cls(os.getenv("GUEST_DB_PATH", str(default)))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def onboarding_mode(self) -> str:
        mode = os.getenv("ONBOARDING_MODE", "mandatory").strip().lower()
        return mode if mode in {"mandatory", "optional", "disabled"} else "mandatory"

    def cookie_max_age(self) -> int:
        try:
            return max(3600, int(os.getenv("GUEST_COOKIE_MAX_AGE_SECONDS", str(DEFAULT_MAX_AGE_SECONDS))))
        except ValueError:
            return DEFAULT_MAX_AGE_SECONDS

    def question_limit(self) -> int:
        try:
            return max(1, int(os.getenv("GUEST_QUESTION_LIMIT", str(DEFAULT_QUESTION_LIMIT))))
        except ValueError:
            return DEFAULT_QUESTION_LIMIT

    def bootstrap(self, raw_token: str | None) -> tuple[dict[str, Any], str | None]:
        """Return (public_state, new_raw_token_or_None)."""
        if raw_token:
            guest = self._get_by_token(raw_token)
            if guest is not None:
                self._touch(guest["id"])
                return self._public_state(guest, is_new_assignment=False), None
        new_token = _raw_token()
        guest = self._create(new_token)
        return self._public_state(guest, is_new_assignment=True), new_token

    def update_tour(
        self,
        raw_token: str | None,
        *,
        step: str,
        version: int = TOUR_VERSION,
    ) -> dict[str, Any] | None:
        if not raw_token:
            return None
        guest = self._get_by_token(raw_token)
        if guest is None:
            return None
        if version != TOUR_VERSION:
            raise ValueError("unsupported tour version")
        if step not in VALID_STEP_IDS:
            raise ValueError("unknown tour step")
        if guest["tour_completed_at"] and step != "complete":
            # Already complete — ignore regressions; keep completed state.
            return self._public_state(guest, is_new_assignment=False)
        current = guest["tour_current_step"]
        if step != "complete":
            if current and current in VALID_STEP_IDS:
                current_index = VALID_STEP_IDS.index(current)
                next_index = VALID_STEP_IDS.index(step)
                # Allow same step retry and forward-only progress of at most a few steps.
                if next_index < current_index:
                    return self._public_state(guest, is_new_assignment=False)
        now = _now()
        completed_at = guest["tour_completed_at"]
        started_at = guest["tour_started_at"] or now
        if step == "complete":
            # Require reaching feedback before complete unless already completed.
            if not completed_at:
                prior = current or "welcome"
                if prior not in VALID_STEP_IDS or VALID_STEP_IDS.index(prior) < VALID_STEP_IDS.index("feedback"):
                    raise ValueError("tour cannot complete before feedback step")
                completed_at = now
            step_value = "complete"
        else:
            step_value = step
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE guest_sessions
                SET tour_version = ?,
                    tour_current_step = ?,
                    tour_started_at = ?,
                    tour_completed_at = ?,
                    last_seen_at = ?
                WHERE id = ?
                """,
                (TOUR_VERSION, step_value, started_at, completed_at, now, guest["id"]),
            )
        refreshed = self._get_by_id(int(guest["id"]))
        return self._public_state(refreshed, is_new_assignment=False) if refreshed else None

    def reset_tour(self, raw_token: str | None) -> dict[str, Any] | None:
        if not raw_token:
            return None
        guest = self._get_by_token(raw_token)
        if guest is None:
            return None
        now = _now()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE guest_sessions
                SET tour_current_step = NULL,
                    tour_started_at = NULL,
                    tour_completed_at = NULL,
                    tour_version = ?,
                    last_seen_at = ?
                WHERE id = ?
                """,
                (TOUR_VERSION, now, guest["id"]),
            )
        refreshed = self._get_by_id(int(guest["id"]))
        return self._public_state(refreshed, is_new_assignment=False) if refreshed else None

    def replay_tour(self, raw_token: str | None) -> dict[str, Any] | None:
        """Soft reset for Settings replay — same guest identity, tour restarts at welcome."""
        if not raw_token:
            return None
        guest = self._get_by_token(raw_token)
        if guest is None:
            return None
        now = _now()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE guest_sessions
                SET tour_current_step = ?,
                    tour_started_at = ?,
                    tour_completed_at = NULL,
                    tour_version = ?,
                    last_seen_at = ?
                WHERE id = ?
                """,
                ("welcome", now, TOUR_VERSION, now, guest["id"]),
            )
        refreshed = self._get_by_id(int(guest["id"]))
        return self._public_state(refreshed, is_new_assignment=False) if refreshed else None

    def skip_tour(self, raw_token: str | None) -> dict[str, Any] | None:
        """Mark onboarding complete without changing the guest identity."""
        if not raw_token:
            return None
        guest = self._get_by_token(raw_token)
        if guest is None:
            return None
        now = _now()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                UPDATE guest_sessions
                SET tour_current_step = ?,
                    tour_started_at = COALESCE(tour_started_at, ?),
                    tour_completed_at = ?,
                    tour_version = ?,
                    last_seen_at = ?
                WHERE id = ?
                """,
                ("complete", now, now, TOUR_VERSION, now, guest["id"]),
            )
        refreshed = self._get_by_id(int(guest["id"]))
        return self._public_state(refreshed, is_new_assignment=False) if refreshed else None

    def claim_question(self, raw_token: str | None) -> tuple[dict[str, Any] | None, bool]:
        """Atomically consume one beta question allowance for a known guest."""
        if not raw_token:
            return None, False
        token_hash = _hash_token(raw_token)
        limit = self.question_limit()
        now = _now()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            guest = connection.execute(
                "SELECT * FROM guest_sessions WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if guest is None:
                connection.rollback()
                return None, False
            used = int(guest["questions_used"] or 0)
            if used >= limit:
                connection.execute(
                    "UPDATE guest_sessions SET last_seen_at = ? WHERE id = ?",
                    (now, guest["id"]),
                )
                connection.commit()
                refreshed = self._get_by_id(int(guest["id"]))
                return (
                    self._public_state(refreshed, is_new_assignment=False) if refreshed else None,
                    False,
                )
            connection.execute(
                """
                UPDATE guest_sessions
                SET questions_used = questions_used + 1, last_seen_at = ?
                WHERE id = ?
                """,
                (now, guest["id"]),
            )
            connection.commit()
        refreshed = self._get_by_id(int(guest["id"]))
        return (
            self._public_state(refreshed, is_new_assignment=False) if refreshed else None,
            True,
        )

    def submit_feedback(
        self,
        raw_token: str | None,
        *,
        category: str,
        message: str,
        page_url: str | None = None,
    ) -> dict[str, Any] | None:
        if not raw_token:
            return None
        guest = self._get_by_token(raw_token)
        if guest is None:
            return None
        created_at = _now()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """
                INSERT INTO guest_feedback(
                    guest_session_id, category, message, page_url, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (guest["id"], category, message, page_url, created_at),
            )
            feedback_id = int(cursor.lastrowid)
        return {
            "id": feedback_id,
            "category": category,
            "createdAt": created_at,
        }

    def list_feedback(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT f.id, f.category, f.message, f.page_url, f.created_at,
                       g.public_guest_id, g.id AS guest_number
                FROM guest_feedback AS f
                JOIN guest_sessions AS g ON g.id = f.guest_session_id
                ORDER BY f.created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "guestId": str(row["public_guest_id"]),
                "guestAlias": "Guest 1",
                "category": str(row["category"]),
                "message": str(row["message"]),
                "pageUrl": row["page_url"],
                "createdAt": str(row["created_at"]),
            }
            for row in rows
        ]

    def _create(self, raw_token: str) -> sqlite3.Row:
        now = _now()
        public_id = _public_id()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """
                INSERT INTO guest_sessions(
                    public_guest_id, token_hash, created_at, last_seen_at, tour_version
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (public_id, _hash_token(raw_token), now, now, TOUR_VERSION),
            )
            guest_id = int(cursor.lastrowid)
        row = self._get_by_id(guest_id)
        assert row is not None
        return row

    def _touch(self, guest_id: int) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "UPDATE guest_sessions SET last_seen_at = ? WHERE id = ?",
                (_now(), guest_id),
            )

    def _get_by_token(self, raw_token: str) -> sqlite3.Row | None:
        with closing(self._connect()) as connection, connection:
            return connection.execute(
                "SELECT * FROM guest_sessions WHERE token_hash = ?",
                (_hash_token(raw_token),),
            ).fetchone()

    def _get_by_id(self, guest_id: int) -> sqlite3.Row | None:
        with closing(self._connect()) as connection, connection:
            return connection.execute(
                "SELECT * FROM guest_sessions WHERE id = ?",
                (guest_id,),
            ).fetchone()

    def _public_state(
        self,
        guest: sqlite3.Row,
        *,
        is_new_assignment: bool = False,
    ) -> dict[str, Any]:
        completed = bool(guest["tour_completed_at"])
        current = guest["tour_current_step"]
        if completed:
            status = "completed"
        elif current:
            status = "in_progress"
        else:
            status = "not_started"
        mode = self.onboarding_mode()
        if mode == "disabled":
            status = "completed"
        public_id = str(guest["public_guest_id"])
        question_limit = self.question_limit()
        questions_used = int(guest["questions_used"] or 0)
        return {
            "guestId": public_id,
            "displayAlias": "Guest 1",
            "isNewAssignment": bool(is_new_assignment),
            "onboardingMode": mode,
            "tour": {
                "version": int(guest["tour_version"] or TOUR_VERSION),
                "status": status,
                "currentStep": None if status == "completed" else current,
                "startedAt": guest["tour_started_at"],
                "completedAt": guest["tour_completed_at"],
            },
            "usage": {
                "questionsUsed": questions_used,
                "questionLimit": question_limit,
                "questionsRemaining": max(0, question_limit - questions_used),
            },
        }
