from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CRAWLER = ROOT / "crawler"
if str(CRAWLER) not in sys.path:
    sys.path.insert(0, str(CRAWLER))

from governed_registry import assign_source_groups, load_governed_registry  # noqa: E402
from index_manifest import IndexManifest, IndexManifestRecord  # noqa: E402


class TestGovernedRegistry(unittest.TestCase):
    def test_every_eligible_source_has_capability_assignment(self):
        sources = load_governed_registry()
        self.assertGreater(len(sources), 4000)
        self.assertTrue(all(source.source_id for source in sources))
        self.assertTrue(all(source.source_group_ids for source in sources))

    def test_broad_ecosystem_category_is_not_routing_evidence(self):
        groups = assign_source_groups({
            "source_id": "TEST-1",
            "source_name": "A page with no topical title",
            "url": "https://www.mcneese.edu/example-neutral-page/",
            "category": "academics|admissions|aid|campus|directory|events|policies|research",
            "notes": "",
        })
        self.assertEqual(groups, ["general_official"])


class TestIndexManifest(unittest.TestCase):
    def test_manifest_round_trip_distinguishes_registered_and_indexed(self):
        path = ROOT / "knowledge" / ".index_manifest_test.json"
        try:
            manifest = IndexManifest(path)
            manifest.update(IndexManifestRecord(
                source_id="SRC-A",
                url="https://www.mcneese.edu/a/",
                source_group_ids=["official_admissions"],
                registry_status="allowed",
                content_type="html",
            ))
            manifest.update(IndexManifestRecord(
                source_id="SRC-B",
                url="https://www.mcneese.edu/b/",
                source_group_ids=["official_calendar"],
                registry_status="allowed",
                content_type="html",
                fetch_status="indexed",
                chunk_count=4,
                collection="askmcneese_sources",
            ))
            manifest.save()
            loaded = IndexManifest(path)
            summary = loaded.summary()
            self.assertEqual(summary["registered_sources"], 2)
            self.assertEqual(summary["indexed_sources"], 1)
            self.assertEqual(summary["total_chunks"], 4)
            self.assertEqual(summary["by_source_group"]["official_calendar"]["indexed"], 1)
        finally:
            path.unlink(missing_ok=True)
            path.with_suffix(path.suffix + ".tmp").unlink(missing_ok=True)
    def test_repository_manifest_exposes_real_coverage_gap(self):
        path = ROOT / "knowledge" / "index_manifest.json"
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        summary = data["summary"]
        self.assertGreater(summary["registered_sources"], summary["indexed_sources"])
        self.assertEqual(summary["total_chunks"], 1500)
        self.assertIn("by_source_group", summary)


if __name__ == "__main__":
    unittest.main()

