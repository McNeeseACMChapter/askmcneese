"""BE-02 — Clean text extractor (structure-preserving).

Strip nav/header/footer/scripts/styles and other non-content noise, normalize
whitespace, and keep document structure so it survives into the chunks:

- Headings -> Markdown ``#`` .. ``######``
- HTML tables -> GitHub-flavored Markdown tables (rows/columns stay associated)
- ``<ul>`` / ``<ol>`` -> Markdown bullet / numbered lists

Preserving tables and lists is critical: GPA tiers, dollar amounts, test-score
cutoffs and deadlines live in tables. Flattening them into a vertical stream of
orphaned cell values (the old ``soup.get_text`` behavior) is why answers used to
hedge — the facts were present but no longer associated with each other.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

_STRIP_TAGS = ["script", "style", "noscript", "nav", "header", "footer",
               "aside", "form", "svg", "iframe", "button"]
_HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "##### ", "h6": "###### "}

# Sentinel wrappers so structured blocks survive the later line-level cleanup
# and can be re-normalized without being collapsed into surrounding prose.
_BLOCK_OPEN = "\uE000"
_BLOCK_CLOSE = "\uE001"


def _cell_text(cell: Tag) -> str:
    """Flatten a single table cell to one clean line (pipes escaped)."""
    text = cell.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", "\\|")


def _table_to_markdown(table: Tag) -> str:
    """Convert an HTML table into a GitHub-flavored Markdown table.

    Falls back to a bullet list when the table has no clean rectangular shape
    (common with layout tables) so we never emit a broken Markdown grid.
    """
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False) or tr.find_all(["th", "td"])
        values = [_cell_text(c) for c in cells]
        if any(v for v in values):
            rows.append(values)

    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        return ""

    width = max(len(r) for r in rows)
    if width < 2:
        # Single-column "table" — treat as a list, not a grid.
        items = [r[0] for r in rows if r and r[0].strip()]
        return "\n".join(f"- {it}" for it in items)

    norm = [r + [""] * (width - len(r)) for r in rows]

    header = norm[0]
    if not any(h.strip() for h in header):
        header = [f"Column {i + 1}" for i in range(width)]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in norm[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _list_to_markdown(list_tag: Tag) -> str:
    """Convert a ``<ul>``/``<ol>`` into a Markdown list (one level of nesting)."""
    ordered = list_tag.name == "ol"
    lines: list[str] = []
    idx = 1
    for li in list_tag.find_all("li", recursive=False):
        # Text directly in this <li>, excluding any nested list text.
        parts = []
        for child in li.children:
            if isinstance(child, Tag) and child.name in ("ul", "ol"):
                continue
            text = child.get_text(" ", strip=True) if isinstance(child, Tag) else str(child).strip()
            if text:
                parts.append(text)
        item = re.sub(r"\s+", " ", " ".join(parts)).strip()
        if item:
            lines.append(f"{idx}. {item}" if ordered else f"- {item}")
            idx += 1
        # Nested lists indented under the item.
        for nested in li.find_all(["ul", "ol"], recursive=False):
            for sub in _list_to_markdown(nested).splitlines():
                lines.append("  " + sub)
    return "\n".join(lines)


def _wrap(md: str) -> NavigableString:
    """Wrap a structured block in sentinels + blank lines for safe re-insertion."""
    return NavigableString(f"\n\n{_BLOCK_OPEN}{md}{_BLOCK_CLOSE}\n\n")


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    # Tables first (a table may contain lists we don't want to double-process).
    for table in soup.find_all("table"):
        md = _table_to_markdown(table)
        table.replace_with(_wrap(md) if md else NavigableString(""))

    # Then top-level lists (skip lists already consumed inside a table).
    for list_tag in soup.find_all(["ul", "ol"]):
        if list_tag.find_parent(["ul", "ol"]):
            continue
        md = _list_to_markdown(list_tag)
        list_tag.replace_with(_wrap(md) if md else NavigableString(""))

    for level, prefix in _HEADINGS.items():
        for node in soup.find_all(level):
            text = node.get_text(" ", strip=True)
            node.replace_with(f"\n\n{prefix}{text}\n\n")

    text = soup.get_text("\n")
    return _normalize(text)


def _normalize(text: str) -> str:
    """Collapse whitespace while preserving the lines inside structured blocks."""
    # Pull structured blocks out, clean prose, then stitch blocks back in.
    block_pattern = re.compile(f"{_BLOCK_OPEN}(.*?){_BLOCK_CLOSE}", re.DOTALL)
    blocks: list[str] = []

    def _stash(match: re.Match) -> str:
        blocks.append(match.group(1).strip())
        return f"\n\n{_BLOCK_OPEN}{len(blocks) - 1}{_BLOCK_CLOSE}\n\n"

    text = block_pattern.sub(_stash, text)

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

    def _restore(match: re.Match) -> str:
        return "\n\n" + blocks[int(match.group(1))] + "\n\n"

    cleaned = re.sub(f"{_BLOCK_OPEN}(\\d+){_BLOCK_CLOSE}", _restore, cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        raw = open(sys.argv[1], encoding="utf-8").read()
        out = clean_html(raw)
        print(out[:2000])
        print(f"\n--- {len(out)} chars of clean text ---")
