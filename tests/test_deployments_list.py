from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from overseer_core import store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def _write_baze2_catalog(root: Path) -> None:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "baze2.yaml").write_text(
        yaml.dump(
            {
                "pipelines": [
                    {
                        "id": "traffic_flow",
                        "name": "Traffic Flow",
                        "owner": "data",
                        "criticality": "medium",
                        "schedule": "*/15 * * * *",
                        "steps": [{"module_id": "traffic_flow", "command": ["python3", "x.py"]}],
                    },
                    {
                        "id": "backup_baze2",
                        "name": "Backup",
                        "owner": "ops",
                        "criticality": "high",
                        "schedule": "0 2 * * *",
                        "steps": [{"module_id": "backup_baze2", "command": ["python3", "b.py"]}],
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_list_deployments_merges_yaml_and_runs(sqlite_store, tmp_path: Path) -> None:
    _write_baze2_catalog(tmp_path)
    store.start_run({"pipeline_id": "traffic_flow", "host_id": "baze2", "pipeline_name": "Traffic Flow"})
    rows = store.list_deployments()
    ids = {row["pipeline_id"] for row in rows}
    assert "traffic_flow" in ids
    assert "backup_baze2" in ids
    traffic = next(row for row in rows if row["pipeline_id"] == "traffic_flow")
    assert traffic["host_id"] == "BAZE2"
    assert traffic["last_status"] == "running"
    assert traffic["catalog_source"] in {"yaml", "db", "runs_only"}


def test_list_deployments_excludes_health_probe(sqlite_store, tmp_path: Path) -> None:
    store.start_run({"pipeline_id": "health_probe", "host_id": "baze2"})
    rows = store.list_deployments()
    assert not any(row["pipeline_id"] == "health_probe" for row in rows)


def test_list_deployments_db_overrides_yaml_metadata(sqlite_store, tmp_path: Path) -> None:
    _write_baze2_catalog(tmp_path)
    store.register_pipeline_catalog(
        {
            "pipeline_id": "traffic_flow",
            "host_id": "baze2",
            "name": "Traffic Flow",
            "owner": "platform",
            "schedule": "manual",
            "criticality": "high",
            "nodes": [{"module_id": "traffic_flow"}],
            "edges": [],
        }
    )
    row = next(item for item in store.list_deployments() if item["pipeline_id"] == "traffic_flow")
    assert row["owner"] == "platform"
    assert row["catalog_source"] == "db"
