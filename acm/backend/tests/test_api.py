from pathlib import Path

from fastapi.testclient import TestClient

from acm.backend.app.main import create_app


def client_for(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "acm-test.sqlite3"))


def test_access_contract_covers_protected_and_editable_modules(tmp_path: Path):
    with client_for(tmp_path) as client:
        response = client.get("/api/acm/access-contract")
        assert response.status_code == 200
        modules = {item["module"]: item for item in response.json()["modules"]}
        assert modules["Projects"]["mode"] == "managed"
        assert modules["Audit"]["mode"] == "immutable"
        assert modules["Finance"]["mode"] == "workflow"


def test_project_owner_can_update_managed_fields_and_writes_audit(tmp_path: Path):
    with client_for(tmp_path) as client:
        response = client.patch(
            "/api/acm/projects/proj-ask-2",
            headers={
                "X-ACM-Actor": "Prince Pudasaini",
                "X-ACM-Role": "project_manager",
            },
            json={
                "progressPercent": 67,
                "nextMilestone": "Complete retrieval evaluation",
                "reason": "Evaluation evidence is now ready for the next review.",
            },
        )
        assert response.status_code == 200
        assert response.json()["progressPercent"] == 67

        audit = client.get(
            "/api/acm/audit",
            headers={"X-ACM-Role": "president"},
        )
        assert audit.status_code == 200
        assert audit.json()[0]["action"] == "PROJECT_UPDATED"
        assert audit.json()[0]["reason"].startswith("Evaluation evidence")


def test_project_manager_cannot_edit_another_owners_project(tmp_path: Path):
    with client_for(tmp_path) as client:
        response = client.patch(
            "/api/acm/projects/proj-hack",
            headers={
                "X-ACM-Actor": "Prince Pudasaini",
                "X-ACM-Role": "project_manager",
            },
            json={
                "progressPercent": 90,
                "reason": "Attempting an edit outside the assigned project scope.",
            },
        )
        assert response.status_code == 403


def test_reason_is_required_for_managed_project_edits(tmp_path: Path):
    with client_for(tmp_path) as client:
        response = client.patch(
            "/api/acm/projects/proj-ask-2",
            headers={
                "X-ACM-Actor": "Prince Pudasaini",
                "X-ACM-Role": "project_manager",
            },
            json={"progressPercent": 70},
        )
        assert response.status_code == 422