from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from overseer_core import slack_digest, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def test_build_digest_text_includes_summary(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "baze2",
            "name": "Demo",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "demo", "host_id": "baze2"})
    store.finish_run(run["run_id"], {"status": "failed", "error_message": "test failure"})

    text = slack_digest.build_digest_text()
    assert "digest diário" in text.lower() or "digest" in text.lower()
    assert "demo" in text
    assert "em aberto" in text.lower() or "falhas" in text.lower()
    assert "<!channel>" in text


def test_build_digest_always_mentions_channel_without_failures(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "baze2",
            "name": "Demo",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "demo", "host_id": "baze2"})
    store.finish_run(run["run_id"], {"status": "ok"})

    text = slack_digest.build_digest_text()
    assert "<!channel>" in text
    assert "em aberto" not in text.lower() or "sem falhas" in text.lower()


def test_build_digest_includes_stale_deployments(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "medidata_pipeline",
            "host_id": "WS1207",
            "name": "Medidata Pipeline",
            "schedule": "30 7 * * *",
            "nodes": [{"module_id": "run_pipeline"}],
            "edges": [],
        }
    )
    run = store.start_run(
        {
            "pipeline_id": "medidata_pipeline",
            "host_id": "WS1207",
            "started_at": store.utcnow() - timedelta(hours=25),
        }
    )
    store.finish_run(run["run_id"], {"status": "ok"})

    text = slack_digest.build_digest_text()
    assert "pipelines stale" in text.lower()
    assert "medidata_pipeline" in text
    assert "WS1207" in text


def test_next_digest_at_0830(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_SLACK_DIGEST_HOUR", "8")
    monkeypatch.setenv("OVERSEER_SLACK_DIGEST_MINUTE", "30")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Lisbon")
    before = datetime(2026, 6, 10, 8, 0, tzinfo=tz)
    assert slack_digest.next_digest_at(before).strftime("%H:%M") == "08:30"
    after = datetime(2026, 6, 10, 9, 0, tzinfo=tz)
    assert slack_digest.next_digest_at(after).strftime("%Y-%m-%d %H:%M") == "2026-06-11 08:30"


@patch("overseer_sdk.slack_notifier.requests.post")
def test_send_daily_digest(mock_post: MagicMock, monkeypatch: pytest.MonkeyPatch, sqlite_store) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "ok"
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")
    monkeypatch.setenv("OVERSEER_SLACK_DIGEST_ENABLED", "true")
    assert slack_digest.send_daily_digest() is True
    mock_post.assert_called_once()
