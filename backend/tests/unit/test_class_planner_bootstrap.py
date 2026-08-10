from unittest.mock import Mock

from app.services.class_planner import bootstrap


def test_bootstrap_syncs_only_missing_configured_terms(monkeypatch):
    monkeypatch.setenv("CLASS_BOOTSTRAP_TERM_IDS", "202660, 202680,202660")
    store = Mock()
    store.freshness.side_effect = [None, {"term": "202680"}]
    sync = Mock()
    monkeypatch.setattr(bootstrap, "sync_mcneese_term", sync)

    bootstrap.bootstrap_missing_terms(store=store)

    assert bootstrap.configured_terms() == ("202660", "202680")
    sync.assert_called_once_with("202660", store=store)


def test_startup_bootstrap_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CLASS_BOOTSTRAP_ON_START", raising=False)
    monkeypatch.setenv("CLASS_SYNC_TERM_ID", "202660")

    assert bootstrap.start_class_planner_bootstrap() is False
