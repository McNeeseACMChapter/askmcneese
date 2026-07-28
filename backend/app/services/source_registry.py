"""Source registry â€” curated, approved McNeese URLs for reliable retrieval.

DuckDuckGo scraping is rate-limited and shallow (mostly returns the homepage).
The knowledge/source_registry_seed.csv file contains hand-curated, approved
McNeese pages mapped to topics. We route each query to the most relevant
approved pages using keyword matching across the *whole* registry, then fetch
those pages (and matching child leaves) directly.

This is the reliable primary retrieval path. Live web search supplements it.
"""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import urlparse

from app.services.domain_registry import (
    domains_for_question,
    host_matches_domain,
    record_for_url,
    trust_tier_for_url,
)


@dataclass
class RegistrySource:
    source_id: str
    name: str
    url: str
    category: str
    use_case: str
    keywords: set[str] = field(default_factory=set)
    parent_source_id: str = ""
    trust_tier: str = "B"
    crawl_policy: str = "targeted"


@dataclass
class RegistryLeaf:
    parent_source_id: str
    name: str
    url: str
    category: str = ""


@dataclass
class RegistryMatch:
    """Result of matching a question against the whole source registry."""

    sources: list[RegistrySource]
    source_ids: list[str]
    seed_urls: list[str]
    browse_domains: list[str]
    topics: list[str]
    scores: dict[str, int] = field(default_factory=dict)


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
    # Academic class schedule â€” keep distinct from athletics game schedules.
    "SRC-012": {"academic schedule", "class schedule", "registration", "final exam",
                "exam schedule", "term", "semester", "semester dates", "semester end",
                "academic calendar", "course schedule", "register for classes",
                "spring", "summer", "fall", "classes end", "finals"},
    "SRC-013": {"class search", "class listing", "sections", "seats"},
    "SRC-014": {"student central", "one stop", "transcript", "advising",
                "holds", "grades", "ferpa"},
    "SRC-015": {"registrar", "transcript", "enrollment verification", "withdrawal",
                "graduation", "probation", "records", "grades", "diploma"},
    "SRC-016": {"campus life", "dining", "health", "wellness",
                "student life", "clubs", "student success"},
    "SRC-017": {"map", "maps", "building", "directions", "parking", "where is"},
    "SRC-018": {"research", "grants", "sponsored", "funding"},
    "SRC-019": {"faculty", "staff", "hr", "human resources", "employee"},
    "SRC-034": {"faculty", "professor", "professors", "instructor", "instructors",
                "who is", "dr", "doctor", "department chair", "faculty list",
                "faculty directory", "teaching"},
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
    "SRC-027": {"bookstore", "textbook", "textbooks", "merch", "merchandise",
                "cowboy store", "cowboystore"},
    "SRC-028": {"athletics", "sports", "cowboys", "cowgirls", "football",
                "basketball", "baseball", "tickets", "game", "games", "team",
                "rodeo", "softball", "soccer", "volleyball", "tennis", "track",
                "cross country", "roster", "athletic", "schedule"},
    "SRC-035": {"bookstore", "textbook", "textbooks", "merch", "merchandise",
                "cowboy store", "cowboystore", "team store", "graduation",
                "class ring", "apparel", "gear", "under armour"},
    "SRC-036": {"housing", "residence", "res life", "reslife", "dorm", "dorms",
                "residence hall", "apartment", "floor plan", "floor plans",
                "move-in", "move in", "amenities", "living on campus",
                "on campus housing", "student housing", "campus housing",
                "housing application", "apply for housing", "residence life"},
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
    "mcneese", "university", "state", "school", "college", "next",
}


def _normalized_terms(text: str) -> set[str]:
    """Return lightweight singularized terms for lexical source matching."""
    terms: set[str] = set()
    for raw in re.findall(r"[a-z0-9']+", (text or "").lower()):
        if len(raw) <= 2 or raw in _STOPWORDS:
            continue
        term = raw
        if len(term) > 4 and term.endswith("ies"):
            term = f"{term[:-3]}y"
        elif len(term) > 4 and term.endswith("s") and not term.endswith(("ss", "us", "is")):
            term = term[:-1]
        terms.add(term)
    return terms

