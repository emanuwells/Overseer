from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import insert, select

from overseer_core import store
from scripts.maintenance.reclassify_traffic_flow_partial_runs import (
    reclassify_partial_runs,
    restore_backup,
)


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None
    store.init_schema()
    yield store.get_engine()
    store._engine = None


def _seed_run(
    engine,
    *,
    run_id: str,
    started_at: datetime,
    nascente_ok: bool,
    poente_ok: bool,
    status: str = "failed",
) -> None:
    now = datetime(2026, 8, 31, 9, 0, 0)
    with engine.begin() as connection:
        connection.execute(
            insert(store.runs_table).values(
                run_id=run_id,
                pipeline_id="traffic_flow",
                host_id="BAZE2",
                pipeline_name="Traffic Flow",
                status=status,
                trigger_type="cron",
                started_at=started_at,
                ended_at=started_at,
                exit_code=1,
                error_message="original",
                created_at=now,
                updated_at=now,
            )
        )
        connection.execute(
            insert(store.modules_table).values(
                run_id=run_id,
                pipeline_id="traffic_flow",
                host_id="BAZE2",
                module_id="traffic_flow",
                status=status,
                created_at=now,
            )
        )
        message = (
            f"- Maia Nascente: ok={nascente_ok} inseridos={1 if nascente_ok else 0}\n"
            f"- Maia Poente: ok={poente_ok} inseridos={1 if poente_ok else 0}"
        )
        connection.execute(
            insert(store.logs_table).values(
                run_id=run_id,
                pipeline_id="traffic_flow",
                host_id="BAZE2",
                module_id="traffic_flow",
                level="info",
                message=message,
                created_at=now,
            )
        )


def test_reclassifies_only_evidenced_partial_runs(sqlite_store, tmp_path: Path) -> None:
    _seed_run(
        sqlite_store,
        run_id="partial",
        started_at=datetime(2026, 8, 25, 4, 15, 3),
        nascente_ok=False,
        poente_ok=True,
    )
    _seed_run(
        sqlite_store,
        run_id="true-failure",
        started_at=datetime(2026, 8, 25, 10, 0, 3),
        nascente_ok=False,
        poente_ok=False,
    )
    _seed_run(
        sqlite_store,
        run_id="before-cutoff",
        started_at=datetime(2026, 8, 25, 4, 0, 3),
        nascente_ok=False,
        poente_ok=True,
    )

    dry_run = reclassify_partial_runs(sqlite_store)
    assert dry_run["candidates"] == 1
    assert dry_run["updated_runs"] == 0

    applied = reclassify_partial_runs(sqlite_store, apply=True, backup_dir=tmp_path)
    assert applied["updated_runs"] == 1
    assert applied["updated_modules"] == 1
    backup = Path(applied["backup"])
    assert backup.is_file()

    with sqlite_store.connect() as connection:
        rows = {
            row.run_id: row
            for row in connection.execute(
                select(
                    store.runs_table.c.run_id,
                    store.runs_table.c.status,
                    store.runs_table.c.exit_code,
                    store.runs_table.c.error_message,
                )
            )
        }
    assert rows["partial"].status == "warning"
    assert rows["partial"].exit_code == 1
    assert rows["partial"].error_message == "original"
    assert rows["true-failure"].status == "failed"
    assert rows["before-cutoff"].status == "failed"
    assert reclassify_partial_runs(sqlite_store, apply=True, backup_dir=tmp_path)["candidates"] == 0

    restored = restore_backup(sqlite_store, backup)
    assert restored == {"mode": "restore", "restored_runs": 1, "restored_modules": 1}
    assert restore_backup(sqlite_store, backup) == {
        "mode": "restore",
        "restored_runs": 0,
        "restored_modules": 0,
    }
