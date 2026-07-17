"""Allowlist / SSRF / companion authorization tests."""

from __future__ import annotations

import unittest

from app.services.rccs.allowlist import is_allowed_url, normalize_url, reject_reason
from app.services.rccs.models import CompanionSource, RetrievalPlan


def _plan(**kwargs) -> RetrievalPlan:
    base = dict(
        use_kb=True,
        use_official_live=True,
        companion_source_ids=["SRC-C-RMP-001"],
        official_source_ids=[],
        search_queries=[],
        entity_queries=[],
        freshness="stable",
        max_results_per_channel=5,
        reason="test",
        companion_categories=["student_rating"],
        primary_intent="faculty_ratings",
    )
    base.update(kwargs)
    return RetrievalPlan(**base)


def _rmp() -> CompanionSource:
    return CompanionSource(
        source_id="SRC-C-RMP-001",
        name="RMP",
        description="",
        content_type="external_companion",
        source_tier="C",
        category="student_rating",
        base_url="https://www.ratemyprofessors.com/school/587",
        url_template="",
        domain_allowlist=["ratemyprofessors.com", "www.ratemyprofessors.com"],
        query_template="",
        fetch_mode="structured_adapter",
        trust_level="student_rating",
        entity_types=["faculty_or_staff"],
        topic_keywords=set(),
        aliases=[],
        enabled=True,
        allowed_for_ai_retrieval=True,
        allow_chroma_ingest=False,
        citation_label="Student ratings",
    )


class TestAllowlist(unittest.TestCase):
    def test_official_mcneese_accepted(self):
        self.assertTrue(
            is_allowed_url("https://www.mcneese.edu/admissions/", channel="official_live")
        )

    def test_catalog_accepted(self):
        self.assertTrue(
            is_allowed_url(
                "https://catalog.mcneese.edu/content.php?catoid=93&navoid=7894",
                channel="official_live",
            )
        )

    def test_rmp_accepted_only_with_companion_plan(self):
        url = "https://www.ratemyprofessors.com/search/professors/587?q=Menon"
        self.assertFalse(is_allowed_url(url, channel="official_live"))
        self.assertTrue(
            is_allowed_url(
                url,
                channel="companion",
                plan=_plan(),
                matched_companions=[_rmp()],
            )
        )

    def test_rmp_rejected_for_tuition_plan(self):
        url = "https://www.ratemyprofessors.com/search/professors/587?q=Menon"
        plan = _plan(
            companion_source_ids=[],
            companion_categories=[],
            primary_intent="admissions_policy",
        )
        self.assertFalse(
            is_allowed_url(
                url,
                channel="companion",
                plan=plan,
                matched_companions=[_rmp()],
            )
        )

    def test_random_external_rejected(self):
        self.assertFalse(
            is_allowed_url("https://evil.example.com/page", channel="official_live")
        )
        self.assertFalse(
            is_allowed_url(
                "https://evil.example.com/page",
                channel="companion",
                plan=_plan(),
                matched_companions=[_rmp()],
            )
        )

    def test_user_supplied_domain_does_not_authorize(self):
        # Prompt text is irrelevant — authorization is registry/plan only
        self.assertFalse(
            is_allowed_url("https://totally-unrelated.edu", channel="companion", plan=_plan())
        )

    def test_private_ip_rejected(self):
        self.assertFalse(is_allowed_url("http://127.0.0.1/admin", channel="official_live"))
        self.assertFalse(is_allowed_url("http://169.254.169.254/latest", channel="official_live"))
        self.assertFalse(is_allowed_url("http://192.168.1.10/", channel="official_live"))
        self.assertIn(reject_reason("http://127.0.0.1/"), {"private_or_local", "not_authorized", "invalid"})

    def test_file_scheme_rejected(self):
        self.assertFalse(is_allowed_url("file:///etc/passwd", channel="official_live"))

    def test_disabled_companion_rejected(self):
        disabled = _rmp()
        disabled.enabled = False
        url = "https://www.ratemyprofessors.com/professor/1"
        self.assertFalse(
            is_allowed_url(
                url,
                channel="companion",
                plan=_plan(),
                matched_companions=[disabled],
            )
        )

    def test_one_companion_does_not_unlock_all_external(self):
        url = "https://instagram.com/someorg"
        self.assertFalse(
            is_allowed_url(
                url,
                channel="companion",
                plan=_plan(companion_categories=["student_rating"]),
                matched_companions=[_rmp()],
            )
        )

    def test_normalize_strips_tracking(self):
        n = normalize_url("https://www.mcneese.edu/admissions/?utm_source=x#frag")
        self.assertTrue(n.startswith("https://www.mcneese.edu/admissions"))
        self.assertNotIn("utm_source", n)
        self.assertNotIn("#", n)


if __name__ == "__main__":
    unittest.main()
