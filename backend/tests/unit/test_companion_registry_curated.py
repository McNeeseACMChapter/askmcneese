"""Curated McNeese-affiliated companion registry + html_fetch adapter."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.rccs.adapters import HtmlFetchAdapter
from app.services.rccs.companion_registry import (
    clear_companion_cache,
    get_companion,
    load_companions,
    match_companions,
)
from app.services.rccs.models import RetrievalPlan


def _plan(**kwargs) -> RetrievalPlan:
    base = dict(
        use_kb=True,
        use_official_live=True,
        companion_source_ids=[],
        official_source_ids=[],
        search_queries=[],
        entity_queries=[],
        freshness="stable",
        max_results_per_channel=5,
        reason="test",
        companion_categories=["social"],
        primary_intent="social_profile",
        allow_open_web=True,
        browse_social=True,
        max_pages_to_open=3,
    )
    base.update(kwargs)
    return RetrievalPlan(**base)


class TestCuratedCompanions(unittest.TestCase):
    def setUp(self) -> None:
        clear_companion_cache()

    def tearDown(self) -> None:
        clear_companion_cache()

    def test_user_provided_companions_enabled(self):
        expected = {
            "SRC-C-FB-MCNEESE-001": "https://www.facebook.com/McNeeseStateU/",
            "SRC-C-FB-ENCS-001": "https://www.facebook.com/McNeeseENCS/",
            "SRC-C-FB-NSA-001": "https://www.facebook.com/nsa.mcneese/",
            "SRC-C-IG-NSA-001": "https://www.instagram.com/nsamcneese/",
            "SRC-C-PRESENCE-001": "https://mcneese.presence.io/organizations",
        }
        for sid, url in expected.items():
            src = get_companion(sid)
            self.assertIsNotNone(src, sid)
            assert src is not None
            self.assertTrue(src.enabled)
            self.assertTrue(src.allowed_for_ai_retrieval)
            if sid == "SRC-C-PRESENCE-001":
                self.assertEqual(src.fetch_mode, "structured_adapter")
            else:
                self.assertEqual(src.fetch_mode, "html_fetch")
            self.assertTrue(src.base_url.rstrip("/").startswith(url.rstrip("/")))

    def test_nsa_aliases_rank_curated_over_platform_hub(self):
        matched = match_companions(
            "nepalese student association facebook",
            categories=["social"],
            max_sources=8,
        )
        ids = [m.source_id for m in matched]
        self.assertIn("SRC-C-FB-NSA-001", ids)
        # Curated NSA should outrank generic Facebook search hub when present
        if "SRC-C-FACEBOOK-001" in ids:
            self.assertLess(ids.index("SRC-C-FB-NSA-001"), ids.index("SRC-C-FACEBOOK-001"))

    def test_load_has_multiple_html_fetch_companions(self):
        html = [c for c in load_companions() if c.enabled and c.fetch_mode == "html_fetch"]
        self.assertGreaterEqual(len(html), 10)


class TestHtmlFetchAdapter(unittest.IsolatedAsyncioTestCase):
    async def test_html_fetch_web_mode_fetches_content(self):
        src = get_companion("SRC-C-FB-ENCS-001")
        self.assertIsNotNone(src)
        assert src is not None
        adapter = HtmlFetchAdapter()
        fake = type(
            "P",
            (),
            {"success": True, "content": "ENCS Engineering Facebook page " * 5, "title": "ENCS"},
        )()
        with patch(
            "app.services.web_search.fetch_page_content",
            new=AsyncMock(return_value=fake),
        ):
            ev = await adapter.retrieve("ENCS facebook", None, src, _plan())
        self.assertEqual(len(ev), 1)
        self.assertFalse(ev[0].is_link_only)
        self.assertTrue(ev[0].metadata.get("page_fetched"))

    async def test_non_web_mode_stays_link_only(self):
        src = get_companion("SRC-C-FB-ENCS-001")
        self.assertIsNotNone(src)
        assert src is not None
        adapter = HtmlFetchAdapter()
        ev = await adapter.retrieve(
            "ENCS facebook",
            None,
            src,
            _plan(allow_open_web=False, browse_social=False, max_pages_to_open=0),
        )
        self.assertEqual(len(ev), 1)
        self.assertTrue(ev[0].is_link_only)


if __name__ == "__main__":
    unittest.main()
