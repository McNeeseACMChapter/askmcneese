from __future__ import annotations

import json
import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


PROJECT_SEED = (
    {
        "id": "proj-ask-2",
        "name": "AskMcNeese Phase 2",
        "owner": "Prince Pudasaini",
        "ownerInitials": "PP",
        "health": "at_risk",
        "progressPercent": 62,
        "nextMilestone": "Evidence pack for retrieval eval",
        "dueDate": "2026-08-30",
        "scope": "Ship retrieval quality improvements and ACM panel operating surfaces.",
    },
    {
        "id": "proj-hack",
        "name": "Hack Night series",
        "owner": "Jordan Lee",
        "ownerInitials": "JL",
        "health": "on_track",
        "progressPercent": 78,
        "nextMilestone": "Confirm September venue",
        "dueDate": "2026-09-05",
        "scope": "Monthly build nights for members.",
    },
    {
        "id": "proj-onboard",
        "name": "Member onboarding kit",
        "owner": "Casey Nguyen",
        "ownerInitials": "CN",
        "health": "on_track",
        "progressPercent": 44,
        "nextMilestone": "Draft checklist review",
        "dueDate": "2026-08-15",
        "scope": "Standardize new-member onboarding evidence.",
    },
)

ACCESS_CONTRACT = (
    {
        "module": "Home & reports",
        "route": "/home",
        "mode": "derived",
        "editable": "None directly",
        "controlled": "Source records only",
        "derived": "Counts, health rollups, activity, trends",
        "destination": "Read model built from operational records",
    },
    {
        "module": "Projects",
        "route": "/projects",
        "mode": "managed",
        "editable": "Scope, milestone, due date, progress, health reason",
        "controlled": "Owner, approval, completion, archive",
        "derived": "Trend, risk count, evidence completeness",
        "destination": "PostgreSQL target · SQLite development adapter",
    },
    {
        "module": "Meetings & minutes",
        "route": "/meetings",
        "mode": "workflow",
        "editable": "Draft agenda, time, location, draft minutes",
        "controlled": "Publish, quorum, approved minutes, archive",
        "derived": "Attendance and agenda completion rollups",
        "destination": "Meeting records + immutable minutes versions",
    },
    {
        "module": "Events",
        "route": "/events",
        "mode": "workflow",
        "editable": "Concept, schedule, venue plan, volunteer plan",
        "controlled": "Budget clearance, approval, completion",
        "derived": "Readiness and registration percentages",
        "destination": "Event records + linked finance/content workflows",
    },
    {
        "module": "Members & roles",
        "route": "/members",
        "mode": "managed",
        "editable": "Own availability, skills, contact preferences",
        "controlled": "Role, term, standing, privileged access",
        "derived": "Engagement and onboarding completion",
        "destination": "Membership records + role-assignment workflow",
    },
    {
        "module": "Governance",
        "route": "/governance",
        "mode": "workflow",
        "editable": "Proposals and evidence before submission",
        "controlled": "Votes, approvals, officer terms, recorded decisions",
        "derived": "Quorum health",
        "destination": "Append-only decision and approval records",
    },
    {
        "module": "Finance",
        "route": "/finance",
        "mode": "workflow",
        "editable": "Requests, vendor, purpose, receipt submission",
        "controlled": "Budget, approvals, reconciliation, close",
        "derived": "Actual, remaining, variance, aging",
        "destination": "Finance ledger + object storage for receipts",
    },
    {
        "module": "SGA",
        "route": "/sga",
        "mode": "workflow",
        "editable": "Packet draft, request amount, hearing notes",
        "controlled": "ACM approval, external award, disbursement",
        "derived": "Award percentage and open-condition count",
        "destination": "SGA request records + external evidence",
    },
    {
        "module": "Communications",
        "route": "/communications",
        "mode": "workflow",
        "editable": "Draft body, channel, proposed publish time",
        "controlled": "Review, sensitive approval, publish",
        "derived": "Pipeline counts and schedule status",
        "destination": "Content records + published artifact archive",
    },
    {
        "module": "Documents",
        "route": "/documents",
        "mode": "managed",
        "editable": "Title, description, replacement upload",
        "controlled": "Classification, retention, official version",
        "derived": "Expiry and evidence completeness warnings",
        "destination": "Object storage bytes + relational metadata",
    },
    {
        "module": "Notifications",
        "route": "/notifications",
        "mode": "managed",
        "editable": "Read state and personal delivery preferences",
        "controlled": "System-generated message and recipient",
        "derived": "Unread and priority counts",
        "destination": "Notification delivery log",
    },
    {
        "module": "Administration",
        "route": "/administration",
        "mode": "restricted",
        "editable": "Technical configuration with change reason",
        "controlled": "Organizational approvals and finance authority",
        "derived": "Service health",
        "destination": "Configuration store + immutable audit",
    },
    {
        "module": "Audit",
        "route": "/audit",
        "mode": "immutable",
        "editable": "Nothing",
        "controlled": "Export by authorized roles",
        "derived": "Filtered views only",
        "destination": "Append-only audit log",
    },
)


