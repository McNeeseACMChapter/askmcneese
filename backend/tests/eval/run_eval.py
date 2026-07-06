"""Eval harness — measure whether the pipeline surfaces the key facts.

Runs the RAG pipeline against a small set of golden scholarship questions and
checks that the expected key facts (GPA thresholds, dollar amounts, test-score
cutoffs, deadlines, emails, URLs) actually appear in the output. This turns
"the answer feels better" into a number we can track across pipeline changes.

Modes (``--mode``):
- ``context`` (default): run live web retrieval (expand -> fetch -> rerank) and
  check facts against the RETRIEVED context. Measures ingestion + retrieval,
  needs network but NOT the LLM API key. Best for iterating on the pipeline.
- ``kb``: check facts against the ChromaDB knowledge-base retrieval
  (``retrieve``). Requires a populated ChromaDB (run the crawler ingest first).
- ``answer``: full end-to-end including Claude generation. Requires
  ANTHROPIC_API_KEY. Checks facts against the final answer.

Usage (from repo root):
    python askmcneese/backend/tests/eval/run_eval.py
    python askmcneese/backend/tests/eval/run_eval.py --mode answer
    python askmcneese/backend/tests/eval/run_eval.py --threshold 0.7

Exit code is non-zero if the mean fact-recall is below --threshold, so this can
gate CI.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

# Make the backend package importable: backend/tests/eval/ -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_questions.json"


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, and drop thousands-separators in numbers."""
    text = text.lower()
    text = re.sub(r"(?<=\d),(?=\d)", "", text)  # 2,500 -> 2500
    text = re.sub(r"\s+", " ", text)
    return text


def _fact_matched(fact: dict, haystack_norm: str, haystack_norm_nospace: str) -> bool:
    for variant in fact.get("any_of", []):
        v = _normalize(variant)
        if v in haystack_norm:
            return True
        # Also try a space-insensitive match so "toefl 79" matches "toefl| 79".
        if v.replace(" ", "") in haystack_norm_nospace:
            return True
    return False


def _check(question: dict, haystack: str, urls: list[str]) -> dict:
    haystack_norm = _normalize(haystack)
    haystack_norm_nospace = haystack_norm.replace(" ", "")

    facts = question.get("expected_facts", [])
    matched, missing = [], []
    for fact in facts:
        if _fact_matched(fact, haystack_norm, haystack_norm_nospace):
            matched.append(fact["label"])
        else:
            missing.append(fact["label"])

    url_norm = " ".join(urls).lower().replace(",", "")
    exp_urls = question.get("expected_urls", [])
    url_hits = [u for u in exp_urls if u.lower() in url_norm]

    recall = len(matched) / len(facts) if facts else 0.0
    return {
        "id": question["id"],
        "recall": recall,
        "matched": matched,
        "missing": missing,
        "url_ok": len(url_hits) == len(exp_urls) and bool(exp_urls),
        "expected_urls": exp_urls,
        "url_hits": url_hits,
    }


def _fail(question: dict, error: str) -> dict:
    return {"id": question["id"], "recall": 0.0, "matched": [],
            "missing": [f["label"] for f in question.get("expected_facts", [])],
            "url_ok": False, "expected_urls": question.get("expected_urls", []),
            "url_hits": [], "error": error}


async def _run_one(question: dict, mode: str) -> dict:
    q = question["question"]

    if mode == "kb":
        from app.services.retrieval import retrieve

        chunks = retrieve(q, top_k=8)
        if not chunks:
            return _fail(question, "No chunks from ChromaDB (run crawler ingest first?).")
        haystack = "\n\n".join(c.text for c in chunks)
        return _check(question, haystack, [c.source_url for c in chunks])

    # context / answer share the same live web retrieval.
    from app.services.web_search import search_and_fetch, pages_to_context

    pages = await search_and_fetch(q, max_pages=6)
    if not pages:
        return _fail(question, "No pages fetched (network blocked or site down?).")
    context, _ = pages_to_context(pages)
    urls = [p.url for p in pages]

    if mode == "context":
        return _check(question, context, urls)

    # answer mode: full generation
    from app.services.llm import generate_answer
    from app.services.persona import detect_persona

    persona = detect_persona(q, question.get("persona_history"))
    chunk_dicts = [
        {"text": p.content, "title": p.title, "source_url": p.url} for p in pages
    ]
    try:
        haystack = generate_answer(q, chunk_dicts, persona=persona).answer
    except Exception as e:  # noqa: BLE001
        return _fail(question, f"Generation failed: {e}")
    return _check(question, haystack, urls)


async def _main_async(args) -> int:
    questions = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    if args.id:
        questions = [q for q in questions if q["id"] == args.id]
        if not questions:
            print(f"No golden question with id={args.id!r}")
            return 2

    results = []
    for q in questions:
        results.append(await _run_one(q, args.mode))

    print(f"\n=== AskMcNeese eval — mode={args.mode} ===\n")
    total = 0.0
    for r in results:
        total += r["recall"]
        status = "PASS" if r["recall"] >= args.threshold else "FAIL"
        print(f"[{status}] {r['id']}: fact recall {r['recall']*100:.0f}% "
              f"({len(r['matched'])}/{len(r['matched']) + len(r['missing'])})")
        if r.get("error"):
            print(f"        ! {r['error']}")
        if r["missing"]:
            print(f"        missing: {', '.join(r['missing'])}")
        url_flag = "ok" if r["url_ok"] else f"MISSING {set(r['expected_urls']) - set(r['url_hits'])}"
        print(f"        expected source url: {url_flag}")
        print()

    mean = total / len(results) if results else 0.0
    print(f"Mean fact recall: {mean*100:.1f}%  (threshold {args.threshold*100:.0f}%)")
    return 0 if mean >= args.threshold else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="AskMcNeese pipeline eval harness")
    parser.add_argument("--mode", choices=["context", "kb", "answer"], default="context")
    parser.add_argument("--threshold", type=float, default=0.8,
                        help="Minimum mean fact recall to pass (0-1)")
    parser.add_argument("--id", help="Run only the golden question with this id")
    args = parser.parse_args()
    sys.exit(asyncio.run(_main_async(args)))


if __name__ == "__main__":
    main()
