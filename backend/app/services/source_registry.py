"""Source registry — curated, approved McNeese URLs for reliable retrieval.

DuckDuckGo scraping is rate-limited and shallow (mostly returns the homepage).
The knowledge/source_registry_seed.csv file contains 30 hand-curated, approved
McNeese pages mapped to topics. We route each query to the most relevant
approved pages using keyword matching, then fetch those pages directly.

This is the reliable primary retrieval path. Live web search supplements it.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class RegistrySource:
    source_id: str
    name: str
    url: str
    category: str
    use_case: str
    keywords: set[str] = field(default_factory=set)


# Extra topic keywords mapped to source IDs. These boost matching beyond the
# words already present in the source name/category/use-case text.
_TOPIC_KEYWORDS: dict[str, set[str]] = {
    "SRC-002": {"admission", "admissions", "apply", "application", "deadline",
                "freshman", "transfer", "enroll", "enrollment", "applicant",
                "how to apply", "requirements", "admit"},
    "SRC-003": {"international", "visa", "immigration", "i-20", "f1", "f-1",
                "sevis", "foreign", "abroad"},
    "SRC-004": {"cost", "costs", "tuition", "fee", "fees", "price", "expensive",
                "estimated", "attendance", "how much", "afford", "net price"},
    "SRC-005": {"financial aid", "fafsa", "aid", "grant", "grants", "loan",
                "loans", "work study", "pell"},
    "SRC-006": {"scholarship", "scholarships", "merit", "award", "awards",
                "endowed", "engineering scholarship"},
    "SRC-031": {"scholarship", "scholarships", "freshman", "freshmen",
                "new student", "incoming", "presidential", "university scholars",
                "john mcneese", "academic excellence", "act", "sat",
                "award", "awards", "merit", "high school", "entering freshman",
                "freshman scholarship", "academic scholarship"},
    "SRC-032": {"scholarship", "scholarships", "continuing", "current student",
                "upperclassman", "upperclassmen", "sophomore", "junior", "senior",
                "renew", "renewal", "academic scholarship application",
                "continuing student", "already enrolled", "award", "awards"},
    "SRC-033": {"scholarship", "scholarships", "international", "international student",
                "international scholarship", "toefl", "ielts", "duolingo",
                "pte", "foreign", "abroad", "transfer", "graduate",
                "award", "awards", "visa"},
    "SRC-007": {"undergraduate", "major", "majors", "degree", "degrees",
                "bachelor", "program", "programs", "minor"},
    "SRC-008": {"graduate", "masters", "master", "phd", "doctoral", "grad school",
                "certificate", "graduate program"},
    "SRC-009": {"online", "distance", "remote", "e-learning", "online program"},
    "SRC-010": {"college", "colleges", "department", "departments", "faculty"},
    "SRC-011": {"catalog", "curriculum", "course", "courses", "policy",
                "requirements", "degree plan"},
    "SRC-012": {"schedule", "calendar", "registration", "final exam", "exam schedule",
                "term", "semester dates", "academic calendar"},
    "SRC-013": {"class search", "class listing", "sections", "seats"},
    "SRC-014": {"student central", "one stop", "transcript", "advising",
                "holds", "grades", "ferpa"},
    "SRC-015": {"registrar", "transcript", "enrollment verification", "withdrawal",
                "graduation", "probation", "records", "grades", "diploma"},
    "SRC-016": {"campus life", "housing", "dorm", "dining", "health", "wellness",
                "student life", "residence", "living on campus", "clubs"},
    "SRC-017": {"map", "maps", "building", "directions", "parking", "where is"},
    "SRC-018": {"research", "grants", "sponsored", "funding"},
    "SRC-019": {"faculty", "staff", "hr", "human resources", "employee"},
    "SRC-020": {"policy", "policies", "governance", "compliance", "procedure"},
    "SRC-021": {"emergency", "closure", "closed", "safety", "weather", "status",
                "hurricane", "alert"},
    "SRC-022": {"consumer information", "disclosure", "disclosures"},
    "SRC-023": {"title ix", "title 9", "harassment", "assault", "reporting",
                "power-based violence"},
    "SRC-024": {"compliance", "civility", "conduct", "report"},
    "SRC-025": {"library", "books", "database", "research help", "interlibrary",
                "study", "librarian"},
    "SRC-026": {"news", "events", "event", "announcement", "today", "happening",
                "what's going on", "whats going on", "calendar of events"},
    "SRC-027": {"bookstore", "textbook", "textbooks", "merch", "merchandise"},
    "SRC-028": {"athletics", "sports", "cowboys", "cowgirls", "football",
                "basketball", "baseball", "tickets", "game", "team", "rodeo"},
    "SRC-029": {"organization", "organizations", "clubs", "engagement",
                "student org", "get involved", "presence"},
    "SRC-030": {"terms of use", "disclaimer", "legal"},
}

# Common English stopwords to ignore when matching.
_STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "to", "in", "on", "at", "for", "and",
    "or", "what", "when", "where", "which", "who", "how", "do", "does", "did",
    "can", "i", "you", "me", "my", "we", "it", "that", "this", "with", "about",
    "from", "as", "be", "will", "would", "should", "could", "have", "has",
    "get", "got", "there", "please", "tell", "give", "want", "need", "know",
    "mcneese", "university", "state", "school", "college",
}


def _registry_path() -> str:
    # backend/app/services/source_registry.py -> repo root -> knowledge/
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    return os.path.join(repo_root, "askmcneese", "knowledge", "source_registry_seed.csv")


@lru_cache(maxsize=1)
def load_registry() -> list[RegistrySource]:
    """Load and cache the approved source registry from CSV."""
    path = _registry_path()
    if not os.path.exists(path):
        # Fallback: try a relative knowledge path
        alt = os.path.join(os.getcwd(), "knowledge", "source_registry_seed.csv")
        path = alt if os.path.exists(alt) else path

    sources: list[RegistrySource] = []
    try:
        # utf-8-sig strips the BOM that Excel prepends to the header row
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = (row.get("Source ID") or "").strip()
                url = (row.get("Source URL") or "").strip()
                allowed = (row.get("Allowed for AI Retrieval") or "").strip().lower()
                if not sid or not url or "yes" not in allowed:
                    continue

                name = (row.get("Source Name") or "").strip()
                category = (row.get("Information Category") or "").strip()
                use_case = (row.get("Primary Use Case") or "").strip()

                # Build keyword set from name/category/use-case + curated topics
                kw: set[str] = set(_TOPIC_KEYWORDS.get(sid, set()))
                for text in (name, category, use_case):
                    for w in text.lower().replace("/", " ").replace(",", " ").split():
                        w = w.strip(".:;()")
                        if len(w) > 3 and w not in _STOPWORDS:
                            kw.add(w)

                sources.append(RegistrySource(
                    source_id=sid,
                    name=name,
                    url=url,
                    category=category,
                    use_case=use_case,
                    keywords=kw,
                ))
    except Exception as e:
        print(f"Registry load error: {e}")
        return []

    return sources


def match_sources(query: str, max_sources: int = 4) -> list[RegistrySource]:
    """Return the most relevant approved sources for a query, ranked by score.

    Always returns at least the admissions + main site as a sensible default
    when nothing else matches, so the assistant has something to read.
    """
    registry = load_registry()
    if not registry:
        return []

    q = query.lower()
    q_words = {w.strip(".:;()?!") for w in q.split() if len(w) > 2}

    scored: list[tuple[int, RegistrySource]] = []
    for src in registry:
        score = 0
        # Multi-word phrase matches (strong signal)
        for kw in src.keywords:
            if " " in kw:
                if kw in q:
                    score += 5
            elif kw in q_words:
                score += 3
        if score > 0:
            scored.append((score, src))

    scored.sort(key=lambda x: -x[0])

    if not scored:
        # Sensible default: main site + admissions overview
        defaults = [s for s in registry if s.source_id in {"SRC-001", "SRC-002"}]
        return defaults[:max_sources]

    return [s for _, s in scored[:max_sources]]
