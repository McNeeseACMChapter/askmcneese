"""Feature boundary for additive campus-intelligence migration."""

from __future__ import annotations

import os


def enabled() -> bool:
    """The legacy classifier/hybrid path remains the one-variable rollback."""
    return os.getenv("CAMPUS_INTELLIGENCE_ENABLED", "1").strip().lower() not in {
        "0", "false", "off", "no"
    }
