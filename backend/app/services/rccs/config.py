"""RCCS feature flags and bounded limits.

Flags are read from the environment at call time so uvicorn --reload and
updated .env files take effect without relying on frozen import-time constants.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load local configuration without replacing process/container/CI settings.
# Precedence: process environment > backend/.env > repository .env.
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[3]  # .../backend
_REPO_ASK = _HERE.parents[4]  # .../askmcneese
load_dotenv(_BACKEND_ROOT / ".env", override=False)
load_dotenv(_REPO_ASK / ".env", override=False)


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def rccs_enabled() -> bool:
    return _flag("RCCS_ENABLED", "0")


def hybrid_enabled() -> bool:
    return _flag("RCCS_HYBRID_ENABLED", "1")


def companions_enabled() -> bool:
    return _flag("RCCS_COMPANIONS_ENABLED", "0")


def rmp_enabled() -> bool:
    return _flag("RCCS_RMP_ENABLED", "0")


def social_links_enabled() -> bool:
    return _flag("RCCS_SOCIAL_LINKS_ENABLED", "0")


def max_kb_results() -> int:
    return _int("RCCS_MAX_KB_RESULTS", 6)


def max_official_results() -> int:
    return _int("RCCS_MAX_OFFICIAL_RESULTS", 5)


def max_companion_results() -> int:
    return _int("RCCS_MAX_COMPANION_RESULTS", 3)


def max_total_evidence() -> int:
    return _int("RCCS_MAX_TOTAL_EVIDENCE", 10)


def max_chars_per_source() -> int:
    return _int("RCCS_MAX_CHARS_PER_SOURCE", 8000)


def fetch_timeout_seconds() -> float:
    return _float("RCCS_FETCH_TIMEOUT_SECONDS", 15.0)


def total_retrieval_timeout_seconds() -> float:
    return _float("RCCS_TOTAL_RETRIEVAL_TIMEOUT_SECONDS", 10.0)


def fast_retrieval_timeout_seconds() -> float:
    return _float("RCCS_FAST_RETRIEVAL_TIMEOUT_SECONDS", 3.5)


def catalog_retrieval_timeout_seconds() -> float:
    return _float("RCCS_CATALOG_RETRIEVAL_TIMEOUT_SECONDS", 40.0)


def turn_retrieval_budget_seconds() -> float:
    """One wall-clock budget shared by every retrieval wave in a turn."""
    return max(1.0, _float("RCCS_TURN_RETRIEVAL_BUDGET_SECONDS", 10.0))


def targeted_recovery_timeout_seconds() -> float:
    """Small final slice for filling missing material fields."""
    return max(0.25, _float("RCCS_TARGETED_RECOVERY_TIMEOUT_SECONDS", 1.5))


def rewrite_timeout_seconds() -> float:
    return max(0.25, _float("RCCS_REWRITE_TIMEOUT_SECONDS", 1.25))


def snapshot_max_age_days() -> int:
    """Maximum age for an official, content-bearing verified snapshot."""
    return max(0, _int("RCCS_SNAPSHOT_MAX_AGE_DAYS", 7))


def min_relevance_score() -> float:
    return _float("RCCS_MIN_RELEVANCE_SCORE", 0.22)


def max_citations() -> int:
    return _int("RCCS_MAX_CITATIONS", 4)


def kb_min_results() -> int:
    return _int("RCCS_KB_MIN_RESULTS", 1)


# Back-compat module attributes (evaluated once for imports that read them
# directly). Prefer the functions above for request-time decisions.
RCCS_ENABLED = rccs_enabled()
RCCS_HYBRID_ENABLED = hybrid_enabled()
RCCS_COMPANIONS_ENABLED = companions_enabled()
RCCS_RMP_ENABLED = rmp_enabled()
RCCS_SOCIAL_LINKS_ENABLED = social_links_enabled()
RCCS_MAX_KB_RESULTS = max_kb_results()
RCCS_MAX_OFFICIAL_RESULTS = max_official_results()
RCCS_MAX_COMPANION_RESULTS = max_companion_results()
RCCS_MAX_TOTAL_EVIDENCE = max_total_evidence()
RCCS_MAX_CHARS_PER_SOURCE = max_chars_per_source()
RCCS_FETCH_TIMEOUT_SECONDS = fetch_timeout_seconds()
RCCS_TOTAL_RETRIEVAL_TIMEOUT_SECONDS = total_retrieval_timeout_seconds()
RCCS_KB_MIN_RESULTS = kb_min_results()


def flags_snapshot() -> dict[str, object]:
    return {
        "RCCS_ENABLED": rccs_enabled(),
        "RCCS_HYBRID_ENABLED": hybrid_enabled(),
        "RCCS_COMPANIONS_ENABLED": companions_enabled(),
        "RCCS_RMP_ENABLED": rmp_enabled(),
        "RCCS_SOCIAL_LINKS_ENABLED": social_links_enabled(),
        "RCCS_MAX_KB_RESULTS": max_kb_results(),
        "RCCS_MAX_OFFICIAL_RESULTS": max_official_results(),
        "RCCS_MAX_COMPANION_RESULTS": max_companion_results(),
        "RCCS_MAX_TOTAL_EVIDENCE": max_total_evidence(),
        "RCCS_FAST_RETRIEVAL_TIMEOUT_SECONDS": fast_retrieval_timeout_seconds(),
        "RCCS_TURN_RETRIEVAL_BUDGET_SECONDS": turn_retrieval_budget_seconds(),
        "RCCS_TARGETED_RECOVERY_TIMEOUT_SECONDS": targeted_recovery_timeout_seconds(),
        "RCCS_REWRITE_TIMEOUT_SECONDS": rewrite_timeout_seconds(),
        "RCCS_SNAPSHOT_MAX_AGE_DAYS": snapshot_max_age_days(),
        "RCCS_MAX_CITATIONS": max_citations(),
    }
