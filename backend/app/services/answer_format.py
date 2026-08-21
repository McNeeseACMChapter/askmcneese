"""Answer formatting fallbacks when the LLM is unavailable."""

from __future__ import annotations

import re

from app.services.retrieval import RetrievedChunk
from app.services.web_search import FetchedPage


def format_chunks_as_answer(chunks: list[RetrievedChunk], question: str = "") -> str:
    """
    Format chunks as a readable answer when LLM is unavailable.
    Extracts the most relevant sections instead of dumping raw text.
    """
    if not chunks:
        return "No relevant information found."

    question_lower = question.lower()

    # Extract key terms from question
    stopwords = {"what", "when", "where", "which", "that", "this", "have", "does", "about", "from", "the", "is", "are"}
    key_terms = [w.strip("?.,!") for w in question_lower.split() if len(w) > 2 and w not in stopwords]

    # Boilerplate phrases to skip
    skip_phrases = [
        'cookie policy', 'privacy statement', 'skip to content',
        'learn more', 'no thanks', 'i agree', 'expand\nexpand',
        'close menu', 'website terms', 'by using our site',
        'equal opportunity', 'compliance', 'reasonable accommodations',
        'university operates', 'treatment or employment', 'fax at',
        'reserves the right to change', 'catalog is not'
    ]

    best_sections = []
    seen = set()

    for chunk in chunks:
        text = chunk.text.strip()

        # Split by markdown headers (##, ###)
        sections = re.split(r'\n(?=##?\s)', text)

        for section in sections:
            section = section.strip()
            if len(section) < 15:
                continue

            section_lower = section.lower()

            # Skip boilerplate
            if any(p in section_lower for p in skip_phrases):
                continue

            # Calculate relevance score
            score = 0

            # Keyword matches
            for term in key_terms:
                if term in section_lower:
                    score += 2

            # High-value patterns (actual content, not navigation)
            high_value = ['deadline', 'august', 'december', 'may', 'january', 'february',
                         'requirement', 'gpa', 'sat', 'act', 'tuition', 'cost', 'fee',
                         'scholarship', 'financial aid', 'fafsa', 'apply', 'admission']
            for hv in high_value:
                if hv in section_lower:
                    score += 3

            # Penalize navigation-looking content
            nav_indicators = ['expand', 'overview', 'next step', 'explore this section',
                             'visit mcneese', 'apply as', 'i am a']
            for nav in nav_indicators:
                if nav in section_lower:
                    score -= 1

            # Check for actual data (numbers, dates)
            if re.search(r'\b\d{1,2}\b', section):  # Has numbers (like dates)
                score += 2

            # Deduplicate
            key = section[:80]
            if key in seen:
                continue
            seen.add(key)

            if score > 2:
                best_sections.append((score, section, chunk.title, chunk.source_url))

    # Sort by score and take best
    best_sections.sort(key=lambda x: -x[0])

    # If the best section is significantly better, just show that one
    if best_sections and best_sections[0][0] >= 8:
        top = [best_sections[0]]
    elif best_sections:
        # Only include if score is high enough
        top = [s for s in best_sections if s[0] >= 6][:1]
        if not top and best_sections[0][0] >= 4:
            top = [best_sections[0]]
    else:
        top = []

    if not top:
        # Fallback: show beginning of first chunk (cleaned)
        chunk = chunks[0]
        text = chunk.text
        # Remove cookie/header noise
        for phrase in skip_phrases:
            text = text.replace(phrase, '')
        lines = [l for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
        clean = '\n'.join(lines[:8])
        return f"{clean[:400]}...\n\n📚 Source: [{chunk.title}]({chunk.source_url})"

    # Build the answer
    parts = []
    for score, section, title, url in top:
        # Clean up
        clean = section.replace('\n\n\n', '\n\n').strip()
        if len(clean) > 350:
            clean = clean[:350] + "..."
        parts.append(clean)

    # Get unique sources
    sources = list(dict.fromkeys((s[2], s[3]) for s in top))
    source_text = ', '.join(f"[{t}]({u})" for t, u in sources)

    return '\n\n'.join(parts) + f"\n\n📚 Source: {source_text}"


def _format_web_results(pages: list[FetchedPage], question: str) -> str:
    """Format fetched web pages as a readable answer when the LLM is unavailable.

    Picks the paragraphs most relevant to the question (keyword overlap) so the
    user sees the useful part of the page instead of a raw dump.
    """
    if not pages:
        return "No relevant information found."

    stop = {"the", "is", "are", "a", "an", "of", "to", "in", "on", "at", "for",
            "and", "or", "what", "when", "where", "which", "who", "how", "do",
            "does", "did", "can", "i", "you", "me", "my", "with", "about",
            "mcneese", "university", "state"}
    q_terms = {w.strip("?.,!").lower() for w in question.split()
               if len(w) > 2 and w.lower() not in stop}

    def _score(para: str) -> int:
        low = para.lower()
        s = sum(2 for t in q_terms if t in low)
        # Reward concrete data (dates, money, numbers)
        if re.search(r"\b(august|september|october|november|december|january|"
                      r"february|march|april|may|june|july)\b", low):
            s += 3
        if re.search(r"\$\d|\d{1,2}(st|nd|rd|th)?\b", para):
            s += 1
        return s

    scored_paras: list[tuple[int, str, FetchedPage]] = []
    for page in pages:
        for para in page.content.split("\n\n"):
            para = para.strip()
            if len(para) < 40:
                continue
            scored_paras.append((_score(para), para, page))

    scored_paras.sort(key=lambda x: -x[0])
    top = [sp for sp in scored_paras if sp[0] > 0][:4]
    if not top:
        top = scored_paras[:2]

    seen_pages = []
    parts = []
    for _, para, page in top:
        if len(para) > 400:
            para = para[:400].rsplit(" ", 1)[0] + "..."
        parts.append(para)
        if page.url not in [p.url for p in seen_pages]:
            seen_pages.append(page)

    body = "\n\n".join(parts)
    sources = ", ".join(f"[{p.title}]({p.url})" for p in seen_pages[:3])
    return f"{body}\n\n📚 Sources: {sources}"
