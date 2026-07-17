"""External search providers: Tavily, Serper, Perplexity (+ DDG fallback).

Keys are read from the environment. Never log API keys.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ASK = _BACKEND_ROOT.parent
load_dotenv(_REPO_ASK / ".env", override=False)
load_dotenv(_BACKEND_ROOT / ".env", override=True)

from app.services.rccs.allowlist import is_mcneese_or_official_url, normalize_url


@dataclass
class ProviderHit:
    url: str
    title: str
    snippet: str
    provider: str
    raw: dict[str, Any] | None = None


def tavily_key() -> str:
    return (os.getenv("TAVILY_API_KEY") or "").strip()


def serper_key() -> str:
    return (os.getenv("SERPER_API_KEY") or "").strip()


def serpapi_key() -> str:
    return (os.getenv("SERPAPI_API_KEY") or "").strip()


def perplexity_key() -> str:
    # Support user's PERPLE_API_KEY typo and canonical name
    return (
        os.getenv("PERPLEXITY_API_KEY")
        or os.getenv("PERPLE_API_KEY")
        or ""
    ).strip()


def web_browsing_enabled() -> bool:
    return os.getenv("WEB_BROWSING_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def preferred_provider() -> str:
    """auto | tavily | serper | serpapi | perplexity | ddg"""
    return (os.getenv("SEARCH_PROVIDER") or "auto").strip().lower()


def provider_status() -> dict[str, object]:
    return {
        "tavily_configured": bool(tavily_key()),
        "serper_configured": bool(serper_key()),
        "serpapi_configured": bool(serpapi_key()),
        "perplexity_configured": bool(perplexity_key()),
        "web_browsing_enabled": web_browsing_enabled(),
        "preferred_provider": preferred_provider(),
    }


def _host_allowed(url: str, *, include_domains: list[str] | None) -> bool:
    if not url:
        return False
    nu = normalize_url(url) or url
    if include_domains is None:
        return True
    try:
        host = urlparse(nu).netloc.lower()
    except Exception:
        return False
    for d in include_domains:
        d = d.lower().strip()
        if not d:
            continue
        if host == d or host.endswith("." + d):
            return True
    return False


async def _tavily_search(
    query: str,
    *,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    key = tavily_key()
    if not key:
        return []
    payload: dict[str, Any] = {
        "api_key": key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
        "max_results": max_results,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()
    hits: list[ProviderHit] = []
    for item in data.get("results") or []:
        url = (item.get("url") or "").strip()
        if not _host_allowed(url, include_domains=include_domains):
            continue
        hits.append(
            ProviderHit(
                url=url,
                title=(item.get("title") or "").strip(),
                snippet=(item.get("content") or item.get("snippet") or "").strip(),
                provider="tavily",
                raw=item if isinstance(item, dict) else None,
            )
        )
    return hits


async def _serper_search(
    query: str,
    *,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    key = serper_key()
    if not key:
        return []
    q = query
    if include_domains:
        # Prefer a single site: filter (dedupe www vs apex)
        primary = include_domains[0].lower().removeprefix("www.")
        q = f"site:{primary} {query}"
    headers = {"X-API-KEY": key, "Content-Type": "application/json"}
    payload = {"q": q, "num": max_results}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
        if r.status_code == 403 and not serpapi_key():
            # Common mix-up: SerpAPI key stored as SERPER_API_KEY
            return await _serpapi_search_with_key(
                key, query=query, max_results=max_results, include_domains=include_domains
            )
        r.raise_for_status()
        data = r.json()
    hits: list[ProviderHit] = []
    for item in (data.get("organic") or [])[: max_results * 2]:
        url = (item.get("link") or "").strip()
        if not _host_allowed(url, include_domains=include_domains):
            continue
        hits.append(
            ProviderHit(
                url=url,
                title=(item.get("title") or "").strip(),
                snippet=(item.get("snippet") or "").strip(),
                provider="serper",
                raw=item if isinstance(item, dict) else None,
            )
        )
    return hits[:max_results]


async def _serpapi_search_with_key(
    key: str,
    *,
    query: str,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    q = query
    if include_domains:
        primary = include_domains[0].lower().removeprefix("www.")
        q = f"site:{primary} {query}"
    params = {
        "engine": "google",
        "q": q,
        "api_key": key,
        "num": max_results,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get("https://serpapi.com/search", params=params)
        r.raise_for_status()
        data = r.json()
    hits: list[ProviderHit] = []
    for item in (data.get("organic_results") or [])[: max_results * 2]:
        url = (item.get("link") or "").strip()
        if not _host_allowed(url, include_domains=include_domains):
            continue
        hits.append(
            ProviderHit(
                url=url,
                title=(item.get("title") or "").strip(),
                snippet=(item.get("snippet") or "").strip(),
                provider="serpapi",
                raw=item if isinstance(item, dict) else None,
            )
        )
    return hits[:max_results]


async def _serpapi_search(
    query: str,
    *,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    key = serpapi_key()
    if not key:
        return []
    return await _serpapi_search_with_key(
        key, query=query, max_results=max_results, include_domains=include_domains
    )


async def _perplexity_search(
    query: str,
    *,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    """Use Perplexity Sonar (agentic-capable) for grounded web answers."""
    key = perplexity_key()
    if not key:
        return []
    domain_filter: list[str] = []
    if include_domains:
        domain_filter = sorted({d.lower().removeprefix("www.") for d in include_domains})
    messages = [
        {
            "role": "system",
            "content": (
                "Return factual findings only from the web. "
                "Do not invent ratings, review counts, emails, or titles."
            ),
        },
        {"role": "user", "content": query},
    ]
    model = os.getenv("PERPLEXITY_MODEL", "sonar-pro")
    web_opts: dict[str, Any] = {
        "search_context_size": os.getenv("PERPLEXITY_SEARCH_CONTEXT_SIZE", "medium"),
    }
    search_type = os.getenv("PERPLEXITY_SEARCH_TYPE", "auto")
    if search_type in {"auto", "pro", "fast"}:
        web_opts["search_type"] = search_type
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "web_search_options": web_opts,
    }
    if domain_filter:
        payload["search_domain_filter"] = domain_filter[:20]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
    content = ""
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = ""
    citations: list[str] = []
    for c in data.get("citations") or []:
        if isinstance(c, str):
            citations.append(c)
    for sr in data.get("search_results") or []:
        if isinstance(sr, dict) and sr.get("url"):
            citations.append(str(sr["url"]))
            # Prefer search_results snippets when present
    hits: list[ProviderHit] = []
    seen: set[str] = set()
    # Prefer structured search_results
    for i, sr in enumerate(data.get("search_results") or []):
        if not isinstance(sr, dict):
            continue
        url = (sr.get("url") or "").strip()
        if not url or not _host_allowed(url, include_domains=include_domains):
            continue
        key_u = (normalize_url(url) or url).rstrip("/").lower()
        if key_u in seen:
            continue
        seen.add(key_u)
        hits.append(
            ProviderHit(
                url=url,
                title=(sr.get("title") or f"Perplexity source {i + 1}").strip(),
                snippet=(sr.get("snippet") or (content[:1500] if i == 0 else "")).strip(),
                provider="perplexity",
                raw=sr,
            )
        )
        if len(hits) >= max_results:
            break
    if not hits:
        for i, url in enumerate(citations[:max_results]):
            if not isinstance(url, str):
                continue
            if not _host_allowed(url, include_domains=include_domains):
                continue
            hits.append(
                ProviderHit(
                    url=url,
                    title=f"Perplexity source {i + 1}",
                    snippet=content[:1500] if i == 0 else content[:400],
                    provider="perplexity",
                    raw={"citation": url},
                )
            )
    elif content and hits:
        # Attach answer summary onto first hit if snippet thin
        if len(hits[0].snippet) < 80:
            hits[0].snippet = (content[:2000] + "\n" + hits[0].snippet).strip()
    return hits[:max_results]


async def _ddg_search(
    query: str,
    *,
    max_results: int,
    include_domains: list[str] | None,
) -> list[ProviderHit]:
    try:
        from app.services.web_search import search_duckduckgo

        results = await search_duckduckgo(query, max_results=max_results)
    except Exception:
        return []
    hits: list[ProviderHit] = []
    for r in results:
        url = getattr(r, "url", "") or ""
        if include_domains is not None and not _host_allowed(url, include_domains=include_domains):
            # search_duckduckgo already McNeese-filters; still apply
            if not is_mcneese_or_official_url(url):
                continue
        hits.append(
            ProviderHit(
                url=url,
                title=getattr(r, "title", "") or "",
                snippet=getattr(r, "snippet", "") or "",
                provider="ddg",
            )
        )
    return hits


async def search_web(
    query: str,
    *,
    max_results: int = 8,
    include_domains: list[str] | None = None,
    providers: list[str] | None = None,
) -> list[ProviderHit]:
    """Run configured providers in preference order; merge unique URLs."""
    if not web_browsing_enabled() and providers is None:
        # Still allow explicit provider calls; default path respects flag via callers
        pass

    pref = preferred_provider()
    order = providers or []
    if not order:
        if pref == "auto":
            # Prefer Perplexity Sonar (agentic browse) when keyed — works without other paid SERPs.
            if perplexity_key():
                order = ["perplexity", "tavily", "serper", "serpapi", "ddg"]
            else:
                order = ["tavily", "serper", "serpapi", "perplexity", "ddg"]
        elif pref in {"tavily", "serper", "serpapi", "perplexity", "ddg"}:
            order = [pref, "tavily", "serper", "serpapi", "perplexity", "ddg"]
        else:
            order = ["tavily", "serper", "serpapi", "perplexity", "ddg"]

    seen: set[str] = set()
    merged: list[ProviderHit] = []

    async def _run(name: str) -> list[ProviderHit]:
        try:
            if name == "tavily":
                return await _tavily_search(query, max_results=max_results, include_domains=include_domains)
            if name == "serper":
                return await _serper_search(query, max_results=max_results, include_domains=include_domains)
            if name == "serpapi":
                return await _serpapi_search(query, max_results=max_results, include_domains=include_domains)
            if name == "perplexity":
                return await _perplexity_search(query, max_results=max_results, include_domains=include_domains)
            if name == "ddg":
                return await _ddg_search(query, max_results=max_results, include_domains=include_domains)
        except Exception as e:
            print(f"search provider {name} failed: {e}")
        return []

    for name in order:
        if len(merged) >= max_results:
            break
        hits = await _run(name)
        for h in hits:
            key = (normalize_url(h.url) or h.url or h.title).rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(h)
            if len(merged) >= max_results:
                break
        # If a primary paid provider returned results, stop cascading
        if merged and name in {"tavily", "serper", "serpapi", "perplexity"}:
            break

    return merged[:max_results]


def search_web_sync(*args: Any, **kwargs: Any) -> list[ProviderHit]:
    return asyncio.get_event_loop().run_until_complete(search_web(*args, **kwargs))
