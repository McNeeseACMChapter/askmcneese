"""Fail-closed URL authorization for RCCS.

McNeese official domains remain allowed for official channels.
Tier C domains require an enabled companion match + active plan + category fit.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.services.domain_registry import official_domains, record_for_host
from app.services.rccs.models import CompanionSource, RetrievalPlan

# Backward-compatible export. The canonical policy lives in the audited CSV.
OFFICIAL_DOMAINS = official_domains()

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Normalize scheme/host and strip fragments + tracking params."""
    try:
        parsed = urlparse((url or "").strip())
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return ""
        query = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in _TRACKING_PARAMS
        ]
        cleaned = parsed._replace(
            netloc=parsed.netloc.lower(),
            fragment="",
            query=urlencode(query),
        )
        return urlunparse(cleaned)
    except Exception:
        return ""


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _is_official_host(host: str) -> bool:
    return record_for_host(host) is not None

def _is_private_or_local(host: str) -> bool:
    if not host:
        return True
    h = host.strip("[]").lower()
    if h in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return True
    if h.endswith(".local") or h.endswith(".internal"):
        return True
    # Cloud metadata
    if h in {"169.254.169.254", "metadata.google.internal"}:
        return True
    try:
        ip = ipaddress.ip_address(h)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        )
    except ValueError:
        return False


def is_safe_public_url_literal(url: str) -> bool:
    """Reject malformed, credential-bearing, local, and literal private URLs."""
    normalized = normalize_url(url)
    if not normalized:
        return False
    return not _is_private_or_local(_host(normalized))


async def validate_outbound_url(
    url: str,
    *,
    allowed_domains: list[str] | None = None,
) -> str:
    """Resolve a URL and return its normalized form only when every IP is public."""
    normalized = normalize_url(url)
    if not normalized:
        raise ValueError("invalid_outbound_url")
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    if _is_private_or_local(host):
        raise ValueError("private_or_local_destination")
    if allowed_domains and not host_matches_allowlist(host, allowed_domains):
        raise ValueError("destination_not_allowed")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    loop = asyncio.get_running_loop()
    try:
        addresses = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            ),
        )
    except OSError as exc:
        raise ValueError("destination_dns_failed") from exc
    if not addresses:
        raise ValueError("destination_dns_empty")
    for item in addresses:
        address = item[4][0].split("%", 1)[0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError("destination_ip_invalid") from exc
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError("private_or_local_destination")
    return normalized

def host_matches_allowlist(host: str, allowlist: list[str]) -> bool:
    host = (host or "").lower()
    for entry in allowlist:
        e = entry.lower().strip()
        if not e:
            continue
        if host == e or host.endswith("." + e):
            return True
    return False


def is_allowed_url(
    url: str,
    *,
    channel: str,
    plan: RetrievalPlan | None = None,
    matched_companions: list[CompanionSource] | None = None,
) -> bool:
    """Fail-closed authorization.

    channel: 'official_live' | 'companion' | 'kb' (kb has no URL fetch)
    """
    normalized = normalize_url(url)
    if not normalized:
        return False

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.hostname or "").lower()
    if _is_private_or_local(host):
        return False

    if channel in {"official_live", "kb"}:
        return _is_official_host(host)

    if channel != "companion":
        return False

    # Companion path: plan must activate companions
    if plan is not None and not (plan.companion_source_ids or plan.companion_categories):
        return False
    if plan is not None and not plan.use_kb and not plan.use_official_live:
        # companions alone are allowed when plan has companion ids
        pass

    companions = matched_companions or []
    if not companions:
        return False

    # URL must match a specific matched companion's domain allowlist —
    # one companion must not unlock every external domain.
    for src in companions:
        if not src.enabled or not src.allowed_for_ai_retrieval:
            continue
        if plan and plan.companion_source_ids and src.source_id not in plan.companion_source_ids:
            continue
        if plan and plan.companion_categories and src.category not in plan.companion_categories:
            continue
        if host_matches_allowlist(host, src.domain_allowlist):
            return True
    return False


def is_mcneese_or_official_url(url: str) -> bool:
    """Backward-compatible official check used by legacy web_search paths."""
    return is_allowed_url(url, channel="official_live")


def filter_official_urls(urls: list[str]) -> list[str]:
    return [u for u in urls if is_mcneese_or_official_url(u)]


_UNSAFE_SCHEME = re.compile(r"^(?:file|ftp|data|javascript):", re.IGNORECASE)


def reject_reason(url: str) -> str:
    if not url:
        return "empty"
    if _UNSAFE_SCHEME.match(url.strip()):
        return "unsafe_scheme"
    host = _host(url)
    if _is_private_or_local(host):
        return "private_or_local"
    if not normalize_url(url):
        return "invalid"
    return "not_authorized"
