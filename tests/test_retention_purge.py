from __future__ import annotations

from pathlib import Path

import pytest

from overseer_core import store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "overseer.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path.as_posix()}")
    store._engine = None  # noqa: SLF001
    store.init_schema()
    yield


def test_purge_retention_dry_run(sqlite_store) -> None:
    store.start_run({"pipeline_id": "demo", "host_id": "linux-host"})
    result = store.purge_retention(30, dry_run=True)
    assert result["dry_run"] is True
    assert "runs" in result
    assert "triggers" in result


def test_purge_legacy_dry_run(sqlite_store) -> None:
    store.register_pipeline_catalog(
        {
            "pipeline_id": "health_probe",
            "host_id": "linux-host",
            "name": "probe",
            "nodes": [],
            "edges": [],
        }
    )
    store.start_run({"pipeline_id": "health_probe", "host_id": "linux-host"})
    result = store.purge_legacy_pipelines(dry_run=True)
    assert result["dry_run"] is True
    assert "health_probe" in result["pipelines"]


def test_excluded_does_not_include_regular_pipeline() -> None:
    assert "windows_pipeline" not in store.EXCLUDED_PIPELINE_IDS
