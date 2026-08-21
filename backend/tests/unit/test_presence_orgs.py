"""Presence / Involve org directory adapter tests."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.rccs.adapters import PresenceOrgAdapter
from app.services.rccs.companion_registry import clear_companion_cache, get_companion
from app.services.rccs.models import DetectedEntity, RetrievalPlan
from app.services.rccs.presence_orgs import (
    PresenceOrgSummary,
    clear_presence_cache,
    detail_from_api,
    match_organizations,
    score_org,
    strip_html,
)


def _plan(**kwargs) -> RetrievalPlan:
    base = dict(
        use_kb=False,
        use_official_live=False,
        companion_source_ids=["SRC-C-PRESENCE-001"],
        official_source_ids=["SRC-029"],
        search_queries=[],
        entity_queries=[],
        freshness="stable",
        max_results_per_channel=5,
        reason="test",
        companion_categories=["social"],
        primary_intent="organization_identity",
        allow_open_web=False,
        browse_social=True,
        max_pages_to_open=0,
    )
    base.update(kwargs)
    return RetrievalPlan(**base)


class TestPresenceHelpers(unittest.TestCase):
    def test_strip_html(self):
        self.assertIn("Nepalese", strip_html("<p>The <b>Nepalese</b> club</p>"))

    def test_detail_builds_facebook_url(self):
        d = detail_from_api(
            {
                "name": "Nepalese Student Association",
                "uri": "nepalese-student-association",
                "description": "About NSA",
                "facebook": "nsamcneese",
                "twitter": "",
                "categories": ["Multicultural"],
            }
        )
        assert d is not None
        self.assertEqual(
            d.portal_url,
            "https://mcneese.presence.io/organization/nepalese-student-association",
        )
        self.assertIn(
            ("Facebook", "https://www.facebook.com/nsamcneese"),
            d.social_urls,
        )

    def test_score_and_match_nsa(self):
        orgs = [
            PresenceOrgSummary(
                name="Nepalese Student Association",
                uri="nepalese-student-association",
                description="NSA at McNeese",
                categories=["Multicultural"],
            ),
            PresenceOrgSummary(
                name="Association for Computing Machinery",
                uri="association-for-computing-machinery",
                description="ACM",
                categories=["Academic"],
            ),
        ]
        self.assertGreater(
            score_org(orgs[0], "Nepalese Student Association facebook", "NSA"),
            score_org(orgs[1], "Nepalese Student Association facebook", "NSA"),
        )
        matched = match_organizations(
            orgs,
            "Tell me about the Nepalese Student Association",
            entity_name="Nepalese Student Association",
        )
        self.assertEqual(matched[0][1].uri, "nepalese-student-association")


class TestPresenceAdapter(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        clear_companion_cache()
        clear_presence_cache()

    def tearDown(self) -> None:
        clear_companion_cache()
        clear_presence_cache()

    async def test_adapter_returns_org_detail(self):
        src = get_companion("SRC-C-PRESENCE-001")
        self.assertIsNotNone(src)
        assert src is not None
        self.assertEqual(src.fetch_mode, "structured_adapter")

        summaries = [
            PresenceOrgSummary(
                name="Nepalese Student Association",
                uri="nepalese-student-association",
                description="NSA summary",
                categories=["Multicultural"],
                member_count=76,
            )
        ]
        detail = detail_from_api(
            {
                "name": "Nepalese Student Association",
                "uri": "nepalese-student-association",
                "description": "<p>NSA helps Nepalese students.</p>",
                "facebook": "nsamcneese",
                "twitter": "",
                "regularMeetingLocation": "Drew 220",
                "categories": ["Multicultural"],
                "memberCount": 76,
                "contactName": "Manish Lohani",
            }
        )
        adapter = PresenceOrgAdapter()
        with patch(
            "app.services.rccs.presence_orgs.fetch_organization_list",
            new=AsyncMock(return_value=summaries),
        ), patch(
            "app.services.rccs.presence_orgs.fetch_organization_detail",
            new=AsyncMock(return_value=detail),
        ):
            ev = await adapter.retrieve(
                "Tell me about the Nepalese Student Association at McNeese",
                DetectedEntity(
                    raw_text="Nepalese Student Association",
                    normalized_name="Nepalese Student Association",
                    entity_type="campus_organization",
                ),
                src,
                _plan(),
            )
        self.assertEqual(len(ev), 1)
        self.assertIn("Nepalese Student Association", ev[0].title)
        self.assertIn("facebook.com/nsamcneese", ev[0].text.lower())
        self.assertIn("Drew 220", ev[0].text)
        self.assertFalse(ev[0].is_link_only)
        self.assertEqual(ev[0].metadata.get("presence_mode"), "detail")


if __name__ == "__main__":
    unittest.main()
