"""Anonymous guest bootstrap and onboarding tour persistence."""

from __future__ import annotations

from functools import lru_cache
import logging
import os
import secrets

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services.guest.store import COOKIE_NAME, TOKEN_HEADER, GuestStore, TOUR_VERSION

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/guest", tags=["guest"])


class TourUpdateRequest(BaseModel):
    version: int = Field(default=TOUR_VERSION)
    step: str = Field(min_length=1, max_length=64)


class FeedbackRequest(BaseModel):
    category: str = Field(min_length=2, max_length=64)
    message: str = Field(min_length=10, max_length=4000)
    pageUrl: str | None = Field(default=None, max_length=500)


@lru_cache(maxsize=1)
def _store() -> GuestStore:
    return GuestStore.from_environment()


def _cookie_secure(request: Request) -> bool:
    configured = os.getenv("GUEST_COOKIE_SECURE", "").strip().lower()
    if configured:
        return configured in {"1", "true", "yes"}
    forwarded = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    return request.url.scheme == "https" or forwarded == "https"


def _token_from_request(request: Request) -> str | None:
    return request.headers.get(TOKEN_HEADER) or request.cookies.get(COOKIE_NAME)


def claim_question_allowance(request: Request) -> dict | None:
    """Consume one question for identified guests; preserve legacy API clients."""
    token = _token_from_request(request)
    if not token:
        return None
    state, allowed = _store().claim_question(token)
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session expired. Refresh and try again.")
    if not allowed:
        limit = state["usage"]["questionLimit"]
        raise HTTPException(
            status_code=429,
            detail=f"This beta guest has used all {limit} available questions.",
        )
    return state


def _set_guest_cookie(request: Request, response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(request),
        samesite="none" if _cookie_secure(request) else "lax",
        path="/",
    )


@router.post("/bootstrap")
def bootstrap(request: Request, response: Response) -> dict:
    store = _store()
    existing = _token_from_request(request)
    try:
        state, new_token = store.bootstrap(existing)
    except Exception:
        LOGGER.exception("guest bootstrap failed")
        raise HTTPException(status_code=500, detail="Unable to start guest session.") from None
    if new_token:
        _set_guest_cookie(request, response, new_token, store.cookie_max_age())
        # Cross-origin deployments cannot rely on third-party cookies. The raw
        # anonymous token is returned once and persisted by this browser only;
        # the database stores its hash.
        state = {**state, "guestToken": new_token}
    return {"data": state}


def _update_tour(body: TourUpdateRequest, request: Request) -> dict:
    store = _store()
    token = _token_from_request(request)
    try:
        state = store.update_tour(token, step=body.step, version=body.version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception:
        LOGGER.exception("guest tour update failed")
        raise HTTPException(status_code=500, detail="Unable to update tour progress.") from None
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}


@router.patch("/tour")
def update_tour_patch(body: TourUpdateRequest, request: Request) -> dict:
    return _update_tour(body, request)


@router.post("/tour")
def update_tour_post(body: TourUpdateRequest, request: Request) -> dict:
    """POST alias for clients/proxies that mishandle PATCH preflight."""
    return _update_tour(body, request)


@router.post("/tour/replay")
def replay_tour(request: Request) -> dict:
    """Replay walkthrough for the same guest (Settings). Does not mint a new identity."""
    store = _store()
    state = store.replay_tour(_token_from_request(request))
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}


@router.post("/tour/skip")
def skip_tour(request: Request) -> dict:
    store = _store()
    state = store.skip_tour(_token_from_request(request))
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}


@router.get("/usage")
def guest_usage(request: Request) -> dict:
    store = _store()
    token = _token_from_request(request)
    state, _ = store.bootstrap(token) if token else (None, None)
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}


@router.post("/feedback")
def submit_feedback(body: FeedbackRequest, request: Request) -> dict:
    store = _store()
    item = store.submit_feedback(
        _token_from_request(request),
        category=body.category.strip(),
        message=body.message.strip(),
        page_url=body.pageUrl,
    )
    if item is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": item}


@router.get("/feedback")
def read_feedback(
    limit: int = 100,
    admin_token: str | None = Header(default=None, alias="X-Feedback-Admin-Token"),
) -> dict:
    expected = os.getenv("FEEDBACK_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Feedback review access is not configured.")
    if not admin_token or not secrets.compare_digest(admin_token, expected):
        raise HTTPException(status_code=401, detail="Feedback review token required.")
    return {"data": _store().list_feedback(limit=limit)}


@router.post("/dev-reset")
def dev_reset(request: Request) -> dict:
    if os.getenv("ONBOARDING_DEV_RESET", "").lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=404, detail="Not found.")
    store = _store()
    state = store.reset_tour(_token_from_request(request))
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}
