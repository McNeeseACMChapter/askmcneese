"""Supervisor feature flags (read at call time for uvicorn --reload)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[3]
_REPO_ASK = _HERE.parents[4]
load_dotenv(_REPO_ASK / ".env", override=False)
load_dotenv(_BACKEND_ROOT / ".env", override=True)


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def supervisor_enabled() -> bool:
    """When on (and RCCS is on), /ask uses the Plan→Route→Execute→Reflect loop."""
    return _flag("SUPERVISOR_ENABLED", "0")


def reflect_enabled() -> bool:
    """Run the reflection/quality gate after skill execution (default on with supervisor)."""
    return _flag("SUPERVISOR_REFLECT_ENABLED", "1")


def reflect_llm_enabled() -> bool:
    """Optional Claude critique; heuristic gate always runs when reflect is on."""
    return _flag("SUPERVISOR_REFLECT_LLM", "0")


def deep_research_enabled() -> bool:
    """Alias / product flag: enables supervisor + reflection for compound queries."""
    return _flag("DEEP_RESEARCH_ENABLED", "0") or supervisor_enabled()


def flags_snapshot() -> dict[str, object]:
    return {
        "SUPERVISOR_ENABLED": supervisor_enabled(),
        "SUPERVISOR_REFLECT_ENABLED": reflect_enabled(),
        "SUPERVISOR_REFLECT_LLM": reflect_llm_enabled(),
        "DEEP_RESEARCH_ENABLED": deep_research_enabled(),
    }
