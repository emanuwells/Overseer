from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, insert, select

from overseer_core import store
from scripts.maintenance.purge_retention_telemetry import (
    purge_retention_with_backup,
    restore_backup,
)


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{tmp_path / 'retention.db'}")
    store._engine = None  # noqa: SLF001
    store.init_schema()
    yield store.get_engine(), tmp_path
    store._engine = None  # noqa: SLF001


def test_retention_apply_and_restore_are_idempotent(sqlite_store) -> None:
    engine, tmp_path = sqlite_store
    now = datetime(2026, 8, 31, 12, 0, 0)
    old = now - timedelta(days=31)
    fresh = now - timedelta(days=1)
    with engine.begin() as connection:
        for run_id, started in (("old", old), ("fresh", fresh)):
            connection.execute(
                insert(store.runs_table).values(
                    run_id=run_id,
                    pipeline_id="demo",
                    host_id="HOST",
                    status="ok",
                    trigger_type="cron",
                    started_at=started,
                    ended_at=started + timedelta(seconds=1),
                    created_at=started,
                    updated_at=started,
                )
            )
            connection.execute(
                insert(store.modules_table).values(
                    run_id=run_id,
                    pipeline_id="demo",
                    host_id="HOST",
                    module_id="run",
                    status="ok",
                    created_at=started,
                )
            )
            connection.execute(
                insert(store.logs_table).values(
                    run_id=run_id,
                    pipeline_id="demo",
                    host_id="HOST",
                    level="info",
                    event_type="log",
                    message=run_id,
                    created_at=started,
                )
            )

    dry = purge_retention_with_backup(engine, now=now)
    assert dry["counts"]["runs"] == 1
    applied = purge_retention_with_backup(
        engine, apply=True, backup_dir=tmp_path / "backups", now=now
    )
    assert applied["counts"] == {
        "runs": 1,
        "modules": 1,
        "logs": 1,
        "triggers": 0,
        "heartbeats": 0,
    }
    assert Path(applied["backup"]).is_file()
    assert purge_retention_with_backup(engine, now=now)["counts"]["runs"] == 0

    restored = restore_backup(engine, Path(applied["backup"]))
    assert restored["restored"]["runs"] == 1
    assert restore_backup(engine, Path(applied["backup"]))["restored"]["runs"] == 0
    with engine.connect() as connection:
        assert connection.execute(select(func.count()).select_from(store.runs_table)).scalar_one() == 2
        assert connection.execute(select(func.count()).select_from(store.modules_table)).scalar_one() == 2
        assert connection.execute(select(func.count()).select_from(store.logs_table)).scalar_one() == 2
