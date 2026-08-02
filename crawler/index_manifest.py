"""Atomic registry/fetch/index/freshness manifest for non-black-box coverage."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "knowledge" / "index_manifest.json"
_lock = threading.Lock()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IndexManifestRecord:
    source_id: str
    url: str
    source_group_ids: list[str]
    registry_status: str
    content_type: str
    fetch_status: str = "registered"
    fetched_at: str | None = None
    content_hash: str | None = None
    parser: str | None = None
    chunk_count: int = 0
    collection: str | None = None
    indexed_at: str | None = None
    last_verified: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    manifest_updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IndexManifest:
    def __init__(self, path: Path = DEFAULT_MANIFEST_PATH):
        self.path = path
        self.records: dict[str, dict[str, Any]] = {}
        self.version = "1.0.0"
        self.generated_at = utcnow()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return
        self.version = str(data.get("version") or self.version)
        self.generated_at = str(data.get("generated_at") or self.generated_at)
        self.records = {
            str(item.get("source_id")): item
            for item in (data.get("sources") or [])
            if item.get("source_id")
        }

    def update(self, record: IndexManifestRecord | dict[str, Any]) -> None:
        item = record.to_dict() if isinstance(record, IndexManifestRecord) else dict(record)
        source_id = str(item.get("source_id") or "")
        if not source_id:
            raise ValueError("manifest records require source_id")
        existing = dict(self.records.get(source_id) or {})
        existing.update({key: value for key, value in item.items() if value is not None})
        existing["manifest_updated_at"] = utcnow()
        self.records[source_id] = existing

    def save(self) -> None:
        payload = {
            "version": self.version,
            "generated_at": utcnow(),
            "summary": self.summary(),
            "sources": sorted(self.records.values(), key=lambda item: item.get("source_id", "")),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with _lock:
            temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.path)

    def summary(self) -> dict[str, Any]:
        values = list(self.records.values())
        by_status: dict[str, int] = {}
        for item in values:
            status = str(item.get("fetch_status") or "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        groups: dict[str, dict[str, int]] = {}
        for item in values:
            for group in item.get("source_group_ids") or ["unassigned"]:
                group_stats = groups.setdefault(group, {"registered": 0, "indexed": 0, "chunks": 0, "failed": 0})
                group_stats["registered"] += 1
                group_stats["chunks"] += int(item.get("chunk_count") or 0)
                if int(item.get("chunk_count") or 0) > 0:
                    group_stats["indexed"] += 1
                if item.get("error_code"):
                    group_stats["failed"] += 1
        return {
            "registered_sources": len(values),
            "indexed_sources": sum(1 for item in values if int(item.get("chunk_count") or 0) > 0),
            "total_chunks": sum(int(item.get("chunk_count") or 0) for item in values),
            "with_content_hash": sum(1 for item in values if item.get("content_hash")),
            "with_last_verified": sum(1 for item in values if item.get("last_verified")),
            "by_fetch_status": by_status,
            "by_source_group": groups,
        }
