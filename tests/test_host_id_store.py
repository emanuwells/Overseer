from __future__ import annotations

from pathlib import Path

import pytest

from src.overseer_core import store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def test_split_legacy_pipeline_id() -> None:
    assert store.split_legacy_pipeline_id("medidata_pipeline__WS1207") == ("medidata_pipeline", "WS1207")
    assert store.split_legacy_pipeline_id("forms_sync") == ("forms_sync", "")


def test_list_pipelines_one_row_per_deployment(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "h1",
            "name": "Demo",
            "nodes": [{"module_id": "a", "label": "A"}],
            "edges": [],
        }
    )
    store.start_run({"pipeline_id": "demo", "host_id": "h1"})
    store.start_run({"pipeline_id": "demo", "host_id": "h1"})
    rows = store.list_pipelines()
    assert len(rows) == 1
    assert rows[0]["host_id"] == "h1"
    assert rows[0]["last_duration_sec"] is None or isinstance(rows[0]["last_duration_sec"], (int, float))


def test_host_id_on_run_and_module(sqlite_store) -> None:
    run = store.start_run({"pipeline_id": "x__HOST1", "pipeline_name": "X"})
    assert run["pipeline_id"] == "x"
    assert run["host_id"] == "HOST1"
    mod = store.record_module(
        {
            "run_id": run["run_id"],
            "pipeline_id": "x",
            "host_id": "HOST1",
            "module_id": "step1",
            "status": "ok",
        }
    )
    assert mod["host_id"] == "HOST1"


def test_list_runs_filters_host(sqlite_store) -> None:
    store.start_run({"pipeline_id": "p", "host_id": "a"})
    store.start_run({"pipeline_id": "p", "host_id": "b"})
    assert len(store.list_runs(pipeline_id="p", host_id="a")) == 1
    assert store.list_runs(pipeline_id="p", host_id="a")[0]["host_id"] == "a"
