from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from overseer_core import deployment_health, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def test_manual_schedule_never_stale() -> None:
    assert deployment_health.schedule_stale_threshold_hours("manual") is None
    assert not deployment_health.is_stale_deployment([], {"schedule": "manual"})


def test_daily_schedule_stale_threshold_is_24h() -> None:
    assert deployment_health.schedule_stale_threshold_hours("30 7 * * *") == 24.0


def test_daily_schedule_becomes_stale_after_24h() -> None:
    stale_started_at = store.utcnow() - timedelta(hours=25)
    fresh_started_at = store.utcnow() - timedelta(hours=23)

    assert deployment_health.is_stale_deployment(
        [{"started_at": stale_started_at}],
        {"schedule": "30 7 * * *"},
    )
    assert not deployment_health.is_stale_deployment(
        [{"started_at": fresh_started_at}],
        {"schedule": "30 7 * * *"},
    )


def test_active_scheduled_deployment_without_runs_is_stale() -> None:
    assert deployment_health.is_stale_deployment([], {"schedule": "30 7 * * *"})


def test_manual_running_over_24h_is_not_stale() -> None:
    stale_started_at = store.utcnow() - timedelta(hours=30)
    assert not deployment_health.is_stale_deployment(
        [{"started_at": stale_started_at, "status": "running"}],
        {"schedule": "manual"},
    )


def test_paused_schedule_never_stale() -> None:
    assert deployment_health.schedule_stale_threshold_hours("paused") is None
    assert not deployment_health.is_stale_deployment([], {"schedule": "paused"})


def test_enrich_deployment_flags(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "local",
            "name": "Demo Pipeline",
            "schedule": "manual",
            "nodes": [{"module_id": "a", "label": "A"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "demo", "host_id": "local"})
    store.finish_run(run["run_id"], {"status": "ok", "duration_sec": 1.0})
    deployments = store.list_deployments()
    demo = next(item for item in deployments if item["pipeline_id"] == "demo")
    assert demo["name"] == "Demo Pipeline"
    assert "is_stale" in demo
    assert demo["is_stale"] is False
    assert "risk_score" in demo
    assert demo["deployment_key"].lower() == "demo::local"


def test_overview_summary_telemetry(sqlite_store) -> None:
    store.start_run({"pipeline_id": "p1", "host_id": "h1", "pipeline_name": "P One"})
    data = store.overview()
    summary = data["summary"]
    assert "avg_cpu" in summary
    assert "p95_exec_time" in summary
    assert "at_risk" in summary
    assert "volume" in summary
    assert summary["retention_days"] == 30
    assert summary["first_run_label"] == summary["telemetry_since"]
    assert summary["total_runs"] == store.count_runs()


def test_telemetry_since_uses_oldest_run(sqlite_store) -> None:
    older = store.utcnow() - timedelta(days=10)
    newer = store.utcnow() - timedelta(days=1)
    run_old = store.start_run({"pipeline_id": "p1", "host_id": "h1"})
    run_new = store.start_run({"pipeline_id": "p2", "host_id": "h1"})
    with store.get_engine().begin() as conn:
        conn.execute(
            store.runs_table.update()
            .where(store.runs_table.c.run_id == run_old["run_id"])
            .values(started_at=older)
        )
        conn.execute(
            store.runs_table.update()
            .where(store.runs_table.c.run_id == run_new["run_id"])
            .values(started_at=newer)
        )
    assert store.telemetry_since_label() == older.strftime("%Y-%m-%d")
