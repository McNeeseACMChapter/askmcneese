"""Task 4E - Smoke test for the PDF ingest pipeline.

Runs ``extract_pdf_pages`` + ``pdf_pages_to_chunks`` on a real McNeese PDF
(picked from ``knowledge/discovered_pdfs.csv`` if present, else a known-good
default) and prints sample chunks showing the table-vs-prose split.

Does NOT write to ChromaDB - it only exercises extraction and chunking.

    python askmcneese/crawler/test_pdf_ingest.py
    python askmcneese/crawler/test_pdf_ingest.py <pdf_url_or_path>
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from ingest_pdf import extract_pdf_pages, pdf_pages_to_chunks  # noqa: E402

DISCOVERED = _HERE.parents[0] / "knowledge" / "discovered_pdfs.csv"
DEFAULT_PDF = (
    "https://www.mcneese.edu/wp-content/uploads/2025/09/Annual-Safety-Report.Oct2024.pdf"
)


def pick_pdfs(n: int = 3) -> list[str]:
    if not DISCOVERED.exists():
        return [DEFAULT_PDF]
    urls: list[str] = []
    with DISCOVERED.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("validation_status") == "ok":
                urls.append(row["pdf_url"])
            if len(urls) >= n:
                break
    return urls or [DEFAULT_PDF]


def _safe(text: str, limit: int = 280) -> str:
    return text.replace("\n", " \\n ")[:limit].encode("ascii", "replace").decode("ascii")


def run_one(url: str) -> None:
    print("=" * 100)
    print("PDF:", url)
    pages = extract_pdf_pages(url)
    if pages is None:
        print("  -> No extractable text (scanned/image PDF). Skipped.")
        return
    n_tables = sum(1 for p in pages if p.tables_markdown)
    print(f"  pages={len(pages)}  pages_with_tables={n_tables}")

    chunks = pdf_pages_to_chunks(
        pages,
        source_url=url,
        source_id="TEST",
        title=Path(url).stem[:60],
        category="pdf_test",
        trust_tier="High",
        last_checked_date="2026-07-05",
    )
    tables = [c for c in chunks if c["metadata"]["is_table"]]
    prose = [c for c in chunks if not c["metadata"]["is_table"]]
    print(f"  chunks={len(chunks)}  table_chunks={len(tables)}  prose_chunks={len(prose)}")

    show = (tables[:3] + prose[:7])[:10]
    for i, c in enumerate(show):
        m = c["metadata"]
        print(f"\n  --- chunk {i} [type={m['chunk_type']} page={m['page_num']} "
              f"is_table={m['is_table']}] id={c['chunk_id']}")
        print("     ", _safe(c["text"]))


def main() -> int:
    urls = sys.argv[1:] or pick_pdfs(3)
    for url in urls:
        try:
            run_one(url)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR on {url}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
