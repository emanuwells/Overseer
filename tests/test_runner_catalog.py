from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from overseer_core import runner_catalog, runner_ssh, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def _write_catalog(root: Path, host_id: str, pipeline_id: str) -> Path:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    path = catalog_dir / f"{host_id}.yaml"
    path.write_text(
        yaml.dump(
            {
                "pipelines": [
                    {"id": pipeline_id, "name": "Old", "schedule": "manual", "steps": []},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    hosts = catalog_dir / "hosts.yaml"
    hosts.write_text(
        yaml.dump(
            {
                "hosts": {
                    host_id: {
                        "ssh": "user@localhost",
                        "platform": "linux",
                        "repo_path": str(root),
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_patch_runner_catalog_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    _write_catalog(tmp_path, "baze2", "demo")
    result = runner_catalog.patch_runner_catalog_yaml(
        "baze2",
        "demo",
        {"owner": "ops", "schedule": "0 2 * * *", "name": "Demo"},
        root=tmp_path,
    )
    assert "owner" in result["updated"]
    data = yaml.safe_load((tmp_path / "deploy" / "runners" / "baze2.yaml").read_text(encoding="utf-8"))
    entry = data["pipelines"][0]
    assert entry["owner"] == "ops"
    assert entry["schedule"] == "0 2 * * *"
    assert entry["name"] == "Demo"


def test_patch_pipeline_catalog_db_only(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "baze2",
            "name": "Demo",
            "owner": "old",
            "schedule": "manual",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    dag = store.patch_pipeline_catalog("demo", "baze2", {"owner": "new-owner", "schedule": "0 3 * * *"})
    assert dag["pipeline"]["owner"] == "new-owner"
    assert dag["pipeline"]["schedule"] == "0 3 * * *"
    nodes = dag["nodes"]
    assert len(nodes) == 1


@patch("overseer_core.runner_ssh._run_local")
def test_sync_remote_runner_local(mock_run: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    monkeypatch.setenv("OVERSEER_SSH_SYNC_ENABLED", "1")
    _write_catalog(tmp_path, "baze2", "demo")
    mock_run.return_value = {"command": "x", "exit_code": 0, "stdout": "ok", "stderr": ""}

    result = runner_ssh.sync_remote_runner("baze2", schedule_changed=True, root=tmp_path)
    assert result["mode"] == "local"
    assert result["ok"] is True
    mock_run.assert_called_once()
