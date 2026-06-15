"""BE-02 — Clean text extractor.

Strip nav/header/footer/scripts/styles and other non-content noise, normalize
whitespace, and keep headings (prefixed with Markdown-style hashes so structure
survives into the chunks).
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_STRIP_TAGS = ["script", "style", "noscript", "nav", "header", "footer",
               "aside", "form", "svg", "iframe", "button"]
_HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "##### ", "h6": "###### "}


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    for level, prefix in _HEADINGS.items():
        for node in soup.find_all(level):
            text = node.get_text(" ", strip=True)
            node.replace_with(f"\n\n{prefix}{text}\n\n")

    text = soup.get_text("\n")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        raw = open(sys.argv[1], encoding="utf-8").read()
        out = clean_html(raw)
        print(out[:2000])
        print(f"\n--- {len(out)} chars of clean text ---")
