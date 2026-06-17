from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from overseer_sdk.slack_notifier import SlackNotifier


# ------------------------------------------------------------------
# __init__ / config
# ------------------------------------------------------------------


def test_init_no_config() -> None:
    notifier = SlackNotifier()
    assert notifier.webhook_url is None
    assert notifier.channel is None
    assert notifier.is_enabled is False


def test_init_with_config_dict() -> None:
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x", "channel": "#test"})
    assert notifier.webhook_url == "https://hooks.slack.com/x"
    assert notifier.channel == "#test"
    assert notifier.is_enabled is True


def test_init_with_config_dict_no_webhook() -> None:
    notifier = SlackNotifier(config={"channel": "#test"})
    assert notifier.is_enabled is False


def test_init_with_config_path(tmp_path: Path) -> None:
    cfg = tmp_path / "slack.json"
    cfg.write_text(json.dumps({"webhook_url": "https://hooks.slack.com/y"}), encoding="utf-8")
    notifier = SlackNotifier(config_path=cfg)
    assert notifier.webhook_url == "https://hooks.slack.com/y"
    assert notifier.is_enabled is True


def test_init_config_path_not_found(tmp_path: Path) -> None:
    notifier = SlackNotifier(config_path=tmp_path / "missing.json")
    assert notifier.is_enabled is False


def test_init_config_path_invalid_json(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.json"
    cfg.write_text("not json!", encoding="utf-8")
    notifier = SlackNotifier(config_path=cfg)
    assert notifier.is_enabled is False


# ------------------------------------------------------------------
# send_message
# ------------------------------------------------------------------


def test_send_message_disabled() -> None:
    notifier = SlackNotifier()
    assert notifier.send_message("hello") is False


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_message_success(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    assert notifier.send_message("hello") is True
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert payload["text"] == "hello"


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_message_with_channel(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x", "channel": "#ops"})
    notifier.send_message("hello")
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert payload["channel"] == "#ops"


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_message_with_blocks(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "test"}}]
    notifier.send_message("hello", blocks=blocks)
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert payload["blocks"] == blocks


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_message_http_error(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "server error"
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    assert notifier.send_message("hello") is False


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_message_network_error(mock_post: MagicMock) -> None:
    from requests import ConnectionError
    mock_post.side_effect = ConnectionError("network down")
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    assert notifier.send_message("hello") is False


# ------------------------------------------------------------------
# notify_run
# ------------------------------------------------------------------


def test_notify_run_disabled() -> None:
    notifier = SlackNotifier()
    notifier.notify_run(
        pipeline_name="test",
        status="ok",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
    )  # should not raise


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_success(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="ETL Pipeline",
        status="ok",
        stats={"records": 100, "errors": 0},
        start_time=datetime(2025, 6, 1, 10, 0, 0),
        end_time=datetime(2025, 6, 1, 10, 5, 30),
        hostname="prod-1",
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    text = payload["text"]
    assert "ETL Pipeline" in text
    assert "records" in text
    assert "prod-1" in text


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_failed_with_error(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="failed",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        error_message="Connection timeout to DB",
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "Connection timeout" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_with_run_url(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="ok",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        run_id="run-123",
        run_url="http://overseer/runs/run-123",
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "run-123" in payload["text"]
    assert "http://overseer/runs/run-123" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_with_run_id_no_url(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="ok",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        run_id="run-456",
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "run-456" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_with_error_events(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    events = [
        {"category": "db", "context": "insert", "message": "duplicate key"},
        {"category": "api", "context": "fetch", "message": "timeout"},
    ]
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="failed",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        error_events=events,
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "duplicate key" in payload["text"]
    assert "timeout" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_truncates_long_error(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="failed",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        error_message="x" * 300,
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert len(payload["text"]) < 600


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_with_extra_lines(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="ok",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        extra_lines=["Custom footer line"],
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "Custom footer line" in payload["text"]


@patch("overseer_sdk.slack_notifier.requests.post")
def test_notify_run_error_events_capped_at_five(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(config={"webhook_url": "https://hooks.slack.com/x"})
    events = [{"category": f"cat{i}", "context": "c", "message": f"msg{i}"} for i in range(10)]
    notifier.notify_run(
        pipeline_name="Pipeline",
        status="failed",
        stats={},
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 1),
        error_events=events,
    )
    payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
    assert "mais 5 erros" in payload["text"]
