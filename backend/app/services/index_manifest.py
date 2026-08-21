"""Read-only runtime view of crawler/index coverage state."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "index_manifest.json"


@lru_cache(maxsize=1)
def get_index_manifest_summary() -> dict[str, Any]:
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "registered_sources": 0, "indexed_sources": 0}
    summary = dict(data.get("summary") or {})
    summary["available"] = True
    summary["manifest_version"] = data.get("version")
    summary["generated_at"] = data.get("generated_at")
    return summary


def clear_index_manifest_cache() -> None:
    get_index_manifest_summary.cache_clear()
