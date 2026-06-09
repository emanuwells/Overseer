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
