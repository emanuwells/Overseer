from __future__ import annotations

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
