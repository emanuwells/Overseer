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
def test_notify_failed_run_mentions_channel(
    mock_post: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_store,
) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://example.invalid/slack/webhook/test")
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
    assert "aviso imediato 1/3" in payload["text"]
    assert "passará para o digest" not in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_third_failed_alert_announces_digest(
    mock_post: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_store,
) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://example.invalid/slack/webhook/test")
    run = {"run_id": "run-3", "pipeline_id": "demo", "host_id": "linux-host"}

    assert slack_alerts.notify_failed_run(run, alert_number=3) is True

    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
    assert "aviso imediato 3/3" in payload["text"]
    assert "último aviso imediato" in payload["text"]
    assert "passará para o digest diário" in payload["text"]


@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_finish_run_marks_slack_notified(mock_notify: MagicMock, sqlite_store) -> None:
    run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    finished = store.finish_run(run["run_id"], {"status": "failed", "error_message": "x"})
    assert finished["status"] == "failed"
    mock_notify.assert_called_once()
    assert mock_notify.call_args.kwargs["alert_number"] == 1
    updated = store.get_run(run["run_id"]) or {}
    assert updated.get("metadata", {}).get("slack_notified") is True
    assert updated.get("metadata", {}).get("slack_alert_number") == 1


@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_failure_episode_sends_only_three_alerts_and_resets(
    mock_notify: MagicMock,
    sqlite_store,
) -> None:
    def finish(status: str) -> dict:
        run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
        return store.finish_run(run["run_id"], {"status": status, "error_message": "x"})

    failed_runs = [finish("failed") for _ in range(5)]

    assert [call.kwargs["alert_number"] for call in mock_notify.call_args_list] == [1, 2, 3]
    assert [run.get("metadata", {}).get("slack_notified") for run in failed_runs] == [
        True,
        True,
        True,
        None,
        None,
    ]

    finish("ok")
    finish("failed")
    assert mock_notify.call_args.kwargs["alert_number"] == 1


@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_failure_alert_limit_is_isolated_by_host(
    mock_notify: MagicMock,
    sqlite_store,
) -> None:
    for _ in range(3):
        run = store.start_run({"pipeline_id": "demo", "host_id": "host-a"})
        store.finish_run(run["run_id"], {"status": "failed"})

    other_host = store.start_run({"pipeline_id": "demo", "host_id": "host-b"})
    store.finish_run(other_host["run_id"], {"status": "failed"})

    assert [call.kwargs["alert_number"] for call in mock_notify.call_args_list] == [1, 2, 3, 1]


@patch("overseer_core.slack_alerts.notify_failed_run", return_value=True)
def test_legacy_unnumbered_notifications_do_not_consume_new_alerts(
    mock_notify: MagicMock,
    sqlite_store,
) -> None:
    for _ in range(4):
        run = store.start_run(
            {
                "pipeline_id": "legacy",
                "host_id": "linux-host",
                "metadata": {"slack_notified": True},
            }
        )
        store.finish_run(run["run_id"], {"status": "failed"})

    current = store.start_run({"pipeline_id": "legacy", "host_id": "linux-host"})
    store.finish_run(current["run_id"], {"status": "failed"})

    mock_notify.assert_called_once()
    assert mock_notify.call_args.kwargs["alert_number"] == 1


@patch("overseer_core.slack_alerts.notify_failed_run", side_effect=[False, True, True, True])
def test_failed_slack_delivery_does_not_consume_an_alert(
    mock_notify: MagicMock,
    sqlite_store,
) -> None:
    for _ in range(4):
        run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
        store.finish_run(run["run_id"], {"status": "failed"})

    assert [call.kwargs["alert_number"] for call in mock_notify.call_args_list] == [1, 1, 2, 3]


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
def test_notify_failed_run_uses_canonical_pipeline_name(
    mock_post: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_store,
) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://example.invalid/slack/webhook/test")
    store.register_pipeline_catalog(
        {
            "pipeline_id": "traffic_flow",
            "host_id": "linux-host",
            "name": "Traffic Flow",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    run = store.start_run(
        {
            "pipeline_id": "traffic_flow",
            "host_id": "linux-host",
            "pipeline_name": "Yunex Traffic Flow",
        }
    )
    store.finish_run(run["run_id"], {"status": "failed", "error_message": "boom"})
    finished = store.get_run(run["run_id"]) or {}
    assert slack_alerts.notify_failed_run(finished) is True
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
    assert "`Traffic Flow`" in payload["text"]
    assert "Yunex Traffic Flow" not in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_resolved_run_mentions_channel(
    mock_post: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_store,
) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://example.invalid/slack/webhook/test")
    monkeypatch.setenv("OVERSEER_SLACK_MENTION_CHANNEL", "true")

    ok_run = {"run_id": "run-ok", "pipeline_id": "demo", "host_id": "linux-host"}
    failed_run = {"run_id": "run-fail", "pipeline_id": "demo", "host_id": "linux-host"}
    assert slack_alerts.notify_resolved_run(ok_run, failed_run) is True
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
    assert "<!channel>" in payload["text"]
    assert "RESOLVIDO" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_failed_run_disabled_without_webhook(mock_post: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OVERSEER_SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("OVERSEER_SLACK_CONFIG", "/nonexistent/slack.json")
    run = {"run_id": "run-2", "pipeline_id": "demo"}
    assert slack_alerts.notify_failed_run(run) is False
    mock_post.assert_not_called()
