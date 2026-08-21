import unittest

from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.evidence import evaluate_evidence
from app.services.campus_intelligence.specialists import retrieve_registry_records
from app.services.persona import detect_persona


class GovernedRegistrySpecialistTests(unittest.TestCase):
    def test_employment_returns_governed_destinations_not_vacancy_claims(self):
        query = compile_campus_query("What jobs are available at McNeese right now?")
        evidence = retrieve_registry_records(query.original_query, query, limit=8)
        self.assertTrue(evidence)
        self.assertTrue(any(set(item.metadata["source_groups"]) & set(query.required_source_groups) for item in evidence))
        self.assertTrue(all(item.metadata.get("claim_boundary") == "destination_only" for item in evidence))
        self.assertTrue(all("not changing facts" in item.text for item in evidence))

    def test_form_record_preserves_owner_action_and_content_type(self):
        query = compile_campus_query("Where can I find the academic suspension appeal form?")
        evidence = retrieve_registry_records(query.original_query, query, limit=8)
        cap = next(item for item in evidence if item.source_id == "CAP-002")
        result = evaluate_evidence(query, [cap])
        self.assertTrue(result.field_coverage["form"])
        self.assertTrue(result.field_coverage["active_url"])
        self.assertTrue(result.field_coverage["owner"])
        self.assertTrue(result.field_coverage["content_type"])

    def test_calendar_destination_does_not_satisfy_date_claim(self):
        query = compile_campus_query("When does Summer 2026 semester end?")
        evidence = retrieve_registry_records(query.original_query, query, limit=8)
        result = evaluate_evidence(query, evidence)
        self.assertFalse(result.field_coverage["date"])
        self.assertFalse(result.passed)

    def test_undergraduate_is_never_substring_matched_as_graduate(self):
        question = "How do I apply as an international undergraduate student?"
        self.assertEqual(detect_persona(question), "international undergraduate")
        self.assertEqual(
            compile_campus_query(question).audience,
            "prospective_international_undergraduate",
        )



class CapabilityCoverageTruthTests(unittest.TestCase):
    def test_unindexed_calendar_is_not_advertised_as_fully_supported(self):
        from app.services.campus_intelligence.registry import capability_snapshot

        snapshot = capability_snapshot(runtime={
            "official_web_search_available": True,
            "web_browsing_enabled": True,
        })
        fully_supported = {
            item["domain_id"]
            for item in snapshot["domains_by_status"]["fully_supported"]
        }
        live_official = {
            item["domain_id"]
            for item in snapshot["domains_by_status"]["live_official"]
        }
        self.assertNotIn("academic_calendar", fully_supported)
        self.assertIn("academic_calendar", live_official)
        self.assertIn("academic_calendar", snapshot["downgraded_domains"])

if __name__ == "__main__":
    unittest.main()