class ProjectPatch(BaseModel):
    scope: str | None = Field(default=None, min_length=8, max_length=1000)
    nextMilestone: str | None = Field(default=None, min_length=3, max_length=180)
    dueDate: str | None = None
    progressPercent: int | None = Field(default=None, ge=0, le=100)
    health: Literal["on_track", "at_risk", "blocked", "completed"] | None = None
    reason: str = Field(min_length=8, max_length=500)

    @field_validator("dueDate")
    @classmethod
    def validate_due_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("dueDate must use YYYY-MM-DD") from exc
        return value


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with closing(self.connect()) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    owner_initials TEXT NOT NULL,
                    health TEXT NOT NULL,
                    progress_percent INTEGER NOT NULL CHECK(progress_percent BETWEEN 0 AND 100),
                    next_milestone TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    before_json TEXT NOT NULL,
                    after_json TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )
            count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            if count == 0:
                now = datetime.now(timezone.utc).isoformat()
                db.executemany(
                    """
                    INSERT INTO projects (
                        id, name, owner, owner_initials, health, progress_percent,
                        next_milestone, due_date, scope, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            project["id"],
                            project["name"],
                            project["owner"],
                            project["ownerInitials"],
                            project["health"],
                            project["progressPercent"],
                            project["nextMilestone"],
                            project["dueDate"],
                            project["scope"],
                            now,
                        )
                        for project in PROJECT_SEED
                    ],
                )
            db.commit()

    @staticmethod
    def project_from_row(row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "name": row["name"],
            "owner": row["owner"],
            "ownerInitials": row["owner_initials"],
            "health": row["health"],
            "progressPercent": row["progress_percent"],
            "nextMilestone": row["next_milestone"],
            "dueDate": row["due_date"],
            "scope": row["scope"],
            "updatedAt": row["updated_at"],
        }

    def list_projects(self) -> list[dict[str, object]]:
        with closing(self.connect()) as db:
            rows = db.execute("SELECT * FROM projects ORDER BY name").fetchall()
            return [self.project_from_row(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, object] | None:
        with closing(self.connect()) as db:
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return self.project_from_row(row) if row else None

    def update_project(
        self,
        project_id: str,
        changes: dict[str, object],
        *,
        actor: str,
        actor_role: str,
        reason: str,
    ) -> dict[str, object]:
        column_map = {
            "scope": "scope",
            "nextMilestone": "next_milestone",
            "dueDate": "due_date",
            "progressPercent": "progress_percent",
            "health": "health",
        }
        with closing(self.connect()) as db:
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if row is None:
                raise KeyError(project_id)
            before = self.project_from_row(row)
            assignments: list[str] = []
            values: list[object] = []
            for key, value in changes.items():
                column = column_map[key]
                assignments.append(f"{column} = ?")
                values.append(value)
            updated_at = datetime.now(timezone.utc).isoformat()
            assignments.append("updated_at = ?")
            values.extend((updated_at, project_id))
            db.execute(
                f"UPDATE projects SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
            next_row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            after = self.project_from_row(next_row)
            db.execute(
                """
                INSERT INTO audit_events (
                    occurred_at, actor, actor_role, action, resource,
                    before_json, after_json, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    updated_at,
                    actor,
                    actor_role,
                    "PROJECT_UPDATED",
                    f"Project:{project_id}",
                    json.dumps(before, sort_keys=True),
                    json.dumps(after, sort_keys=True),
                    reason,
                ),
            )
            db.commit()
            return after

    def list_audit(self, limit: int = 100) -> list[dict[str, object]]:
        with closing(self.connect()) as db:
            rows = db.execute(
                "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "at": row["occurred_at"],
                    "actor": row["actor"],
                    "actorRole": row["actor_role"],
                    "action": row["action"],
                    "resource": row["resource"],
                    "before": json.loads(row["before_json"]),
                    "after": json.loads(row["after_json"]),
                    "reason": row["reason"],
                }
                for row in rows
            ]


