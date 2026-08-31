from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from overseer_api.main import app
from overseer_core import runner_catalog, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    monkeypatch.setenv("OVERSEER_API_TOKEN", "test-token")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def _write_catalog(root: Path) -> None:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "linux-host.yaml").write_text(
        yaml.dump(
            {
                "pipelines": [
                    {
                        "id": "demo_pipe",
                        "name": "Demo",
                        "owner": "data",
                        "schedule": "manual",
                        "steps": [{"module_id": "demo_pipe", "command": ["echo", "ok"]}],
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_catalog_payload_from_yaml_honours_depends_on() -> None:
    entry = {
        "pipeline_id": "etl",
        "name": "ETL",
        "owner": "data",
        "schedule": "manual",
        "steps": [
            {"module_id": "extract", "command": ["echo", "e"]},
            {"module_id": "transform", "command": ["echo", "t"], "depends_on": "extract"},
            {"module_id": "load", "command": ["echo", "l"], "depends_on": ["transform"]},
        ],
    }
    payload = store._catalog_payload_from_yaml_entry(entry, "LINUX-HOST", "linux-host")
    assert payload["edges"] == [
        {"from_module_id": "extract", "to_module_id": "transform"},
        {"from_module_id": "transform", "to_module_id": "load"},
    ]


def test_catalog_payload_from_yaml_includes_command_and_edges() -> None:
    entry = {
        "pipeline_id": "demo_pipe",
        "name": "Demo",
        "owner": "data",
        "schedule": "manual",
        "steps": [
            {"module_id": "step_a", "command": ["python3", "/tmp/a.py"], "cwd": "/tmp"},
            {"module_id": "step_b", "command": ["python3", "/tmp/b.py"]},
        ],
    }
    payload = store._catalog_payload_from_yaml_entry(entry, "LINUX-HOST", "linux-host")
    assert payload["nodes"][0]["metadata"]["command"] == ["python3", "/tmp/a.py"]
    assert payload["nodes"][0]["metadata"]["cwd"] == "/tmp"
    assert payload["edges"] == [{"from_module_id": "step_a", "to_module_id": "step_b"}]


def test_reconcile_registers_yaml_pipelines(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    result = store.reconcile_catalog_from_yaml()
    assert len(result["created"]) == 1
    row = store.get_pipeline("demo_pipe", "LINUX-HOST")
    assert row is not None
    assert row["owner"] == "data"


def test_reconcile_updates_legacy_pipeline_row(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo_pipe",
            "host_id": "",
            "name": "Legacy",
            "owner": "old",
            "nodes": [{"module_id": "demo_pipe"}],
            "edges": [],
        }
    )
    result = store.reconcile_catalog_from_yaml()
    assert result["updated"]
    row = store.get_pipeline("demo_pipe", "LINUX-HOST")
    assert row is not None
    assert row["owner"] == "old"
    with store.get_engine().connect() as connection:
        legacy = connection.execute(
            store.pipelines_table.select().where(
                (store.pipelines_table.c.pipeline_id == "demo_pipe")
                & (store.pipelines_table.c.host_id == "")
            )
        ).first()
    assert legacy is None


def test_reconcile_preserves_patched_owner(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    store.reconcile_catalog_from_yaml()
    store.patch_pipeline_catalog("demo_pipe", "LINUX-HOST", {"owner": "operator"})
    store.reconcile_catalog_from_yaml()
    row = store.get_pipeline("demo_pipe", "LINUX-HOST")
    assert row is not None
    assert row["owner"] == "operator"
    deployments = store.list_deployments()
    match = next((d for d in deployments if d.get("pipeline_id") == "demo_pipe"), None)
    assert match is not None
    assert match["owner"] == "operator"


def test_sync_pipeline_yaml_from_db_exports_owner_and_steps(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    store.reconcile_catalog_from_yaml()
    store.patch_pipeline_catalog("demo_pipe", "LINUX-HOST", {"owner": "operator", "name": "Demo Renamed"})
    runner_catalog.sync_pipeline_yaml_from_db("linux-host", "demo_pipe", root=tmp_path)
    catalog = yaml.safe_load((tmp_path / "deploy" / "runners" / "linux-host.yaml").read_text(encoding="utf-8"))
    entry = catalog["pipelines"][0]
    assert entry["owner"] == "operator"
    assert entry["name"] == "Demo Renamed"
    assert entry["steps"][0]["module_id"] == "demo_pipe"


def test_reconcile_exports_yaml_from_db(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    store.reconcile_catalog_from_yaml()
    store.patch_pipeline_catalog("demo_pipe", "LINUX-HOST", {"owner": "operator"})
    store.reconcile_catalog_from_yaml()
    catalog = yaml.safe_load((tmp_path / "deploy" / "runners" / "linux-host.yaml").read_text(encoding="utf-8"))
    assert catalog["pipelines"][0]["owner"] == "operator"


def test_reconcile_api_endpoint(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    client = TestClient(app)
    response = client.post(
        "/v1/catalog/reconcile",
        json={"sync_remote": False},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert len(payload["reconcile"]["created"]) == 1
