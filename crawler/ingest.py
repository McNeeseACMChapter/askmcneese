"""BE-04 — Local ChromaDB ingest.

Ties the pipeline together: fetch -> clean -> chunk -> insert into a local
ChromaDB collection. Also writes reproducible samples for review (BE-05).

Usage:
    python ingest.py                       # ingest the first allowed source + write samples
    python ingest.py --url https://www.mcneese.edu/
    python ingest.py --all --limit 3       # ingest first 3 allowed sources
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb

from chunker import chunk_text, chunk_to_dict
from clean_text import clean_html
from config import CHROMA_DIR, COLLECTION
from crawler import fetch_url
from source_registry import crawl_allowed_sources
SAMPLES_DIR = Path(__file__).resolve().parents[1] / "docs" / "samples"


def _collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION)


def _looks_like_pdf(url: str) -> bool:
    return url.lower().split("?")[0].strip().endswith(".pdf")


def ingest_source(url: str, *, content_type: str | None = None,
                  meta: dict | None = None, write_samples: bool = False) -> dict:
    """Route a source to the right ingester based on content type.

    ``content_type`` may be "pdf", "html", or "dynamic_catalog" (from the merged
    registry). When omitted it is inferred from the URL extension. Both the HTML
    and PDF paths produce the same chunk/metadata shape and upsert to the same
    ChromaDB collection.
    """
    is_pdf = content_type == "pdf" or (content_type is None and _looks_like_pdf(url))
    if is_pdf:
        from ingest_pdf import ingest_pdf
        return ingest_pdf(url, meta=meta, collection=_collection())
    return ingest_page(url, write_samples=write_samples)


def ingest_page(url: str, write_samples: bool = False) -> dict:
    fetched = fetch_url(url)
    if not fetched.ok:
        return {"url": url, "ok": False, "error": fetched.error}

    text = clean_html(fetched.html or "")
    meta = fetched.meta
    chunks = chunk_text(
        text,
        source_url=url,
        title=meta.get("title", ""),
        category=meta.get("category", ""),
        trust_tier=meta.get("trust_tier", ""),
        last_checked_date=meta.get("last_checked_date", ""),
        source_id=meta.get("source_id", "SRC"),
    )
    if not chunks:
        return {"url": url, "ok": False, "error": "No chunks produced."}

    collection = _collection()
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{
            "source_url": c.source_url,
            "title": c.title,
            "category": c.category,
            "trust_tier": c.trust_tier,
            "last_checked_date": c.last_checked_date,
            "chunk_index": c.chunk_index,
            "chunk_type": c.chunk_type,
        } for c in chunks],
    )

    if write_samples:
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        (SAMPLES_DIR / "clean_text_sample.md").write_text(
            f"# Clean text sample\n\nSource: {url}\n\n{text[:4000]}\n", encoding="utf-8")
        (SAMPLES_DIR / "chunks_sample.json").write_text(
            json.dumps([chunk_to_dict(c) for c in chunks[:3]], indent=2), encoding="utf-8")

    return {
        "url": url,
        "ok": True,
        "chunks": len(chunks),
        "collection": COLLECTION,
        "stored_total": collection.count(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AskMcNeese local ingest proof")
    parser.add_argument("--url", help="A single approved URL to ingest")
    parser.add_argument("--all", action="store_true", help="Ingest all allowed sources")
    parser.add_argument("--limit", type=int, default=1, help="Max sources when using --all")
    parser.add_argument("--no-samples", action="store_true", help="Skip writing samples")
    args = parser.parse_args()

    targets: list[str]
    if args.url:
        targets = [args.url]
    elif args.all:
        targets = [s.url for s in crawl_allowed_sources()[:args.limit]]
    else:
        allowed = crawl_allowed_sources()
        targets = [allowed[0].url] if allowed else []

    if not targets:
        print("No allowed sources found in the registry.")
        return

    for i, url in enumerate(targets):
        result = ingest_page(url, write_samples=(i == 0 and not args.no_samples))
        if result["ok"]:
            print(f"INGESTED  {url}\n  chunks={result['chunks']}  "
                  f"collection={result['collection']}  stored_total={result['stored_total']}")
        else:
            print(f"SKIPPED   {url}\n  {result['error']}")


if __name__ == "__main__":
    main()
