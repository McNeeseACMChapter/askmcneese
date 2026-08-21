"""Reconcile the governed registry with the active Chroma collection."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


THIS = Path(__file__).resolve()
REPO = THIS.parents[2]
CRAWLER = REPO / "crawler"
sys.path.insert(0, str(CRAWLER))

from config import CHROMA_DIR, COLLECTION  # noqa: E402
from governed_registry import load_governed_registry  # noqa: E402
from index_manifest import IndexManifest, IndexManifestRecord  # noqa: E402


def chroma_counts() -> tuple[Counter, Counter]:
    try:
        import chromadb

        collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(COLLECTION)
        result = collection.get(include=["metadatas"])
    except Exception as exc:
        print(f"Chroma reconciliation unavailable: {exc}")
        return Counter(), Counter()
    by_source_id: Counter = Counter()
    by_url: Counter = Counter()
    for metadata in result.get("metadatas") or []:
        metadata = metadata or {}
        source_id = str(metadata.get("source_id") or "")
        url = str(metadata.get("source_url") or "").rstrip("/").lower()
        if source_id:
            by_source_id[source_id] += 1
        if url:
            by_url[url] += 1
    return by_source_id, by_url


def build(path: Path | None = None) -> IndexManifest:
    by_source_id, by_url = chroma_counts()
    manifest = IndexManifest(path) if path else IndexManifest()
    for source in load_governed_registry():
        chunks = by_source_id[source.source_id] or by_url[source.url.rstrip("/").lower()]
        if chunks:
            status = "indexed"
        elif source.last_ingested_timestamp:
            status = "ingested_unconfirmed"
        else:
            status = "registered"
        manifest.update(IndexManifestRecord(
            source_id=source.source_id,
            url=source.url,
            source_group_ids=list(source.source_group_ids),
            registry_status="allowed",
            content_type=source.content_type,
            fetch_status=status,
            fetched_at=source.last_ingested_timestamp or None,
            content_hash=source.content_hash or None,
            chunk_count=int(chunks),
            collection=COLLECTION if chunks else None,
            indexed_at=source.last_ingested_timestamp if chunks else None,
            last_verified=source.last_ingested_timestamp or None,
        ))
    manifest.save()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = build(args.output)
    print(manifest.path)
    print(manifest.summary())


if __name__ == "__main__":
    main()
