"""Requested official action links survive generative omissions."""

from __future__ import annotations

import unittest

from app.services.llm import _missing_action_links_appendix


class TestActionLinkPreservation(unittest.TestCase):
    def test_appends_missing_relevant_form_without_unrelated_links(self) -> None:
        provider = "https://www.mcneese.edu/provider.pdf"
        veterinarian = "https://www.mcneese.edu/veterinarian.pdf"
        chunks = [{
            "text": (
                "Relevant official action links found on this page:\n"
                f"- ESA Healthcare Provider Form: {provider}\n"
                f"- ESA Veterinarian Form: {veterinarian}\n"
                "- Annual Security Reports: https://www.mcneese.edu/security/"
            )
        }]
        answer = f"Use [the provider form]({provider})."

        appendix = _missing_action_links_appendix(
            "Where are the required emotional support animal forms?",
            answer,
            chunks,
        )

        self.assertIn(veterinarian, appendix)
        self.assertNotIn(provider, appendix)
        self.assertNotIn("security", appendix)


if __name__ == "__main__":
    unittest.main()
