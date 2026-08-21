"""Small dependency-free abuse boundary for the public Ask endpoint."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable

ASGIApp = Callable[[dict[str, Any], Callable[..., Awaitable[dict]], Callable[..., Awaitable[None]]], Awaitable[None]]


def _positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


class AskRequestGuardMiddleware:
    """Bound request size, per-client frequency, and expensive concurrency.

    This is a process-local safety net. Production should also enforce limits at
    the load balancer/API gateway where limits can be shared across workers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.max_body_bytes = _positive_int("ASK_MAX_BODY_BYTES", 96 * 1024)
        self.requests_per_minute = _positive_int("ASK_RATE_LIMIT_PER_MINUTE", 24)
        self.acquire_timeout_ms = _positive_int("ASK_CONCURRENCY_WAIT_MS", 250)
        self._semaphore = asyncio.Semaphore(
            _positive_int("ASK_MAX_CONCURRENT_REQUESTS", 8)
        )
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._hits_lock = asyncio.Lock()

    @staticmethod
    async def _json_response(
        send: Callable[..., Awaitable[None]],
        status: int,
        detail: str,
        *,
        retry_after: int | None = None,
    ) -> None:
        body = json.dumps({"detail": detail}).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"cache-control", b"no-store"),
        ]
        if retry_after is not None:
            headers.append((b"retry-after", str(retry_after).encode("ascii")))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    async def _within_rate_limit(self, client_key: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60.0
        async with self._hits_lock:
            hits = self._hits[client_key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.requests_per_minute:
                return False
            hits.append(now)
            if len(self._hits) > 4096:
                stale = [key for key, values in self._hits.items() if not values or values[-1] <= cutoff]
                for key in stale[:1024]:
                    self._hits.pop(key, None)
            return True

    async def __call__(self, scope, receive, send) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/ask"
        ):
            await self.app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers") or []}
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    await self._json_response(send, 413, "Request body is too large.")
                    return
            except ValueError:
                await self._json_response(send, 400, "Invalid Content-Length header.")
                return

        client = scope.get("client") or ("unknown", 0)
        client_key = str(client[0] or "unknown")
        if not await self._within_rate_limit(client_key):
            await self._json_response(
                send,
                429,
                "Too many requests. Please wait before trying again.",
                retry_after=60,
            )
            return

        body = bytearray()
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            body.extend(message.get("body") or b"")
            if len(body) > self.max_body_bytes:
                await self._json_response(send, 413, "Request body is too large.")
                return
            if not message.get("more_body", False):
                break

        delivered = False

        async def replay_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            # StreamingResponse listens for a real client disconnect after reading
            # the request body; do not synthesize one or SSE will stop immediately.
            return await receive()

        acquired = False
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.acquire_timeout_ms / 1000.0,
            )
            acquired = True
        except TimeoutError:
            await self._json_response(
                send,
                503,
                "The assistant is busy. Please try again shortly.",
                retry_after=2,
            )
            return

        try:
            await self.app(scope, replay_receive, send)
        finally:
            if acquired:
                self._semaphore.release()