def _registry_path() -> str:
    """Prefer the full merged registry; fall back to the original seed file."""
    knowledge = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "knowledge")
    )
    configured = (os.getenv("SOURCE_REGISTRY_PATH") or "").strip()
    if configured:
        return os.path.abspath(configured)
    merged = os.path.join(knowledge, "source_registry_merged.csv")
    return merged if os.path.exists(merged) else os.path.join(knowledge, "source_registry_seed.csv")


def _external_pages_path() -> str:
    return os.path.join(os.path.dirname(_registry_path()), "external_site_pages.csv")


def _knowledge_file(name: str) -> str:
    primary = os.path.join(os.path.dirname(_registry_path()), name)
    if os.path.exists(primary):
        return primary
    alt = os.path.join(os.getcwd(), "knowledge", name)
    return alt if os.path.exists(alt) else primary


def _value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def _is_explicitly_allowed(row: dict[str, str]) -> bool:
    allowed = _value(row, "Allowed_for_AI_Retrieval", "Allowed for AI Retrieval").lower()
    return allowed.startswith("yes") or allowed in {"true", "1"}


def _is_auto_allowed_official(row: dict[str, str], url: str) -> bool:
    """Allow public Tier-A pages discovered through official maps/catalog routes.

    Affiliated Tier-B domains still require explicit approval. This keeps source
    expansion useful without allowing an arbitrary external link to authorize a host.
    """
    record = record_for_url(url)
    discovered = _value(row, "discovered_from").lower()
    return bool(
        record
        and record.trust_tier == "A"
        and record.crawl_policy == "public"
        and discovered in {"seed", "sitemap_xml", "catalog_browse", "catalog_inventory"}
    )


@lru_cache(maxsize=1)
def load_registry() -> list[RegistrySource]:
    """Load every governed public source from the merged registry."""
    path = _registry_path()
    if not os.path.exists(path):
        return []

    sources: list[RegistrySource] = []
    seen_source_ids: set[str] = set()
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                sid = _value(row, "source_id", "Source ID")
                url = _value(row, "url", "Source URL")
                if not sid or not url:
                    continue
                if not (_is_explicitly_allowed(row) or _is_auto_allowed_official(row, url)):
                    continue

                # Discovery exports historically reused two curated IDs. Preserve
                # the curated root even when its generated child appears first.
                row_parent_source_id = _value(row, "parent_source_id")
                if sid in _TOPIC_KEYWORDS and row_parent_source_id:
                    sid = f"{sid}--duplicate-{len(sources)}"
                elif sid in seen_source_ids:
                    sid = f"{sid}--duplicate-{len(sources)}"
                seen_source_ids.add(sid)

                name = _value(row, "source_name", "Source Name")
                category = _value(row, "category", "Information Category")
                use_case = _value(row, "Primary Use Case", "notes")
                parent_source_id = row_parent_source_id
                record = record_for_url(url)

                kw: set[str] = set(_TOPIC_KEYWORDS.get(sid, set()))
                searchable = (
                    name,
                    category,
                    use_case,
                    urlparse(url).path.replace("-", " ").replace("_", " "),
                )
                for text in searchable:
                    for word in re.findall(r"[a-z0-9']+", text.lower()):
                        if len(word) > 3 and word not in _STOPWORDS:
                            kw.add(word)
                if sid == "SRC-016":
                    kw -= {"housing", "dorm", "residence", "dorms"}

                sources.append(RegistrySource(
                    source_id=sid,
                    name=name,
                    url=url,
                    category=category,
                    use_case=use_case,
                    keywords=kw,
                    parent_source_id=parent_source_id,
                    trust_tier=trust_tier_for_url(url),
                    crawl_policy=record.crawl_policy if record else "targeted",
                ))
    except Exception as e:
        print(f"Registry load error: {e}")
        return []

    return sources

