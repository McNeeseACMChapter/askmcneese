"""PDF ingest pipeline for AskMcNeese.

Turns a McNeese PDF (policy, disclosure, form, report) into ChromaDB-ready
chunks using the *same* structure-aware chunker as the HTML path so tables stay
intact.

Pipeline
--------
1. ``extract_pdf_pages(url_or_path)`` - download (if URL) and extract, per page:
     * body text via PyMuPDF (fitz) - fast, good layout
     * tables via pdfplumber, rendered to Markdown pipe tables
   Scanned/image-only PDFs (no extractable text) return ``None``.
2. ``pdf_pages_to_chunks(pages, ...)`` - feed each page's ``text + tables`` to the
   shared ``chunk_text()`` so table blocks become ``chunk_type="table"`` chunks
   and prose becomes ``chunk_type="prose"``. Each chunk carries ``page_num`` and
   ``is_table`` metadata.
3. ``ingest_pdf(url, meta)`` - orchestrates extract -> chunk -> Chroma upsert and
   returns the same result dict shape as ``ingest.ingest_page``.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

from chunker import chunk_text

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DOWNLOAD_TIMEOUT = 60


@dataclass
class PdfPage:
    page_num: int          # 1-indexed
    text: str              # body prose extracted from the page
    tables_markdown: str    # all tables on the page, rendered as Markdown ("" if none)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def _download_pdf(url: str) -> Path:
    """Download a PDF to a temp file and return its path."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=DOWNLOAD_TIMEOUT)
    resp.raise_for_status()
    name = Path(urlparse(url).path).name or "download.pdf"
    tmp_dir = Path(tempfile.gettempdir()) / "askmcneese_pdfs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    # Prefix with a short hash so different URLs with the same basename don't clash.
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    path = tmp_dir / f"{digest}_{name}"
    path.write_bytes(resp.content)
    return path


# ---------------------------------------------------------------------------
# Table -> Markdown
# ---------------------------------------------------------------------------
def _table_to_markdown(table: list[list]) -> str:
    """Render a pdfplumber table (list of rows) as a GitHub-style Markdown table."""
    rows = [[(c if c is not None else "").strip().replace("\n", " ") for c in row]
            for row in table if row is not None]
    rows = [r for r in rows if any(cell for cell in r)]  # drop empty rows
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join(["---"] * width) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# A/B) Extraction
# ---------------------------------------------------------------------------
def extract_pdf_pages(url_or_path: str) -> list[PdfPage] | None:
    """Extract per-page text + tables. Returns None for scanned/no-text PDFs."""
    import fitz  # PyMuPDF
    import pdfplumber

    is_url = url_or_path.lower().startswith(("http://", "https://"))
    path = _download_pdf(url_or_path) if is_url else Path(url_or_path)

    pages: list[PdfPage] = []

    # 1) Text via PyMuPDF.
    page_texts: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            page_texts.append(page.get_text("text") or "")

    # 2) Tables via pdfplumber (best-effort; some PDFs raise on odd fonts).
    page_tables: list[str] = ["" for _ in page_texts]
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= len(page_tables):
                    break
                md_tables = []
                for tbl in page.extract_tables() or []:
                    md = _table_to_markdown(tbl)
                    if md:
                        md_tables.append(md)
                page_tables[i] = "\n\n".join(md_tables)
    except Exception:  # noqa: BLE001 - tables are a bonus, never fatal
        pass

    for i, text in enumerate(page_texts):
        pages.append(PdfPage(page_num=i + 1, text=text.strip(), tables_markdown=page_tables[i]))

    # Scanned/image-only PDF: no extractable text anywhere.
    total_chars = sum(len(p.text) for p in pages)
    if total_chars < 40:
        return None
    return pages


# ---------------------------------------------------------------------------
# C) Chunking
# ---------------------------------------------------------------------------
def pdf_pages_to_chunks(
    pages: list[PdfPage],
    *,
    source_url: str,
    source_id: str = "SRC",
    title: str = "",
    category: str = "",
    trust_tier: str = "",
    last_checked_date: str = "",
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[dict]:
    """Chunk extracted pages into Chroma-ready dicts (reuses chunk_text)."""
    chunk_dicts: list[dict] = []
    running_index = 0

    for page in pages:
        # Give the chunker a heading so each chunk carries page context, then the
        # tables (kept atomic) and the prose body.
        parts = [f"# {title or 'Document'} — Page {page.page_num}"]
        if page.tables_markdown:
            parts.append(page.tables_markdown)
        if page.text:
            parts.append(page.text)
        page_md = "\n\n".join(parts)

        page_chunks = chunk_text(
            page_md,
            source_url=source_url,
            title=title,
            category=category,
            trust_tier=trust_tier,
            last_checked_date=last_checked_date,
            source_id=source_id,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for c in page_chunks:
            is_table = c.chunk_type == "table"
            chunk_dicts.append({
                "chunk_id": f"{source_id}-p{page.page_num:03d}-{running_index:04d}",
                "text": c.text,
                "metadata": {
                    "source_url": source_url,
                    "source_id": source_id,
                    "title": title,
                    "category": category,
                    "trust_tier": trust_tier,
                    "last_checked_date": last_checked_date,
                    "chunk_index": running_index,
                    "chunk_type": c.chunk_type,
                    "page_num": page.page_num,
                    "is_table": is_table,
                    "content_type": "pdf",
                },
            })
            running_index += 1

    return chunk_dicts


# ---------------------------------------------------------------------------
# D) Orchestration (called by ingest.ingest_source router)
# ---------------------------------------------------------------------------
def ingest_pdf(url: str, meta: dict | None = None, collection=None) -> dict:
    """Extract, chunk and upsert a single PDF. Returns an ingest result dict."""
    meta = meta or {}
    try:
        pages = extract_pdf_pages(url)
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "ok": False, "error": f"PDF extract failed: {exc}"}

    if pages is None:
        return {"url": url, "ok": False, "error": "No extractable text (scanned/image PDF)."}

    chunks = pdf_pages_to_chunks(
        pages,
        source_url=url,
        source_id=meta.get("source_id", "SRC"),
        title=meta.get("title", ""),
        category=meta.get("category", ""),
        trust_tier=meta.get("trust_tier", ""),
        last_checked_date=meta.get("last_checked_date", ""),
    )
    if not chunks:
        return {"url": url, "ok": False, "error": "No chunks produced from PDF."}

    if collection is None:
        import chromadb

        from config import CHROMA_DIR, COLLECTION
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(name=COLLECTION)

    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    return {
        "url": url,
        "ok": True,
        "chunks": len(chunks),
        "pages": len(pages),
        "tables": sum(1 for c in chunks if c["metadata"]["is_table"]),
        "stored_total": collection.count(),
    }
