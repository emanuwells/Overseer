from __future__ import annotations

from pathlib import Path

import pytest

from overseer_core import store


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
    assert rows[0]["host_id"] == "H1"
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
    assert store.list_runs(pipeline_id="p", host_id="a")[0]["host_id"] == "A"


def test_list_pipelines_one_row_per_host(sqlite_store) -> None:
    for host in ("baze2", "WS1207"):
        store.register_pipeline_catalog(
            {
                "pipeline_id": "medidata_pipeline",
                "host_id": host,
                "name": "Medidata Pipeline",
                "nodes": [{"module_id": "run", "label": "run"}],
                "edges": [],
            }
        )
        store.start_run({"pipeline_id": "medidata_pipeline", "host_id": host})
    rows = store.list_pipelines()
    assert len(rows) == 2
    hosts = {row["host_id"] for row in rows}
    assert hosts == {"BAZE2", "WS1207"}
    assert all(row["pipeline_id"] == "medidata_pipeline" for row in rows)


def test_list_pipelines_resolves_metadata_host_and_latest_run(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "medidata_pipeline",
            "name": "Medidata Pipeline",
            "owner": "data",
            "metadata": {"host_id": "WS1207"},
            "nodes": [{"module_id": "run", "label": "run"}],
            "edges": [],
        }
    )
    store.register_pipeline_catalog(
        {
            "pipeline_id": "medidata_pipeline__WS1207",
            "name": "Medidata Pipeline Legacy",
            "nodes": [{"module_id": "run", "label": "run"}],
            "edges": [],
        }
    )
    old = store.start_run({"pipeline_id": "medidata_pipeline", "host_id": "", "hostname": "ws1207"})
    store.finish_run(old["run_id"], {"status": "ok", "duration_sec": 10})
    latest = store.start_run({"pipeline_id": "medidata_pipeline", "host_id": "WS1207"})
    store.finish_run(latest["run_id"], {"status": "ok", "duration_sec": 20})

    rows = store.list_pipelines()
    medidata = [row for row in rows if row["pipeline_id"] == "medidata_pipeline"]
    assert len(medidata) == 1
    assert medidata[0]["host_id"] == "WS1207"
    assert medidata[0]["last_run_id"] == latest["run_id"]


def test_list_pipelines_merges_legacy_duplicate(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "medidata_pipeline",
            "host_id": "WS1207",
            "name": "Medidata Pipeline",
            "nodes": [{"module_id": "run", "label": "run"}],
            "edges": [],
        }
    )
    store.register_pipeline_catalog(
        {
            "pipeline_id": "medidata_pipeline__WS1207",
            "name": "Medidata Pipeline Legacy",
            "nodes": [{"module_id": "run", "label": "run"}],
            "edges": [],
        }
    )
    store.start_run({"pipeline_id": "medidata_pipeline", "host_id": "WS1207"})
    rows = store.list_pipelines()
    assert len(rows) == 1
    assert rows[0]["pipeline_id"] == "medidata_pipeline"
    assert rows[0]["host_id"] == "WS1207"
