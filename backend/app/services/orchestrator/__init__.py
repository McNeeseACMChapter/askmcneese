"""Thin custom multi-skill supervisor on top of RCCS (no LangGraph/CrewAI).

Public entrypoint: ``run`` / ``run_supervised_retrieval``.
"""

from __future__ import annotations

from app.services.orchestrator.config import (
    deep_research_enabled,
    flags_snapshot,
    reflect_enabled,
    supervisor_enabled,
)
from app.services.orchestrator.supervisor import run, run as run_supervised_retrieval

__all__ = [
    "run",
    "run_supervised_retrieval",
    "supervisor_enabled",
    "reflect_enabled",
    "deep_research_enabled",
    "flags_snapshot",
]