@lru_cache(maxsize=1)
def load_registry_leaves() -> list[RegistryLeaf]:
    """Return deduplicated child pages from merged and legacy discovery files."""
    leaves: list[RegistryLeaf] = []
    seen: set[str] = set()

    for source in load_registry():
        if not source.parent_source_id:
            continue
        key = source.url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        leaves.append(RegistryLeaf(
            parent_source_id=source.parent_source_id,
            name=source.name,
            url=source.url,
            category=source.category,
        ))

    path = _knowledge_file("external_site_pages.csv")
    if not os.path.exists(path):
        return leaves
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                parent = (row.get("parent_source_id") or "").strip()
                url = (row.get("url") or "").strip()
                key = url.rstrip("/").lower()
                if not parent or not url or key in seen or record_for_url(url) is None:
                    continue
                seen.add(key)
                leaves.append(RegistryLeaf(
                    parent_source_id=parent,
                    name=(row.get("source_name") or "").strip(),
                    url=url,
                    category=(row.get("category") or "").strip(),
                ))
    except Exception as e:
        print(f"Registry leaf load error: {e}")
    return leaves

def get_source(source_id: str) -> RegistrySource | None:
    for src in load_registry():
        if src.source_id == source_id:
            return src
    return None


_ACADEMIC_SCHEDULE_BASE = (
    "https://www.mcneese.edu/about-us/leadership-team/administrative-and-student-affairs/"
    "division-of-administrative-and-student-affairs/student-central/registrar/schedule"
)


def academic_schedule_page_candidates(query: str) -> list[str]:
    """Derive official Registrar term pages from a term/year question.

    This is URL routing, not a canned answer: page content is still fetched and
    cited live. If McNeese changes the route, provider search remains the fallback.
    """
    q = (query or "").lower()
    term_match = re.search(r"\b(spring|summer|fall|winter)\b", q)
    year_match = re.search(r"\b(20\d{2})\b", q)
    if not term_match or not year_match:
        return []
    slug = f"{term_match.group(1)}-{year_match.group(1)}"
    urls = [f"{_ACADEMIC_SCHEDULE_BASE}/{slug}/"]
    if re.search(r"\bfinal(?:s|\s+exam|\s+examination)?\b", q):
        urls.insert(0, f"{_ACADEMIC_SCHEDULE_BASE}/{slug}-final-exam-schedule/")
    return urls


def _score_source(query: str, q_words: set[str], src: RegistrySource) -> int:
    q = query.lower()
    host = (urlparse(src.url).hostname or "").lower()
    academic_calendar = any(
        cue in q
        for cue in ("semester", "academic calendar", "classes end", "final exam", "finals")
    )
    sports_question = any(
        cue in q
        for cue in ("football", "basketball", "baseball", "softball", "soccer", "volleyball", "athletics", "game", "roster")
    )
    if academic_calendar and not sports_question and "mcneesesports.com" in host:
        return 0
    score = 0
    for kw in src.keywords:
        if " " in kw:
            if kw in q:
                score += 5
        elif kw in q_words:
            score += 3
    # Light boost when the source name tokens appear in the question.
    for token in re.findall(r"[a-z0-9']+", src.name.lower()):
        if len(token) > 3 and token in q_words and token not in _STOPWORDS:
            score += 1

    # A source's own title/path is stronger evidence of topical specificity than
    # broad category tags. Reward pages that cover several meaningful question
    # terms so exact leaf pages outrank generic hubs without topic-specific rules.
    query_terms = _normalized_terms(query)
    source_terms = _normalized_terms(
        f"{src.name} {urlparse(src.url).path.replace('-', ' ').replace('_', ' ')}"
    )
    lexical_overlap = query_terms & source_terms
    score += min(len(lexical_overlap), 4) * 4
    if len(lexical_overlap) >= 2:
        title_coverage = len(lexical_overlap) / max(len(source_terms), 1)
        score += min(len(lexical_overlap), 4) * 2
        if title_coverage >= 0.60:
            score += 6
        if urlparse(src.url).path.strip("/").count("/") >= 1:
            score += 2
        if src.trust_tier == "A":
            score += 3
            if src.parent_source_id:
                score += 12
        if len(lexical_overlap) >= 3:
            score += 15

    # Curated roots retain routing authority for broad topic questions. A highly
    # specific leaf can still beat this prior through the coverage bonus above.
    if src.source_id in _TOPIC_KEYWORDS and not src.parent_source_id and score > 0:
        score += 25

    core = {"mcneese.edu", "catalog.mcneese.edu", "schedule.mcneese.edu"}
    scoped = [domain for domain in domains_for_question(query) if domain not in core]
    if scoped:
        if any(host_matches_domain(host, domain) for domain in scoped):
            score += 8
        elif src.trust_tier == "B":
            score -= 8
    return max(score, 0)


