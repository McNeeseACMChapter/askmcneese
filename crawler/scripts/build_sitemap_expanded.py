"""Generate sitemap_expanded.csv for AskMcNeese registry expansion.

Run from repo root:
    python askmcneese/crawler/scripts/build_sitemap_expanded.py

Output: askmcneese/knowledge/sitemap_expanded.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import httpx

KNOWLEDGE = Path(__file__).resolve().parents[2] / "knowledge"
OUT = KNOWLEDGE / "sitemap_expanded.csv"
SEED = KNOWLEDGE / "source_registry_seed.csv"

UA = {"User-Agent": "Mozilla/5.0 (compatible; AskMcNeeseBot/0.1; registry-expansion)"}
MCNEESE_HOSTS = {"www.mcneese.edu", "mcneese.edu", "catalog.mcneese.edu"}

HUB_PATTERNS = [
    r"^/$", r"^/admissions/?$", r"^/student-central/?$", r"^/academics/?$",
    r"^/academics/undergraduate-programs/?$", r"^/academics/graduate-programs/?$",
    r"^/academics/colleges-and-departments/?$", r"^/financial-aid/?$",
    r"^/international/?$", r"^/registrar/?$", r"^/campus-life/?$",
    r"^/library/?$", r"^/policy/?$", r"^/schedule/?$", r"^/today/?$",
    r"^/scholarships/?$",
]

LEAF_BOOST_PATTERNS = [
    (r"/scholarships/", "scholarship_leaf", "high"),
    (r"/student-central/international-scholarships", "scholarship_leaf", "high"),
    (r"preview_program\.php", "catalog_program", "high"),
    (r"content\.php.*navoid=", "catalog_content", "high"),
    (r"/admissions/(apply|estimated-costs|deadlines)", "admissions_leaf", "high"),
    (r"/financial-aid/", "financial_aid_leaf", "high"),
    (r"/registrar/", "registrar_leaf", "medium"),
    (r"/policy/", "policy_leaf", "high"),
    (r"\.pdf$", "pdf", "high"),
    (r"/academics/.+/.+", "academic_leaf", "medium"),
    (r"/college-of-|/department-of-|/school-of-", "department_leaf", "medium"),
]

EXCLUDE_PATTERNS = [
    r"/wp-json/", r"/feed/", r"/author/", r"/tag/", r"/category/",
    r"/breakdance", r"\?replytocom=",
    r"/wp-content/uploads/\d{4}/\d{2}/.*\.(jpg|jpeg|png|gif|webp)$",
]


def parse_sitemap_urls(text: str) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return urls
    for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if loc.text:
            urls.append(loc.text.strip())
    if not urls:
        for loc in root.findall(".//loc"):
            if loc.text:
                urls.append(loc.text.strip())
    return urls


def fetch(client: httpx.Client, url: str) -> str:
    r = client.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def collect_mcneese_sitemap_urls(client: httpx.Client) -> list[str]:
    index = fetch(client, "https://www.mcneese.edu/sitemap_index.xml")
    child_sitemaps = [u for u in parse_sitemap_urls(index) if u.endswith(".xml")]
    page_urls: list[str] = []
    for sm in child_sitemaps:
        if "post-sitemap" in sm or "page-sitemap" in sm:
            try:
                page_urls.extend(parse_sitemap_urls(fetch(client, sm)))
            except Exception:
                pass
    return list(dict.fromkeys(page_urls))


def collect_catalog_urls(client: httpx.Client, max_pages: int = 400) -> list[str]:
    start = "https://catalog.mcneese.edu/"
    seen: set[str] = set()
    queue = [start]
    found: list[str] = []
    link_re = re.compile(r'href=["\']([^"\']+)["\']', re.I)
    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = fetch(client, url)
        except Exception:
            continue
        for href in link_re.findall(html):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            abs_url = urljoin(url, href)
            parsed = urlparse(abs_url)
            if parsed.netloc.lower() != "catalog.mcneese.edu":
                continue
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean += "?" + parsed.query
            if clean not in seen:
                if "preview_program.php" in clean or "content.php" in clean:
                    found.append(clean)
                elif parsed.path in ("/", "") or "index.php" in parsed.path:
                    queue.append(clean)
                elif any(k in clean for k in ("preview_program", "content.php", "program", "course")):
                    queue.append(clean)
    return list(dict.fromkeys(found))


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    path = p.path.rstrip("/").lower() or "/"
    host = p.netloc.lower()
    if host == "mcneese.edu":
        host = "www.mcneese.edu"
    base = f"https://{host}{path}"
    return f"{base}?{p.query}" if p.query else base


def categorize(url: str) -> tuple[str, str, str]:
    p = urlparse(url)
    host = p.netloc.lower()
    path = p.path.lower()
    full = url.lower()
    if host not in MCNEESE_HOSTS and "mcneese.edu" not in host:
        return "external", "false", "low"
    if full.endswith(".pdf") or ".pdf?" in full:
        return "pdf", "true", "high"
    for pat, cat, pri in LEAF_BOOST_PATTERNS:
        if re.search(pat, full, re.I):
            return cat, "false", pri
    for hub_pat in HUB_PATTERNS:
        if re.match(hub_pat, path):
            return "hub_nav", "false", "medium"
    if "catalog.mcneese.edu" in host:
        if "preview_program" in full or "content.php" in full:
            return "catalog_leaf", "false", "high"
        return "catalog_page", "false", "medium"
    if "/20" in path and re.search(r"/\d{4}/\d{2}/", path):
        return "news_post", "false", "low"
    if path.count("/") >= 3:
        return "leaf_detail", "false", "high"
    return "leaf_detail", "false", "medium"


def should_include(url: str, category: str, priority: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, url, re.I):
            return False
    if category in ("external", "news_post") and priority == "low":
        return False
    return True


def load_seed_urls() -> set[str]:
    if not SEED.exists():
        return set()
    return {normalize_url(r["Source URL"]) for r in csv.DictReader(SEED.open(encoding="utf-8-sig")) if r.get("Source URL")}


def propose_parent(url: str, category: str) -> str:
    u = url.lower()
    if "scholarship" in u:
        if "international" in u: return "SRC-033"
        if "freshman" in u: return "SRC-031"
        if "continuing" in u: return "SRC-032"
        return "SRC-006"
    if "catalog.mcneese.edu" in u: return "SRC-011"
    if "/admissions/" in u: return "SRC-002"
    if "/financial-aid/" in u: return "SRC-005"
    if "/international/" in u: return "SRC-003"
    if "/registrar/" in u: return "SRC-015"
    if "/academics/" in u or "preview_program" in u: return "SRC-007"
    if "/policy/" in u: return "SRC-020"
    if "/student-central/" in u: return "SRC-014"
    return ""


def main() -> None:
    with httpx.Client(headers=UA, follow_redirects=True) as client:
        mcneese_urls = collect_mcneese_sitemap_urls(client)
        catalog_urls = collect_catalog_urls(client)
        print(f"Sitemap URLs: {len(mcneese_urls)}; catalog browse: {len(catalog_urls)}")

    rows = []
    for url in dict.fromkeys(mcneese_urls + catalog_urls):
        norm = normalize_url(url)
        cat, is_pdf, priority = categorize(norm)
        if not should_include(norm, cat, priority):
            continue
        domain = urlparse(norm).netloc.lower()
        rows.append({
            "url": norm,
            "category_heuristic": cat,
            "is_pdf": is_pdf,
            "domain": domain,
            "extracted_from": "catalog_browse" if "catalog.mcneese.edu" in domain else "sitemap_xml",
            "priority": priority,
            "proposed_parent_source_id": propose_parent(norm, cat),
        })

    pri_order = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: (pri_order.get(r["priority"], 9), r["category_heuristic"], r["url"]))
    high = [r for r in rows if r["priority"] == "high"]
    medium = [r for r in rows if r["priority"] == "medium"]
    final = (high[:160] + medium[: max(0, 200 - min(160, len(high)))])[:200]

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "url", "category_heuristic", "is_pdf", "domain",
            "extracted_from", "priority", "proposed_parent_source_id",
        ])
        w.writeheader()
        w.writerows(final)

    seed = load_seed_urls()
    print(f"Wrote {len(final)} rows -> {OUT}")
    print(f"  overlap with seed: {sum(1 for r in final if r['url'] in seed)}")


if __name__ == "__main__":
    main()
