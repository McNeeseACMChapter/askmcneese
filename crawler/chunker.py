"""BE-03 — Structure-aware chunker.

Splits clean (Markdown) text into retrieval chunks with these rules:

- **Tables** (Markdown ``| ... |`` blocks) and **lists** (``-`` / ``1.`` blocks)
  are kept **intact as a single chunk regardless of size**. Splitting a GPA/award
  table or an eligibility list across chunks is what made answers lose the link
  between, say, "GPA 3.5+" and "$1,750".
- **Prose** paragraphs are packed together up to ``chunk_size`` tokens and only
  then split with a sliding window (``overlap`` tokens) — the classic behavior.
- Every chunk is prefixed with its **heading context** (the enclosing ``#``
  headings) so a table under "First Time Freshmen" carries that label with it.

Each chunk records its ``chunk_type`` (prose / table / list) so downstream
retrieval/reranking can prefer structured chunks for fact-heavy questions.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import tokenizer_util

CHUNK_SIZE = 300
OVERLAP = 50
# Structured blocks are kept whole; this only guards against a pathological
# single block (e.g. a giant nav list that slipped through) ballooning a chunk.
MAX_STRUCTURED_TOKENS = 1200

_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
_LIST_LINE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S")
_HEADING_LINE = re.compile(r"^\s*#{1,6}\s+\S")


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    text: str
    source_url: str
    title: str
    category: str
    trust_tier: str
    last_checked_date: str
    chunk_type: str = "prose"


def _block_type(line: str) -> str:
    if _HEADING_LINE.match(line):
        return "heading"
    if _TABLE_LINE.match(line):
        return "table"
    if _LIST_LINE.match(line):
        return "list"
    return "prose"


def _split_blocks(text: str) -> list[tuple[str, str]]:
    """Group raw lines into typed blocks: heading / table / list / prose."""
    lines = text.split("\n")
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue

        kind = _block_type(stripped)

        if kind == "heading":
            blocks.append(("heading", stripped))
            i += 1
            continue

        if kind == "table":
            buf = []
            while i < n and _TABLE_LINE.match(lines[i].strip() or "\u0000"):
                buf.append(lines[i].strip())
                i += 1
            blocks.append(("table", "\n".join(buf)))
            continue

        if kind == "list":
            buf = []
            while i < n:
                s = lines[i].strip()
                if not s:
                    break
                # Continue the list on list markers or indented continuation lines.
                if _LIST_LINE.match(s) or lines[i].startswith(("  ", "\t")):
                    buf.append(lines[i].rstrip())
                    i += 1
                else:
                    break
            blocks.append(("list", "\n".join(buf)))
            continue

        # Prose paragraph: accumulate until a blank line or a structural line.
        buf = []
        while i < n:
            s = lines[i].strip()
            if not s or _block_type(s) != "prose":
                break
            buf.append(s)
            i += 1
        blocks.append(("prose", " ".join(buf)))

    return blocks


def _heading_prefix(stack: list[tuple[int, str]]) -> str:
    return "\n".join(text for _, text in stack)


def _update_heading_stack(stack: list[tuple[int, str]], heading: str) -> None:
    level = len(heading) - len(heading.lstrip("#"))
    while stack and stack[-1][0] >= level:
        stack.pop()
    stack.append((level, heading))


def _window_split(tokens: list, chunk_size: int, overlap: int) -> list[list]:
    step = max(1, chunk_size - overlap)
    windows: list[list] = []
    for start in range(0, len(tokens), step):
        window = tokens[start:start + chunk_size]
        if not window:
            break
        windows.append(window)
        if start + chunk_size >= len(tokens):
            break
    return windows


def chunk_text(
    text: str,
    *,
    source_url: str,
    title: str,
    category: str,
    trust_tier: str,
    last_checked_date: str,
    source_id: str = "SRC",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[Chunk]:
    if not text or not text.strip():
        return []

    blocks = _split_blocks(text)
    # Seed the heading stack with the page title as a top-level heading so EVERY
    # chunk — including a table buried under sub-headings like "Transfer
    # Students" — carries the page topic (e.g. "International Scholarships").
    # Without this, fact tables embed with no page context and lose retrieval to
    # lexically-closer but wrong pages.
    heading_stack: list[tuple[int, str]] = []
    if title and title.strip():
        heading_stack.append((1, f"# {title.strip()}"))
    chunks: list[Chunk] = []
    index = 0

    # Buffer of prose blocks (as text) pending emission.
    prose_buf: list[str] = []
    prose_tokens = 0

    def _make(chunk_str: str, chunk_type: str) -> None:
        nonlocal index
        chunk_str = chunk_str.strip()
        if not chunk_str:
            return
        chunks.append(
            Chunk(
                chunk_id=f"{source_id}-{index:04d}",
                chunk_index=index,
                text=chunk_str,
                source_url=source_url,
                title=title,
                category=category,
                trust_tier=trust_tier,
                last_checked_date=last_checked_date,
                chunk_type=chunk_type,
            )
        )
        index += 1

    def _flush_prose() -> None:
        nonlocal prose_buf, prose_tokens
        if not prose_buf:
            return
        prefix = _heading_prefix(heading_stack)
        body = "\n\n".join(prose_buf)
        tokens = tokenizer_util.encode(body)
        if len(tokens) <= chunk_size:
            _make(f"{prefix}\n\n{body}" if prefix else body, "prose")
        else:
            for window in _window_split(tokens, chunk_size, overlap):
                piece = tokenizer_util.decode(window).strip()
                _make(f"{prefix}\n\n{piece}" if prefix else piece, "prose")
        prose_buf = []
        prose_tokens = 0

    for kind, content in blocks:
        if kind == "heading":
            # A heading starts a new section: flush pending prose first.
            _flush_prose()
            _update_heading_stack(heading_stack, content)
            continue

        if kind in ("table", "list"):
            _flush_prose()
            prefix = _heading_prefix(heading_stack)
            block_text = f"{prefix}\n\n{content}" if prefix else content
            tokens = tokenizer_util.encode(block_text)
            if len(tokens) > MAX_STRUCTURED_TOKENS:
                # Pathologically large: window-split but keep whole rows/items.
                for window in _window_split(tokens, MAX_STRUCTURED_TOKENS, 0):
                    piece = tokenizer_util.decode(window).strip()
                    _make(piece, kind)
            else:
                _make(block_text, kind)
            continue

        # prose block
        block_tokens = tokenizer_util.count_tokens(content)
        if prose_tokens + block_tokens > chunk_size and prose_buf:
            _flush_prose()
        prose_buf.append(content)
        prose_tokens += block_tokens

    _flush_prose()
    return chunks


def chunk_to_dict(chunk: Chunk) -> dict:
    return asdict(chunk)
