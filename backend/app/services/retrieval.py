"""ChromaDB retrieval service.

Reads chunks from the same ChromaDB collection the crawler writes to.
Backend is READ-ONLY — never writes to ChromaDB.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "crawler/chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "askmcneese_sources")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_url: str
    title: str
    category: str
    trust_tier: str
    score: float


def _get_collection():
    """Get the ChromaDB collection (read-only access)."""
    db_path = Path(__file__).resolve().parents[3] / CHROMA_DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(
            f"ChromaDB not found at {db_path}. Run crawler ingest first."
        )
    client = chromadb.PersistentClient(path=str(db_path))
    return client.get_or_create_collection(name=CHROMA_COLLECTION)


def search_chunks(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """
    Semantic search for chunks matching the question with keyword reranking.
    
    Args:
        question: The user's question text
        top_k: Number of results to return (default from env)
    
    Returns:
        List of RetrievedChunk with text, metadata, and similarity score
    """
    if top_k is None:
        top_k = RETRIEVAL_TOP_K
    
    try:
        collection = _get_collection()
    except FileNotFoundError:
        return []
    
    if collection.count() == 0:
        return []
    
    # Fetch more chunks than needed for reranking
    fetch_k = min(max(top_k * 3, 8), collection.count())
    
    results = collection.query(
        query_texts=[question],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"],
    )
    
    if not results["ids"] or not results["ids"][0]:
        return []
    
    # Extract keywords from question for reranking
    question_lower = question.lower()
    keywords = _extract_keywords(question_lower)
    
    chunks: list[RetrievedChunk] = []
    ids = results["ids"][0]
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []
    
    for i, chunk_id in enumerate(ids):
        meta = metas[i] if i < len(metas) else {}
        distance = distances[i] if i < len(distances) else 1.0
        text = docs[i] if i < len(docs) else ""
        
        # Base score from embedding similarity
        embed_score = max(0, 1 - distance)
        
        # Keyword reranking score
        keyword_score = _keyword_score(text.lower(), keywords)
        
        # Combined score (embedding + keywords)
        final_score = embed_score * 0.6 + keyword_score * 0.4
        
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=text,
                source_url=meta.get("source_url", ""),
                title=meta.get("title", "Unknown Source"),
                category=meta.get("category", ""),
                trust_tier=meta.get("trust_tier", ""),
                score=round(final_score, 3),
            )
        )
    
    # Sort by combined score and return top_k
    chunks.sort(key=lambda c: -c.score)
    return chunks[:top_k]


def _extract_keywords(question: str) -> list[str]:
    """Extract meaningful keywords from question."""
    # Common question words to ignore
    stopwords = {
        "what", "when", "where", "which", "who", "how", "why",
        "is", "are", "was", "were", "the", "a", "an", "to", "for",
        "of", "in", "on", "at", "by", "with", "from", "about",
        "can", "could", "would", "should", "does", "do", "did",
        "have", "has", "had", "be", "been", "being", "will",
        "there", "their", "they", "this", "that", "these", "those",
        "my", "your", "his", "her", "its", "our", "i", "me", "you"
    }
    
    words = question.lower().split()
    keywords = [w.strip("?.,!") for w in words if len(w) > 2 and w not in stopwords]
    
    # Add related terms for common queries
    expansions = {
        "deadline": ["deadline", "deadlines", "august", "december", "may", "date", "dates", "application"],
        "application": ["application", "apply", "deadline", "admission", "admissions"],
        "admission": ["admission", "admissions", "apply", "application", "requirements"],
        "cost": ["cost", "fee", "fees", "tuition", "price", "financial"],
        "financial": ["financial", "aid", "scholarship", "scholarships", "fafsa"],
        "requirement": ["requirement", "requirements", "required", "need", "gpa", "sat", "act"],
    }
    
    expanded = set(keywords)
    for kw in keywords:
        for base, related in expansions.items():
            if base in kw or kw in related:
                expanded.update(related)
    
    return list(expanded)


def _keyword_score(text: str, keywords: list[str]) -> float:
    """Score text by keyword presence."""
    if not keywords:
        return 0.0
    
    matches = sum(1 for kw in keywords if kw in text)
    
    # Bonus for having multiple keywords close together (likely relevant section)
    if matches >= 3:
        return min(1.0, matches / len(keywords) + 0.2)
    
    return matches / len(keywords)


def get_collection_stats() -> dict:
    """Get statistics about the ChromaDB collection."""
    try:
        collection = _get_collection()
        return {
            "collection": CHROMA_COLLECTION,
            "count": collection.count(),
            "path": str(Path(__file__).resolve().parents[3] / CHROMA_DB_PATH),
        }
    except FileNotFoundError as e:
        return {"error": str(e), "count": 0}