def authorize_project_edit(project: dict[str, object], actor: str, role: str) -> None:
    if role in {"president", "advisor"}:
        return
    if role == "project_manager" and project["owner"] == actor:
        return
    raise HTTPException(
        status_code=403,
        detail="project.manage is limited to the assigned owner or authorized officers",
    )


def create_app(database_path: Path | None = None) -> FastAPI:
    default_path = Path(__file__).resolve().parents[1] / "data" / "acm.sqlite3"
    database = Database(database_path or Path(os.getenv("ACM_DATABASE_PATH", default_path)))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        app.state.database = database
        yield

    app = FastAPI(
        title="McNeese ACM Operations API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3100", "http://localhost:3100"],
        allow_credentials=False,
        allow_methods=["GET", "PATCH", "POST"],
        allow_headers=["Content-Type", "X-ACM-Actor", "X-ACM-Role"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "persistence": "sqlite-development"}

    @app.get("/api/acm/access-contract")
    def access_contract() -> dict[str, object]:
        return {
            "environment": "development",
            "authoritativeTarget": "PostgreSQL + object storage",
            "currentAdapter": "SQLite",
            "modules": ACCESS_CONTRACT,
        }

    @app.get("/api/acm/projects")
    def list_projects(request: Request) -> list[dict[str, object]]:
        return request.app.state.database.list_projects()

    @app.get("/api/acm/projects/{project_id}")
    def get_project(project_id: str, request: Request) -> dict[str, object]:
        project = request.app.state.database.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @app.patch("/api/acm/projects/{project_id}")
    def update_project(
        project_id: str,
        patch: ProjectPatch,
        request: Request,
        x_acm_actor: str = Header(...),
        x_acm_role: str = Header(...),
    ) -> dict[str, object]:
        project = request.app.state.database.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        authorize_project_edit(project, x_acm_actor, x_acm_role)
        changes = patch.model_dump(
            exclude={"reason"},
            exclude_none=True,
        )
        if not changes:
            raise HTTPException(status_code=422, detail="No editable project fields supplied")
        try:
            return request.app.state.database.update_project(
                project_id,
                changes,
                actor=x_acm_actor,
                actor_role=x_acm_role,
                reason=patch.reason,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Project not found") from exc

    @app.get("/api/acm/audit")
    def list_audit(
        request: Request,
        x_acm_role: str = Header(...),
    ) -> list[dict[str, object]]:
        if x_acm_role not in {"advisor", "president", "secretary", "treasurer"}:
            raise HTTPException(status_code=403, detail="audit.view is required")
        return request.app.state.database.list_audit()

    return app


app = create_app()