from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from overseer_core import runner_catalog, runner_ssh, store


def test_runners_dir_uses_configured_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configured = tmp_path / "private-runners"
    monkeypatch.setenv("OVERSEER_RUNNERS_DIR", str(configured))

    assert runner_catalog.runners_dir(tmp_path / "repo") == configured


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
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


def test_resolve_catalog_host_id_case_insensitive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    _write_catalog(tmp_path, "linux-host", "demo")
    assert runner_ssh.resolve_catalog_host_id("LINUX-HOST", root=tmp_path) == "linux-host"
    assert runner_ssh.resolve_catalog_host_id("linux-host", root=tmp_path) == "linux-host"


def test_patch_runner_catalog_yaml_uppercase_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    _write_catalog(tmp_path, "linux-host", "demo")
    result = runner_catalog.patch_runner_catalog_yaml(
        "LINUX-HOST",
        "demo",
        {"owner": "ops"},
        root=tmp_path,
    )
    assert result["host_id"] == "linux-host"
    data = yaml.safe_load((tmp_path / "deploy" / "runners" / "linux-host.yaml").read_text(encoding="utf-8"))
    assert data["pipelines"][0]["owner"] == "ops"


def test_patch_runner_catalog_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    _write_catalog(tmp_path, "linux-host", "demo")
    result = runner_catalog.patch_runner_catalog_yaml(
        "linux-host",
        "demo",
        {"owner": "ops", "schedule": "0 2 * * *", "name": "Demo"},
        root=tmp_path,
    )
    assert "owner" in result["updated"]
    data = yaml.safe_load((tmp_path / "deploy" / "runners" / "linux-host.yaml").read_text(encoding="utf-8"))
    entry = data["pipelines"][0]
    assert entry["owner"] == "ops"
    assert entry["schedule"] == "0 2 * * *"
    assert entry["name"] == "Demo"


def test_pause_and_resume_schedule_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    path = _write_catalog(tmp_path, "linux-host", "demo")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["pipelines"][0]["schedule"] = "0 2 * * *"
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")

    runner_catalog.patch_runner_catalog_yaml("linux-host", "demo", {"schedule": "paused"}, root=tmp_path)
    paused = yaml.safe_load(path.read_text(encoding="utf-8"))["pipelines"][0]
    assert paused["schedule"] == "paused"
    assert paused["prev_schedule"] == "0 2 * * *"

    runner_catalog.patch_runner_catalog_yaml("linux-host", "demo", {"schedule": "0 3 * * *"}, root=tmp_path)
    resumed = yaml.safe_load(path.read_text(encoding="utf-8"))["pipelines"][0]
    assert resumed["schedule"] == "0 3 * * *"
    assert "prev_schedule" not in resumed


def test_patch_pipeline_catalog_pause_db(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "linux-host",
            "name": "Demo",
            "owner": "ops",
            "schedule": "0 1 * * *",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    dag = store.patch_pipeline_catalog("demo", "linux-host", {"schedule": "paused"})
    assert dag["pipeline"]["schedule"] == "paused"
    meta = dag["pipeline"].get("metadata") or {}
    assert meta.get("prev_schedule") == "0 1 * * *"


def test_patch_pipeline_catalog_db_only(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "demo",
            "host_id": "linux-host",
            "name": "Demo",
            "owner": "old",
            "schedule": "manual",
            "nodes": [{"module_id": "a"}],
            "edges": [],
        }
    )
    dag = store.patch_pipeline_catalog("demo", "linux-host", {"owner": "new-owner", "schedule": "0 3 * * *"})
    assert dag["pipeline"]["owner"] == "new-owner"
    assert dag["pipeline"]["schedule"] == "0 3 * * *"
    nodes = dag["nodes"]
    assert len(nodes) == 1


@patch("overseer_core.runner_ssh._run_local")
def test_sync_remote_runner_local(mock_run: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    monkeypatch.setenv("OVERSEER_SSH_SYNC_ENABLED", "1")
    _write_catalog(tmp_path, "linux-host", "demo")
    mock_run.return_value = {"command": "x", "exit_code": 0, "stdout": "ok", "stderr": ""}

    result = runner_ssh.sync_remote_runner("linux-host", schedule_changed=True, root=tmp_path)
    assert result["mode"] == "local"
    assert result["ok"] is True
    mock_run.assert_called_once()


@patch("overseer_core.runner_ssh._run_ssh")
def test_windows_sync_runs_schedule_script(mock_ssh: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    monkeypatch.setenv("OVERSEER_SSH_SYNC_ENABLED", "1")
    catalog_dir = tmp_path / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "windows-host.yaml").write_text("pipelines: []\n", encoding="utf-8")
    hosts = catalog_dir / "hosts.yaml"
    hosts.write_text(
        yaml.dump(
            {
                "hosts": {
                    "windows-host": {
                        "ssh": "user@winhost",
                        "platform": "windows",
                        "repo_path": r"C:\Tools\Overseer",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    mock_ssh.return_value = {"command": "x", "exit_code": 0, "stdout": "ok", "stderr": ""}

    cfg = runner_ssh.get_host_config("windows-host", tmp_path)
    command = runner_ssh.build_sync_command("windows-host", cfg, schedule_changed=True)
    assert "update-taskscheduler-schedule.ps1" in command
    runner_ssh.sync_remote_runner("windows-host", schedule_changed=True, root=tmp_path)
    mock_ssh.assert_called_once()
    assert "update-taskscheduler-schedule.ps1" in mock_ssh.call_args[0][1]
    assert "FromBase64String" in mock_ssh.call_args[0][1]


def test_linux_sync_embeds_private_catalog() -> None:
    command = runner_ssh.build_sync_command(
        "host-a",
        {"ssh": "user@host-a", "platform": "linux", "repo_path": "/srv/overseer"},
        schedule_changed=False,
        catalog_payload=b"pipelines: []\n",
    )

    assert "base64 -d" in command
    assert "/tmp/overseer-host-a.yaml" in command
