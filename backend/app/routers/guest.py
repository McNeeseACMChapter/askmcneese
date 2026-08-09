"""Anonymous guest bootstrap and onboarding tour persistence."""

from __future__ import annotations

from functools import lru_cache
import logging
import os

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services.guest.store import COOKIE_NAME, GuestStore, TOUR_VERSION

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/guest", tags=["guest"])


class TourUpdateRequest(BaseModel):
    version: int = Field(default=TOUR_VERSION)
    step: str = Field(min_length=1, max_length=64)


@lru_cache(maxsize=1)
def _store() -> GuestStore:
    return GuestStore.from_environment()


def _cookie_secure() -> bool:
    return os.getenv("GUEST_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}


def _set_guest_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


@router.post("/bootstrap")
def bootstrap(request: Request, response: Response) -> dict:
    store = _store()
    existing = request.cookies.get(COOKIE_NAME)
    try:
        state, new_token = store.bootstrap(existing)
    except Exception:
        LOGGER.exception("guest bootstrap failed")
        raise HTTPException(status_code=500, detail="Unable to start guest session.") from None
    if new_token:
        _set_guest_cookie(response, new_token, store.cookie_max_age())
    return {"data": state}


def _update_tour(body: TourUpdateRequest, request: Request) -> dict:
    store = _store()
    token = request.cookies.get(COOKIE_NAME)
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
    state = store.replay_tour(request.cookies.get(COOKIE_NAME))
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}


@router.post("/dev-reset")
def dev_reset(request: Request) -> dict:
    if os.getenv("ONBOARDING_DEV_RESET", "").lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=404, detail="Not found.")
    store = _store()
    state = store.reset_tour(request.cookies.get(COOKIE_NAME))
    if state is None:
        raise HTTPException(status_code=401, detail="Guest session required.")
    return {"data": state}
