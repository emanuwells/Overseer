from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.overseer_api.main import create_app
from src.overseer_core import monitoring_export, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_API_TOKEN", "")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def test_ops_fast_shape(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "local",
            "name": "Demo Pipeline",
            "owner": "data",
            "nodes": [{"module_id": "a", "label": "A"}],
            "edges": [],
        }
    )
    store.start_run({"pipeline_id": "demo", "host_id": "local", "requested_by": "test"})
    payload = monitoring_export.build_ops_fast_payload()
    assert "generated_at" in payload
    assert "summary" in payload
    assert "overview" in payload
    signals = payload["overview"]["operationalSignals"]
    assert "atRisk" in signals
    assert "stale" in signals
    assert payload["summary"]["total_runs"] >= 1


def test_full_payload_rows(sqlite_store) -> None:
    run = store.start_run({"pipeline_id": "p1", "host_id": "h1", "pipeline_name": "P One"})
    store.finish_run(run["run_id"], {"status": "ok", "duration_sec": 12.5})
    full = monitoring_export.build_full_payload()
    assert full["fields"] == monitoring_export.ROW_FIELDS
    assert len(full["rows"]) == 1
    assert full["rows"][0][full["fields"].index("pipelineId")] == "p1"
    assert full["orchestrator_runs"]


def test_monitoring_routes_public_ops(sqlite_store) -> None:
    client = TestClient(create_app())
    fast = client.get("/v1/monitoring/ops/fast")
    assert fast.status_code == 200
    body = fast.json()
    assert "summary" in body
    assert "overview" in body

    heavy = client.get("/v1/monitoring/ops/heavy")
    assert heavy.status_code == 200
    assert "rows" in heavy.json()


def test_module_lineage_latest_run_scoped(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "pipe",
            "host_id": "local",
            "name": "Pipe",
            "nodes": [
                {"module_id": "extract", "label": "Extract", "metadata": {"command": ["python3", "extract.py"]}},
                {"module_id": "load", "label": "Load", "metadata": {"command": ["python3", "load.py"]}},
            ],
            "edges": [{"from_module_id": "extract", "to_module_id": "load"}],
        }
    )
    run = store.start_run({"pipeline_id": "pipe", "host_id": "local"})
    store.record_module(
        {
            "run_id": run["run_id"],
            "pipeline_id": "pipe",
            "module_id": "extract",
            "status": "ok",
            "duration_sec": 1.0,
        }
    )
    store.finish_run(run["run_id"], {"status": "ok"})

    full = monitoring_export.build_full_payload()
    lineage = full["module_lineage"]["pipe"]
    levels = {node["id"]: node["lastEventLevel"] for node in lineage["nodes"]}
    assert levels["extract"] == "ok"
    assert levels["load"] == "inventory"
    scripts = full["pipeline_scripts"]["pipe"]
    assert len(scripts) == 2
    assert scripts[0]["executed"] is True
    assert scripts[1]["executed"] is False


def test_module_lineage_failed_module(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "fail_pipe",
            "host_id": "local",
            "nodes": [{"module_id": "step1", "label": "Step 1"}],
            "edges": [],
        }
    )
    run = store.start_run({"pipeline_id": "fail_pipe", "host_id": "local"})
    store.record_module(
        {
            "run_id": run["run_id"],
            "pipeline_id": "fail_pipe",
            "module_id": "step1",
            "status": "failed",
            "error_message": "boom",
        }
    )
    store.finish_run(run["run_id"], {"status": "failed", "error_message": "boom"})

    full = monitoring_export.build_full_payload()
    node = full["module_lineage"]["fail_pipe"]["nodes"][0]
    assert node["lastEventLevel"] == "error"
    assert node["lastMessage"] == "boom"


def test_purge_pipeline_data(sqlite_store) -> None:
    run = store.start_run({"pipeline_id": "p_monitor_recent", "host_id": "local"})
    store.record_module(
        {"run_id": run["run_id"], "pipeline_id": "p_monitor_recent", "module_id": "x", "status": "ok"}
    )
    store.record_log({"run_id": run["run_id"], "pipeline_id": "p_monitor_recent", "message": "log"})
    store.finish_run(run["run_id"], {"status": "ok"})

    dry = store.purge_pipeline_data("p_monitor_recent", dry_run=True)
    assert dry["runs"] == 1
    assert dry["modules"] == 1
    assert dry["logs"] == 1

    result = store.purge_pipeline_data("p_monitor_recent")
    assert result["runs"] == 1
    assert store.list_runs(pipeline_id="p_monitor_recent") == []
