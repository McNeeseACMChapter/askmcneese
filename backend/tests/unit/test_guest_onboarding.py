from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.routers import guest as guest_router
from app.services.guest.store import GuestStore


class GuestStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GuestStore(Path(self.tmp.name) / "guest.sqlite3")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bootstrap_is_idempotent_for_same_token(self) -> None:
        first, token = self.store.bootstrap(None)
        self.assertIsNotNone(token)
        self.assertTrue(first["isNewAssignment"])
        self.assertEqual(len(first["displayAlias"]), 4)
        second, again = self.store.bootstrap(token)
        self.assertIsNone(again)
        self.assertEqual(first["guestId"], second["guestId"])
        self.assertFalse(second["isNewAssignment"])
        self.assertEqual(first["displayAlias"], second["displayAlias"])
        self.assertNotEqual(first["displayAlias"], first["guestId"])

    def test_tour_progress_and_completion(self) -> None:
        _, token = self.store.bootstrap(None)
        for step in (
            "welcome",
            "ask",
            "ask_input",
            "class_planner",
            "planner_week",
            "planner_find",
            "about",
            "about_scroll",
            "updates",
            "usage",
            "conversations",
            "home_banner",
            "settings",
            "feedback",
        ):
            state = self.store.update_tour(token, step=step)
            assert state is not None
            self.assertEqual(state["tour"]["currentStep"], step)
        done = self.store.update_tour(token, step="complete")
        assert done is not None
        self.assertEqual(done["tour"]["status"], "completed")
        again = self.store.update_tour(token, step="complete")
        assert again is not None
        self.assertEqual(again["tour"]["status"], "completed")

    def test_cannot_complete_early(self) -> None:
        _, token = self.store.bootstrap(None)
        self.store.update_tour(token, step="welcome")
        with self.assertRaises(ValueError):
            self.store.update_tour(token, step="complete")


class GuestApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GuestStore(Path(self.tmp.name) / "guest.sqlite3")
        guest_router._store.cache_clear()
        self.patcher = patch.object(guest_router, "_store", return_value=self.store)
        self.patcher.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.patcher.stop()
        guest_router._store.cache_clear()
        self.tmp.cleanup()

    def test_bootstrap_sets_cookie_once(self) -> None:
        first = self.client.post("/guest/bootstrap")
        self.assertEqual(first.status_code, 200)
        self.assertIn("askmcneese_guest", first.cookies)
        guest_id = first.json()["data"]["guestId"]
        second = self.client.post("/guest/bootstrap")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["data"]["guestId"], guest_id)

    def test_patch_and_post_tour_update(self) -> None:
        self.client.post("/guest/bootstrap")
        patched = self.client.patch("/guest/tour", json={"version": 1, "step": "welcome"})
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["data"]["tour"]["currentStep"], "welcome")
        posted = self.client.post("/guest/tour", json={"version": 1, "step": "ask"})
        self.assertEqual(posted.status_code, 200)
        self.assertEqual(posted.json()["data"]["tour"]["currentStep"], "ask")

    def test_cors_preflight_allows_patch(self) -> None:
        response = self.client.options(
            "/guest/tour",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        allow = response.headers.get("access-control-allow-methods", "")
        self.assertIn("PATCH", allow.upper())
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://127.0.0.1:5173")
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_replay_keeps_guest_identity(self) -> None:
        boot = self.client.post("/guest/bootstrap")
        guest_id = boot.json()["data"]["guestId"]
        alias = boot.json()["data"]["displayAlias"]
        self.client.patch("/guest/tour", json={"version": 1, "step": "welcome"})
        # Force completed-ish path via store helper through replay endpoint mid-tour.
        replayed = self.client.post("/guest/tour/replay")
        self.assertEqual(replayed.status_code, 200)
        data = replayed.json()["data"]
        self.assertEqual(data["guestId"], guest_id)
        self.assertEqual(data["displayAlias"], alias)
        self.assertEqual(data["tour"]["currentStep"], "welcome")
        self.assertEqual(data["tour"]["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
