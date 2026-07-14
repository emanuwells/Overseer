from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from overseer_core import slack_alerts, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_failed_run_mentions_channel(mock_post: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")
    monkeypatch.setenv("OVERSEER_SLACK_CHANNEL", "#overseer")
    monkeypatch.setenv("OVERSEER_SLACK_MENTION_CHANNEL", "true")

    run = {
        "run_id": "run-1",
        "pipeline_id": "demo",
        "host_id": "linux-host",
        "error_message": "boom",
        "duration_sec": 12,
    }
    assert slack_alerts.notify_failed_run(run) is True
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
    assert "<!channel>" in payload["text"]
    assert "FAILED" in payload["text"]


@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_finish_run_marks_slack_notified(mock_notify: MagicMock, sqlite_store) -> None:
    run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    finished = store.finish_run(run["run_id"], {"status": "failed", "error_message": "x"})
    assert finished["status"] == "failed"
    mock_notify.assert_called_once()
    updated = store.get_run(run["run_id"]) or {}
    assert updated.get("metadata", {}).get("slack_notified") is True


@patch("overseer_core.slack_alerts.notify_resolved_run", return_value=True)
@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_finish_run_ok_after_failed_notifies_resolved(
    _mock_fail: MagicMock,
    mock_resolve: MagicMock,
    sqlite_store,
) -> None:
    failed = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    store.finish_run(failed["run_id"], {"status": "failed", "error_message": "x"})
    ok_run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    store.finish_run(ok_run["run_id"], {"status": "ok"})
    mock_resolve.assert_called_once()


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_failed_run_disabled_without_webhook(mock_post: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OVERSEER_SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("OVERSEER_SLACK_CONFIG", "/nonexistent/slack.json")
    run = {"run_id": "run-2", "pipeline_id": "demo"}
    assert slack_alerts.notify_failed_run(run) is False
    mock_post.assert_not_called()
