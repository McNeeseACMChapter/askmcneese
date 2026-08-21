"""Discover public McNeese ecosystem pages without crossing auth/private boundaries.

The script starts with McNeese-owned directory pages plus the governed domain
registry, obeys robots.txt, reads sitemap indexes, and writes an auditable page
inventory. ``--merge`` adds enabled public Tier A/B pages to the merged source
registry; unknown domains are candidates only and never become retrieval targets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.services.domain_registry import (  # noqa: E402
    host_matches_domain,
    load_domain_registry,
    record_for_url,
)

KNOWLEDGE = REPO / "knowledge"
DOMAIN_CANDIDATES = KNOWLEDGE / "domain_discovery_candidates.csv"
PAGE_INVENTORY = KNOWLEDGE / "ecosystem_discovered_pages.csv"
MERGED_REGISTRY = KNOWLEDGE / "source_registry_merged.csv"
USER_AGENT = "AskMcNeesePublicIndexer/1.0 (+https://www.mcneese.edu/)"
OFFICIAL_DIRECTORY_SEEDS = (
    "https://www.mcneese.edu/a-to-z/",
    "https://www.mcneese.edu/alumni-friends/",
    "https://www.mcneese.edu/",
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


def normalize_public_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    if parsed.username or parsed.password:
        return ""
    path = parsed.path or "/"
    return parsed._replace(fragment="", path=path).geturl()


class DiscoveryClient:
    def __init__(self) -> None:
        self.http = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=20,
        )
        self.robots: dict[str, RobotFileParser] = {}
        self.sitemaps: dict[str, list[str]] = {}

    def close(self) -> None:
        self.http.close()

    def robot(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin in self.robots:
            return self.robots[origin]
        rp = RobotFileParser()
        robots_url = origin + "/robots.txt"
        rp.set_url(robots_url)
        try:
            response = self.http.get(robots_url)
            rp.parse(response.text.splitlines() if response.status_code == 200 else [])
            self.sitemaps[origin] = [
                line.split(":", 1)[1].strip()
                for line in response.text.splitlines()
                if response.status_code == 200 and line.lower().startswith("sitemap:")
            ]
        except Exception:
            rp.parse([])
            self.sitemaps[origin] = []
        self.robots[origin] = rp
        return rp

    def get(self, url: str) -> httpx.Response | None:
        if not self.robot(url).can_fetch(USER_AGENT, url):
            return None
        try:
            response = self.http.get(url)
            if response.status_code == 200:
                return response
        except Exception:
            return None
        return None


def html_links(base_url: str, html: str) -> list[str]:
    parser = LinkParser()
    parser.feed(html)
    out: list[str] = []
    for href in parser.hrefs:
        url = normalize_public_url(urljoin(base_url, href))
        if url:
            out.append(url)
    return out


def sitemap_urls(client: DiscoveryClient, root_url: str, limit: int) -> list[str]:
    parsed = urlparse(root_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    client.robot(root_url)
    queue = list(client.sitemaps.get(origin) or [])
    queue.extend([origin + "/sitemap.xml", origin + "/sitemap_index.xml"])
    seen_maps: set[str] = set()
    pages: list[str] = []
    seen_pages: set[str] = set()
    while queue and len(pages) < limit:
        sitemap = queue.pop(0)
        if sitemap in seen_maps:
            continue
        seen_maps.add(sitemap)
        response = client.get(sitemap)
        if response is None:
            continue
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            continue
        is_index = root.tag.lower().endswith("sitemapindex")
        for node in root.iter():
            if not node.tag.lower().endswith("loc") or not node.text:
                continue
            url = normalize_public_url(node.text.strip())
            if not url:
                continue
            if is_index:
                queue.append(url)
            elif url not in seen_pages and client.robot(url).can_fetch(USER_AGENT, url):
                seen_pages.add(url)
                pages.append(url)
                if len(pages) >= limit:
                    break
    return pages


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def merge_pages(pages: list[dict[str, str]]) -> int:
    with MERGED_REGISTRY.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    existing = {(row.get("url") or "").rstrip("/").lower() for row in rows}
    added = 0
    for page in pages:
        url = page["url"]
        key = url.rstrip("/").lower()
        record = record_for_url(url)
        if key in existing or not record or not record.enabled:
            continue
        if record.trust_tier not in {"A", "B"} or record.crawl_policy != "public":
            continue
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:14].upper()
        rows.append({
            "source_id": f"ECO-{digest}",
            "source_name": page.get("title") or urlparse(url).path.strip("/") or record.domain,
            "url": url,
            "domain": record.domain,
            "content_type": "html",
            "category": "|".join(sorted(record.categories)),
            "parent_source_id": "",
            "is_leaf": "true",
            "catalog_year": "",
            "priority_for_ingest": "medium",
            "PM_Review_Status": "Registry_Auto_Approved",
            "Allowed_for_AI_Retrieval": "Yes",
            "last_ingested_timestamp": "",
            "content_hash": "",
            "discovered_from": page.get("discovered_from") or "ecosystem_sitemap",
            "notes": f"Public page on enabled Tier {record.trust_tier} domain; robots.txt allowed.",
        })
        existing.add(key)
        added += 1
    with MERGED_REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover governed public McNeese ecosystem pages.")
    parser.add_argument("--max-urls-per-domain", type=int, default=2000)
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()

    client = DiscoveryClient()
    candidate_map: dict[str, dict[str, str]] = {}
    page_map: dict[str, dict[str, str]] = {}
    try:
        for seed in OFFICIAL_DIRECTORY_SEEDS:
            response = client.get(seed)
            if response is None:
                continue
            for url in html_links(str(response.url), response.text):
                host = (urlparse(url).hostname or "").lower().removeprefix("www.")
                if not host:
                    continue
                record = record_for_url(url)
                candidate_map.setdefault(host, {
                    "domain": host,
                    "status": "enabled" if record else "review_required",
                    "trust_tier": record.trust_tier if record else "",
                    "relationship": record.relationship if record else "",
                    "found_on": seed,
                    "example_url": url,
                })
                if record and record.enabled and record.crawl_policy == "public":
                    page_map.setdefault(url, {
                        "url": url,
                        "domain": record.domain,
                        "trust_tier": record.trust_tier,
                        "discovered_from": "official_directory_link",
                        "title": "",
                    })

        for record in load_domain_registry():
            if not record.enabled or record.trust_tier not in {"A", "B"}:
                continue
            root = f"https://{record.domain}/"
            page_map.setdefault(root, {
                "url": root,
                "domain": record.domain,
                "trust_tier": record.trust_tier,
                "discovered_from": "domain_registry",
                "title": record.domain,
            })
            if record.crawl_policy != "public":
                continue
            for url in sitemap_urls(client, root, args.max_urls_per_domain):
                if not host_matches_domain(urlparse(url).hostname or "", record.domain):
                    continue
                page_map.setdefault(url, {
                    "url": url,
                    "domain": record.domain,
                    "trust_tier": record.trust_tier,
                    "discovered_from": "ecosystem_sitemap",
                    "title": "",
                })
    finally:
        client.close()

    candidates = sorted(candidate_map.values(), key=lambda row: row["domain"])
    pages = sorted(page_map.values(), key=lambda row: (row["domain"], row["url"]))
    write_csv(
        DOMAIN_CANDIDATES,
        candidates,
        ["domain", "status", "trust_tier", "relationship", "found_on", "example_url"],
    )
    write_csv(
        PAGE_INVENTORY,
        pages,
        ["url", "domain", "trust_tier", "discovered_from", "title"],
    )
    added = merge_pages(pages) if args.merge else 0
    print(f"domains={len(candidates)} pages={len(pages)} merged={added}")
    print(f"candidates={DOMAIN_CANDIDATES}")
    print(f"inventory={PAGE_INVENTORY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
