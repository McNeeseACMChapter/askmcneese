from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import _cors_origins, app
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
        self.assertRegex(first["displayAlias"], r"^Guest [0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$")
        self.assertEqual(first["usage"], {"questionsUsed": 0, "questionLimit": 10, "questionsRemaining": 10})
        second, again = self.store.bootstrap(token)
        self.assertIsNone(again)
        self.assertEqual(first["guestId"], second["guestId"])
        self.assertFalse(second["isNewAssignment"])
        self.assertEqual(first["displayAlias"], second["displayAlias"])
        self.assertNotEqual(first["displayAlias"], first["guestId"])

    def test_separate_guests_receive_distinct_public_identities(self) -> None:
        first, first_token = self.store.bootstrap(None)
        second, second_token = self.store.bootstrap(None)
        self.assertNotEqual(first_token, second_token)
        self.assertNotEqual(first["guestId"], second["guestId"])
        self.assertNotEqual(first["displayAlias"], second["displayAlias"])

    def test_environment_uses_managed_database_for_durable_identity(self) -> None:
        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "postgresql://guest:secret@database.internal/askmcneese"},
        ):
            store = GuestStore.from_environment()
        self.assertTrue(store._is_postgres)

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

    def test_skip_marks_tour_complete_without_losing_identity(self) -> None:
        first, token = self.store.bootstrap(None)
        skipped = self.store.skip_tour(token)
        assert skipped is not None
        self.assertEqual(skipped["guestId"], first["guestId"])
        self.assertEqual(skipped["tour"]["status"], "completed")
        self.assertIsNone(skipped["tour"]["currentStep"])

    def test_question_limit_is_atomic_and_truthful(self) -> None:
        _, token = self.store.bootstrap(None)
        with patch.dict("os.environ", {"GUEST_QUESTION_LIMIT": "2"}):
            first, first_allowed = self.store.claim_question(token)
            second, second_allowed = self.store.claim_question(token)
            third, third_allowed = self.store.claim_question(token)
        self.assertTrue(first_allowed)
        self.assertTrue(second_allowed)
        self.assertFalse(third_allowed)
        assert first is not None and second is not None and third is not None
        self.assertEqual(first["usage"]["questionsUsed"], 1)
        self.assertEqual(second["usage"]["questionsRemaining"], 0)
        self.assertEqual(third["usage"], second["usage"])

    def test_feedback_is_stored_and_reviewable(self) -> None:
        _, token = self.store.bootstrap(None)
        receipt = self.store.submit_feedback(
            token,
            category="bug",
            message="The walkthrough target is offset on mobile.",
            page_url="http://127.0.0.1:5173/ask",
        )
        assert receipt is not None
        rows = self.store.list_feedback()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], receipt["id"])
        self.assertEqual(rows[0]["category"], "bug")
        self.assertEqual(rows[0]["guestAlias"], self.store.bootstrap(token)[0]["displayAlias"])


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
                "Access-Control-Request-Headers": "content-type,x-guest-token",
            },
        )
        self.assertEqual(response.status_code, 200)
        allow = response.headers.get("access-control-allow-methods", "")
        self.assertIn("PATCH", allow.upper())
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://127.0.0.1:5173")
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_cors_keeps_custom_domain_when_render_environment_is_stale(self) -> None:
        with patch.dict(
            "os.environ",
            {"CORS_ALLOWED_ORIGINS": "https://askmcneese-1.onrender.com"},
            clear=False,
        ):
            origins = _cors_origins()

        self.assertIn("https://askmcneese-1.onrender.com", origins)
        self.assertIn("https://closedbeta.mcneeseacm.com", origins)

    def test_cors_preflight_allows_custom_production_domain(self) -> None:
        response = self.client.options(
            "/class-planner/terms",
            headers={
                "Origin": "https://closedbeta.mcneeseacm.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "https://closedbeta.mcneeseacm.com",
        )

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

    def test_header_token_works_when_cross_origin_cookie_is_unavailable(self) -> None:
        boot = self.client.post("/guest/bootstrap")
        token = boot.json()["data"]["guestToken"]
        header_client = TestClient(app)
        updated = header_client.post(
            "/guest/tour",
            headers={"X-Guest-Token": token},
            json={"version": 1, "step": "welcome"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["tour"]["currentStep"], "welcome")

    def test_skip_endpoint_and_feedback_admin_review(self) -> None:
        boot = self.client.post("/guest/bootstrap")
        token = boot.json()["data"]["guestToken"]
        skipped = self.client.post("/guest/tour/skip", headers={"X-Guest-Token": token})
        self.assertEqual(skipped.status_code, 200)
        self.assertEqual(skipped.json()["data"]["tour"]["status"], "completed")
        submitted = self.client.post(
            "/guest/feedback",
            headers={"X-Guest-Token": token},
            json={"category": "suggestion", "message": "Please add clearer class filters."},
        )
        self.assertEqual(submitted.status_code, 200)
        with patch.dict("os.environ", {"FEEDBACK_ADMIN_TOKEN": "review-secret"}):
            denied = self.client.get("/guest/feedback")
            reviewed = self.client.get(
                "/guest/feedback", headers={"X-Feedback-Admin-Token": "review-secret"}
            )
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(len(reviewed.json()["data"]), 1)


if __name__ == "__main__":
    unittest.main()