def match_sources(query: str, max_sources: int = 4) -> list[RegistrySource]:
    """Return the most relevant approved sources for a query, ranked by score.

    Always returns at least the admissions + main site as a sensible default
    when nothing else matches, so the assistant has something to read.
    """
    matched = match_registry(query, max_sources=max_sources)
    return matched.sources


def match_child_urls(
    query: str,
    parent_ids: list[str],
    *,
    max_urls: int = 4,
) -> list[str]:
    """Pick child leaf URLs under matched parents whose path/name fits the query."""
    if not parent_ids:
        return []
    q = query.lower()
    q_words = {w.strip(".:;()?!") for w in re.findall(r"[a-z0-9']+", q) if len(w) > 2}
    parents = set(parent_ids)
    scored: list[tuple[int, str]] = []
    for leaf in load_registry_leaves():
        if leaf.parent_source_id not in parents:
            continue
        blob = f"{leaf.name} {leaf.url}".lower().replace("-", " ").replace("/", " ")
        score = 0
        for w in q_words:
            if w in _STOPWORDS:
                continue
            if w in blob:
                score += 3
        # Prefer schedule/roster/amenities style pages when asked when/next/where.
        if any(w in q for w in ("when", "next", "upcoming", "schedule", "game")) and "schedule" in blob:
            score += 4
        if any(w in q for w in ("roster", "who is on", "players")) and "roster" in blob:
            score += 4
        if any(w in q for w in ("ticket", "tickets")) and "ticket" in blob:
            score += 4
        if any(w in q for w in ("floor plan", "amenities", "move-in", "apply")) and any(
            t in blob for t in ("floor", "amenities", "move", "apply")
        ):
            score += 3
        if score > 0:
            scored.append((score, leaf.url))
    scored.sort(key=lambda x: -x[0])
    out: list[str] = []
    seen: set[str] = set()
    for _, url in scored:
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(url)
        if len(out) >= max_urls:
            break
    return out


def match_registry(query: str, max_sources: int = 5) -> RegistryMatch:
    """Match a question against the whole seed registry (+ child leaf URLs)."""
    registry = load_registry()
    if not registry:
        return RegistryMatch([], [], [], [], [], {})

    q = (query or "").lower()
    q_words = {w.strip(".:;()?!") for w in q.split() if len(w) > 2}

    scored: list[tuple[int, RegistrySource]] = []
    scores: dict[str, int] = {}
    for src in registry:
        score = _score_source(q, q_words, src)
        if score > 0:
            scored.append((score, src))
            scores[src.source_id] = score

    scored.sort(key=lambda x: -x[0])

    if not scored:
        defaults = [s for s in registry if s.source_id in {"SRC-001", "SRC-002"}]
        sources = defaults[:max_sources]
    else:
        sources = [s for _, s in scored[:max_sources]]

    source_ids = [s.source_id for s in sources]
    seed_urls = [s.url for s in sources]
    # Expand matched hubs into the best-fitting child pages from the registry leaves.
    for child in match_child_urls(query, source_ids, max_urls=4):
        if child.rstrip("/").lower() not in {u.rstrip("/").lower() for u in seed_urls}:
            seed_urls.append(child)

    domains: list[str] = []
    seen_d: set[str] = set()
    for url in seed_urls:
        host = urlparse(url).netloc.lower()
        if not host:
            continue
        apex = host.removeprefix("www.")
        for candidate in (host, apex):
            if candidate and candidate not in seen_d:
                seen_d.add(candidate)
                domains.append(candidate)

    topics: list[str] = []
    for src in sources:
        for part in re.split(r"[/,|]", src.category or ""):
            t = part.strip().lower()
            if t and t not in topics:
                topics.append(t)

    return RegistryMatch(
        sources=sources,
        source_ids=source_ids,
        seed_urls=seed_urls,
        browse_domains=domains,
        topics=topics,
        scores=scores,
    )
