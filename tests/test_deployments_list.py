from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from sqlalchemy import insert

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


def _write_linux_host_catalog(root: Path) -> None:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "linux-host.yaml").write_text(
        yaml.dump(
            {
                "pipelines": [
                    {
                        "id": "scheduled_pipeline",
                        "name": "Scheduled Pipeline",
                        "owner": "data",
                        "criticality": "medium",
                        "schedule": "*/15 * * * *",
                        "steps": [{"module_id": "scheduled_pipeline", "command": ["python3", "x.py"]}],
                    },
                    {
                        "id": "operations_db_backup",
                        "name": "Operations DB Backup",
                        "owner": "ops",
                        "criticality": "high",
                        "schedule": "0 2 * * *",
                        "steps": [{"module_id": "operations_db_backup", "command": ["python3", "b.py"]}],
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_windows_host_catalog(root: Path) -> None:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "windows-host.yaml").write_text(
        yaml.dump(
            {
                "pipelines": [
                    {
                        "id": "example_pipeline",
                        "name": "Example Pipeline",
                        "owner": "operator",
                        "criticality": "medium",
                        "schedule": "30 7 * * *",
                        "steps": [{"module_id": "run_pipeline", "command": ["python", "run_pipeline.py"]}],
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_list_deployments_merges_yaml_and_runs(sqlite_store, tmp_path: Path) -> None:
    _write_linux_host_catalog(tmp_path)
    store.start_run({"pipeline_id": "scheduled_pipeline", "host_id": "linux-host", "pipeline_name": "Scheduled Pipeline"})
    rows = store.list_deployments()
    ids = {row["pipeline_id"] for row in rows}
    assert "scheduled_pipeline" in ids
    assert "operations_db_backup" in ids
    traffic = next(row for row in rows if row["pipeline_id"] == "scheduled_pipeline")
    assert traffic["host_id"] == "LINUX-HOST"
    assert traffic["last_status"] == "running"
    assert traffic["catalog_source"] in {"yaml", "db", "runs_only"}


def test_list_deployments_marks_windows_daily_pipeline_without_runs_as_stale(
    sqlite_store,
    tmp_path: Path,
) -> None:
    _write_windows_host_catalog(tmp_path)
    rows = store.list_deployments()
    example = next(row for row in rows if row["pipeline_id"] == "example_pipeline")
    assert example["host_id"] == "WINDOWS-HOST"
    assert example["schedule"] == "30 7 * * *"
    assert example["is_stale"] is True
    assert example["is_at_risk"] is True


def test_list_deployments_excludes_health_probe(sqlite_store, tmp_path: Path) -> None:
    store.start_run({"pipeline_id": "health_probe", "host_id": "linux-host"})
    rows = store.list_deployments()
    assert not any(row["pipeline_id"] == "health_probe" for row in rows)


def test_list_deployments_manual_pipeline_never_stale(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "adhoc_job",
            "host_id": "linux-host",
            "name": "Adhoc Job",
            "owner": "platform",
            "schedule": "manual",
            "criticality": "low",
            "nodes": [{"module_id": "adhoc_job"}],
            "edges": [],
        }
    )
    rows = store.list_deployments()
    manual = next(row for row in rows if row["pipeline_id"] == "adhoc_job")
    assert manual["schedule"] == "manual"
    assert manual["is_stale"] is False
    assert manual["is_at_risk"] is False


def test_list_deployments_db_overrides_yaml_metadata(sqlite_store, tmp_path: Path) -> None:
    _write_linux_host_catalog(tmp_path)
    store.register_pipeline_catalog(
        {
            "pipeline_id": "scheduled_pipeline",
            "host_id": "linux-host",
            "name": "Scheduled Pipeline",
            "owner": "platform",
            "schedule": "manual",
            "criticality": "high",
            "nodes": [{"module_id": "scheduled_pipeline"}],
            "edges": [],
        }
    )
    row = next(item for item in store.list_deployments() if item["pipeline_id"] == "scheduled_pipeline")
    assert row["owner"] == "platform"
    assert row["catalog_source"] == "db"
    assert row["schedule"] == "*/15 * * * *"


def test_list_deployments_slow_pipeline_not_starved_by_noise(sqlite_store, tmp_path: Path) -> None:
    """Um pipeline semanal não pode ficar "invisível" só por outras apps
    gerarem milhares de runs recentes (ver fix da leitura global top-1000)."""
    store.register_pipeline_catalog(
        {
            "pipeline_id": "warden_system_info",
            "host_id": "baze2",
            "name": "Warden System Info",
            "owner": "eferreira",
            "schedule": "0 2 * * 1",
            "criticality": "medium",
            "nodes": [{"module_id": "warden_system_info"}],
            "edges": [],
        }
    )
    now = store.utcnow()
    old_started = now - timedelta(days=4)
    rows = [
        {
            "run_id": "run-old-warden-system-info",
            "pipeline_id": "warden_system_info",
            "host_id": "BAZE2",
            "pipeline_name": "Warden System Info",
            "status": "ok",
            "trigger_type": "cron",
            "started_at": old_started,
            "ended_at": old_started + timedelta(minutes=2),
            "duration_sec": 120.0,
            "created_at": old_started,
            "updated_at": old_started,
            "run_local_id": 1,
        }
    ] + [
        {
            "run_id": f"run-noise-{i}",
            "pipeline_id": "noisy_pipeline",
            "host_id": "NOISY-HOST",
            "pipeline_name": "Noisy Pipeline",
            "status": "ok",
            "trigger_type": "cron",
            "started_at": now - timedelta(seconds=i),
            "ended_at": now - timedelta(seconds=i) + timedelta(seconds=1),
            "duration_sec": 1.0,
            "created_at": now,
            "updated_at": now,
            "run_local_id": i + 2,
        }
        for i in range(1500)
    ]
    with store.get_engine().begin() as conn:
        conn.execute(insert(store.runs_table), rows)

    row = next(item for item in store.list_deployments() if item["pipeline_id"] == "warden_system_info")
    assert row["stale_hours"] is not None
    assert 90 <= row["stale_hours"] <= 100
    assert row["is_stale"] is False


def test_list_deployments_db_schedule_overrides_yaml_when_explicit(sqlite_store, tmp_path: Path) -> None:
    _write_linux_host_catalog(tmp_path)
    store.register_pipeline_catalog(
        {
            "pipeline_id": "operations_db_backup",
            "host_id": "linux-host",
            "name": "Operations DB Backup",
            "owner": "ops",
            "schedule": "0 8 * * *",
            "criticality": "high",
            "nodes": [{"module_id": "operations_db_backup"}],
            "edges": [],
        }
    )
    row = next(item for item in store.list_deployments() if item["pipeline_id"] == "operations_db_backup")
    assert row["schedule"] == "0 8 * * *"
