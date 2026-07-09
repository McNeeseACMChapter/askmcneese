"""Observational contract harness for the two HTML-extraction implementations.

There are currently TWO independent copies of the table/list -> Markdown
converters:

- ``backend/app/services/web_search.py`` — used at request time on live pages.
- ``crawler/clean_text.py`` — used offline when building the ChromaDB store.

Sprint 4 does NOT unify them. This harness simply feeds the same HTML snippets
to both and records whether the outputs agree, so a future sprint can decide
whether to merge them into one shared function. The tests are intentionally
non-strict: they PASS whether or not the outputs match, and print any diffs so
the divergence is visible in test output.

Known reasons the two could diverge (kept here for the future decision):
- clean_text handles headings (``#``..``######``) inside ``clean_html`` rather
  than inside the table/list helpers, so heading markers are out of scope here.
- web_search runs extra nav/design-token "garbage" filtering in
  ``_extract_structured_content`` (not in these two helpers).
- The single-column table fallback is phrased differently in each file even
  though it currently produces the same bullet output.

No network or LLM calls are made.
"""

import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

# crawler/ is a sibling of backend/ and is not an installed package, so add it
# to the import path explicitly (repo_root/crawler).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CRAWLER_DIR = _REPO_ROOT / "crawler"
if str(_CRAWLER_DIR) not in sys.path:
    sys.path.insert(0, str(_CRAWLER_DIR))

from app.services.web_search import (
    _table_to_markdown as web_table_to_markdown,
    _list_to_markdown as web_list_to_markdown,
)
import clean_text  # noqa: E402  (crawler module, imported via sys.path above)

crawler_table_to_markdown = clean_text._table_to_markdown
crawler_list_to_markdown = clean_text._list_to_markdown


# --- HTML snippets (hard-coded) -------------------------------------------

TABLE_SNIPPET = """
<table>
  <tr><th>Applicant</th><th>Minimum GPA</th><th>Award</th></tr>
  <tr><td>New Freshman</td><td>3.0</td><td>$1,000/year</td></tr>
  <tr><td>Transfer</td><td>2.5</td><td>$500/year</td></tr>
</table>
"""

SINGLE_COLUMN_TABLE_SNIPPET = """
<table>
  <tr><td>Fall deadline: July 1</td></tr>
  <tr><td>Spring deadline: November 1</td></tr>
</table>
"""

UNORDERED_LIST_SNIPPET = """
<ul>
  <li>Submit the application</li>
  <li>Send official transcripts</li>
  <li>Pay the application fee</li>
</ul>
"""

NESTED_LIST_SNIPPET = """
<ol>
  <li>Apply for admission
    <ul>
      <li>Complete the online form</li>
      <li>Upload transcripts</li>
    </ul>
  </li>
  <li>Apply for scholarships</li>
</ol>
"""


def _first_tag(html: str, name):
    return BeautifulSoup(html, "html.parser").find(name)


class TestHtmlExtractionContract(unittest.TestCase):
    """Compare both implementations; report differences, never enforce equality."""

    def _compare(self, label: str, web_out: str, crawler_out: str) -> None:
        self.assertIsInstance(web_out, str)
        self.assertIsInstance(crawler_out, str)
        if web_out != crawler_out:
            # Observational only: surface the diff so a future sprint can decide
            # whether to unify the two implementations. Do NOT fail the test.
            print(f"\n[HTML-EXTRACTION DIFF] {label}")
            print("  web_search:\n" + "\n".join(f"    {ln}" for ln in web_out.splitlines()))
            print("  clean_text:\n" + "\n".join(f"    {ln}" for ln in crawler_out.splitlines()))

    def test_multi_column_table(self) -> None:
        tag = _first_tag(TABLE_SNIPPET, "table")
        self._compare(
            "multi-column table",
            web_table_to_markdown(tag),
            crawler_table_to_markdown(_first_tag(TABLE_SNIPPET, "table")),
        )

    def test_single_column_table(self) -> None:
        self._compare(
            "single-column table",
            web_table_to_markdown(_first_tag(SINGLE_COLUMN_TABLE_SNIPPET, "table")),
            crawler_table_to_markdown(_first_tag(SINGLE_COLUMN_TABLE_SNIPPET, "table")),
        )

    def test_unordered_list(self) -> None:
        self._compare(
            "unordered list",
            web_list_to_markdown(_first_tag(UNORDERED_LIST_SNIPPET, "ul")),
            crawler_list_to_markdown(_first_tag(UNORDERED_LIST_SNIPPET, "ul")),
        )

    def test_nested_ordered_list(self) -> None:
        self._compare(
            "nested ordered list",
            web_list_to_markdown(_first_tag(NESTED_LIST_SNIPPET, "ol")),
            crawler_list_to_markdown(_first_tag(NESTED_LIST_SNIPPET, "ol")),
        )


if __name__ == "__main__":
    unittest.main()
