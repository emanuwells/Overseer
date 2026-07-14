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


def test_build_digest_text_operations_style(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "linux-host",
            "name": "Demo",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    store.finish_run(run["run_id"], {"status": "failed", "error_message": "test failure"})

    text = slack_digest.build_digest_text()
    assert "Overseer Daily Digest" in text
    assert ":gear: *Pipelines*" in text
    assert ":arrow_forward: *Runs por pipeline (24h)*" in text
    assert ":rotating_light: *Falhas em aberto*" in text
    assert "Falha(s) em aberto" in text or "falha(s) em aberto" in text.lower() or "`Demo`" in text
    assert "<!channel>" in text


def test_build_digest_does_not_mention_channel_without_actionable_issues(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "linux-host",
            "name": "Demo",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    store.finish_run(run["run_id"], {"status": "ok"})

    text = slack_digest.build_digest_text()
    assert "<!channel>" not in text
    assert ":gear: *Pipelines*" in text
    assert "`nenhuma`" in text or ":warning:" in text or ":white_check_mark:" in text


def test_build_digest_omits_heartbeats_and_queued_triggers(sqlite_store) -> None:
    store.record_heartbeat({"source_id": "runner-a", "host_id": "host-a", "api_reachable": True})
    store.enqueue_trigger({"pipeline_id": "demo", "host_id": "host-a", "requested_by": "test"})

    text = slack_digest.build_digest_text()

    assert "heartbeats" not in text.lower()
    assert "triggers em fila" not in text.lower()
    assert "runner-a" not in text


def test_build_digest_includes_stale_deployments(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "example_pipeline",
            "host_id": "windows-host",
            "name": "Example Pipeline",
            "schedule": "30 7 * * *",
            "nodes": [{"module_id": "run_pipeline"}],
            "edges": [],
        }
    )
    run = store.start_run(
        {
            "pipeline_id": "example_pipeline",
            "host_id": "windows-host",
            "started_at": store.utcnow() - timedelta(hours=25),
        }
    )
    store.finish_run(run["run_id"], {"status": "ok"})

    text = slack_digest.build_digest_text()
    assert ":hourglass_flowing_sand: *Stale" in text
    assert "Example" in text or "example" in text.lower() or "`nenhum`" in text


def test_build_digest_normalizes_yunex_pipeline_name(sqlite_store) -> None:
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
    store.finish_run(run["run_id"], {"status": "failed", "error_message": "x"})

    text = slack_digest.build_digest_text()
    assert "`Traffic Flow`" in text
    assert "Yunex Traffic Flow" not in text


def test_build_digest_lists_runs_per_pipeline(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "weather_pipeline",
            "host_id": "linux-host",
            "name": "Weather",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    for _ in range(3):
        run = store.start_run({"pipeline_id": "weather_pipeline", "host_id": "linux-host"})
        store.finish_run(run["run_id"], {"status": "ok"})

    text = slack_digest.build_digest_text()
    assert "`3` run(s)" in text
    assert "weather_pipeline" in text or "Weather" in text


def test_aggregate_runs_by_deployment(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "a",
            "host_id": "h1",
            "name": "A",
            "nodes": [{"module_id": "m"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "a", "host_id": "h1"})
    store.finish_run(run["run_id"], {"status": "ok"})
    rows = slack_digest.aggregate_runs_by_deployment(slack_digest.runs_last_24h())
    assert len(rows) == 1
    assert rows[0]["total"] == 1
    assert rows[0]["ok"] == 1


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
    monkeypatch.setenv("OVERSEER_SLACK_WEBHOOK_URL", "https://example.invalid/slack/webhook/test")
    monkeypatch.setenv("OVERSEER_SLACK_DIGEST_ENABLED", "true")
    assert slack_digest.send_daily_digest() is True
    mock_post.assert_called_once()
