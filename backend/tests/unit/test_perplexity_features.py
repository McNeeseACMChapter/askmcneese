"""Smoke tests for Perplexity embeddings helpers (no live API)."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.perplexity_embeddings import _decode_embedding, cosine_similarity


class TestPerplexityEmbedHelpers(unittest.TestCase):
    def test_cosine_identical(self):
        v = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=5)

    def test_decode_float_list(self):
        self.assertEqual(_decode_embedding([1, 2, 3.5]), [1.0, 2.0, 3.5])


class TestQueryRewriteOffline(unittest.TestCase):
    def test_rewrite_off(self):
        with patch("app.services.query_rewrite.rewrite_enabled", return_value=False):
            from app.services.query_rewrite import rewrite_question

            r = rewrite_question("Who is Dr Menon?", use_web_search=True)
            self.assertEqual(r.rewritten, "Who is Dr Menon?")
            self.assertEqual(r.provider, "off")


if __name__ == "__main__":
    unittest.main()
