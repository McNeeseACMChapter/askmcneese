"""Governed local Chroma ingest for HTML, dynamic pages, and PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import chromadb

from chunker import chunk_text, chunk_to_dict
from clean_text import clean_html
from config import CHROMA_DIR, COLLECTION
from crawler import fetch_url
from index_manifest import IndexManifest, IndexManifestRecord
from source_registry import Source, crawl_allowed_sources

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "docs" / "samples"


def _collection():
    return chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(name=COLLECTION)


def _looks_like_pdf(url: str) -> bool:
    return url.lower().split("?")[0].strip().endswith(".pdf")


def _manifest_record(url: str, meta: dict, result: dict, *, content_hash: str | None = None, parser: str | None = None) -> None:
    source_id = str(meta.get("source_id") or "")
    if not source_id:
        return
    manifest = IndexManifest()
    ok = bool(result.get("ok"))
    now = datetime.now(timezone.utc).isoformat()
    manifest.update(IndexManifestRecord(
        source_id=source_id,
        url=url,
        source_group_ids=list(meta.get("source_group_ids") or []),
        registry_status="allowed",
        content_type=str(meta.get("content_type") or ("pdf" if _looks_like_pdf(url) else "html")),
        fetch_status="indexed" if ok else "failed",
        fetched_at=now,
        content_hash=content_hash,
        parser=parser,
        chunk_count=int(result.get("chunks") or 0),
        collection=COLLECTION if ok else None,
        indexed_at=now if ok else None,
        last_verified=now if ok else None,
        error_code=None if ok else "INGEST_FAILURE",
        error_detail=None if ok else str(result.get("error") or "unknown ingest failure")[:500],
    ))
    manifest.save()


def ingest_source(
    url: str,
    *,
    content_type: str | None = None,
    meta: dict | None = None,
    write_samples: bool = False,
) -> dict:
    """Route one governed source through a shared manifest-aware entrypoint."""
    source_meta = dict(meta or {})
    source_meta.setdefault("content_type", content_type or ("pdf" if _looks_like_pdf(url) else "html"))
    if source_meta["content_type"] == "pdf":
        from ingest_pdf import ingest_pdf

        result = ingest_pdf(url, meta=source_meta, collection=_collection())
        _manifest_record(url, source_meta, result, parser="pdf")
        return result
    return ingest_page(url, write_samples=write_samples, meta=source_meta)


def ingest_page(url: str, write_samples: bool = False, meta: dict | None = None) -> dict:
    fetched = fetch_url(url)
    source_meta = dict(fetched.meta or {})
    source_meta.update(meta or {})
    if fetched.source:
        source_meta.setdefault("source_id", fetched.source.source_id)
        source_meta.setdefault("source_group_ids", list(fetched.source.source_group_ids))
        source_meta.setdefault("content_type", fetched.source.content_type)
    if not fetched.ok:
        result = {"url": url, "ok": False, "error": fetched.error}
        _manifest_record(url, source_meta, result, parser="html")
        return result

    text = clean_html(fetched.html or "")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    chunks = chunk_text(
        text,
        source_url=url,
        title=source_meta.get("title", ""),
        category=source_meta.get("category", ""),
        trust_tier=source_meta.get("trust_tier", ""),
        last_checked_date=source_meta.get("last_checked_date", ""),
        source_id=source_meta.get("source_id", "SRC"),
    )
    if not chunks:
        result = {"url": url, "ok": False, "error": "No chunks produced."}
        _manifest_record(url, source_meta, result, content_hash=content_hash, parser="html")
        return result

    collection = _collection()
    group_ids = json.dumps(list(source_meta.get("source_group_ids") or []), separators=(",", ":"))
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{
            "source_id": source_meta.get("source_id", "SRC"),
            "source_url": c.source_url,
            "title": c.title,
            "category": c.category,
            "trust_tier": c.trust_tier,
            "last_checked_date": c.last_checked_date,
            "chunk_index": c.chunk_index,
            "chunk_type": c.chunk_type,
            "source_group_ids": group_ids,
            "content_hash": content_hash,
        } for c in chunks],
    )

    if write_samples:
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        (SAMPLES_DIR / "clean_text_sample.md").write_text(
            f"# Clean text sample\n\nSource: {url}\n\n{text[:4000]}\n", encoding="utf-8"
        )
        (SAMPLES_DIR / "chunks_sample.json").write_text(
            json.dumps([chunk_to_dict(c) for c in chunks[:3]], indent=2), encoding="utf-8"
        )

    result = {
        "url": url,
        "ok": True,
        "chunks": len(chunks),
        "collection": COLLECTION,
        "stored_total": collection.count(),
        "content_hash": content_hash,
    }
    _manifest_record(url, source_meta, result, content_hash=content_hash, parser="html")
    return result


def _source_meta(source: Source) -> dict:
    return {
        "source_id": source.source_id,
        "title": source.title,
        "category": source.category,
        "trust_tier": source.trust_tier,
        "last_checked_date": source.last_checked_date,
        "content_type": source.content_type,
        "source_group_ids": list(source.source_group_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AskMcNeese governed ingest")
    parser.add_argument("--url")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--no-samples", action="store_true")
    args = parser.parse_args()

    allowed = crawl_allowed_sources()
    if args.url:
        targets = [source for source in allowed if source.url.rstrip("/") == args.url.rstrip("/")]
    elif args.all:
        targets = allowed[:args.limit]
    else:
        targets = allowed[:1]
    if not targets:
        print("No allowed governed sources found.")
        return
    for index, source in enumerate(targets):
        result = ingest_source(
            source.url,
            content_type=source.content_type,
            meta=_source_meta(source),
            write_samples=(index == 0 and not args.no_samples),
        )
        if result["ok"]:
            print(f"INGESTED  {source.url}\n  chunks={result['chunks']} collection={result.get('collection', COLLECTION)}")
        else:
            print(f"SKIPPED   {source.url}\n  {result['error']}")


if __name__ == "__main__":
    main()
