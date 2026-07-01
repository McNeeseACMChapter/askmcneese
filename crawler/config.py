"""Shared ChromaDB configuration for crawler ingest modules."""

from pathlib import Path

CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION = "askmcneese_sources"
