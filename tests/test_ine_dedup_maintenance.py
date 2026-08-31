from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, insert, select

from overseer_core import store
from scripts.maintenance.deduplicate_ine_runs import deduplicate_ine_runs, restore_backup


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{tmp_path / 'dedup.db'}")
    store._engine = None  # noqa: SLF001
    store.init_schema()
    yield store.get_engine(), tmp_path
    store._engine = None  # noqa: SLF001


def test_ine_duplicate_is_consolidated_and_restorable(sqlite_store) -> None:
    engine, tmp_path = sqlite_store
    started = datetime(2026, 8, 31, 3, 0, 0)
    with engine.begin() as connection:
        connection.execute(
            insert(store.runs_table).values(
                run_id="wrapper",
                pipeline_id="ine_pipeline",
                host_id="BAZE2",
                status="ok",
                trigger_type="cron",
                started_at=started,
                ended_at=started + timedelta(minutes=10),
                exit_code=0,
                metadata_json=store.json_dump({"runner": "manifest"}),
                created_at=started,
                updated_at=started,
            )
        )
        connection.execute(
            insert(store.runs_table).values(
                run_id="internal",
                pipeline_id="ine_pipeline",
                host_id="BAZE2",
                status="warning",
                trigger_type="pipeline",
                started_at=started + timedelta(seconds=2),
                ended_at=started + timedelta(minutes=11),
                metadata_json=store.json_dump({"detail": True}),
                created_at=started,
                updated_at=started,
            )
        )
        for run_id, module_id in (("wrapper", "run"), ("internal", "ine_series")):
            connection.execute(
                insert(store.modules_table).values(
                    run_id=run_id,
                    pipeline_id="ine_pipeline",
                    host_id="BAZE2",
                    module_id=module_id,
                    status="ok",
                    created_at=started,
                )
            )
            connection.execute(
                insert(store.logs_table).values(
                    run_id=run_id,
                    pipeline_id="ine_pipeline",
                    host_id="BAZE2",
                    level="info",
                    event_type="log",
                    message=module_id,
                    created_at=started,
                )
            )

    assert deduplicate_ine_runs(engine)["pairs"] == 1
    applied = deduplicate_ine_runs(engine, apply=True, backup_dir=tmp_path / "backups")
    assert applied["pairs"] == 1
    assert deduplicate_ine_runs(engine)["pairs"] == 0
    with engine.connect() as connection:
        run = connection.execute(
            select(store.runs_table).where(store.runs_table.c.run_id == "wrapper")
        ).mappings().one()
        assert run["status"] == "warning"
        assert connection.execute(select(func.count()).select_from(store.runs_table)).scalar_one() == 1
        assert connection.execute(select(func.count()).select_from(store.modules_table)).scalar_one() == 2
        assert set(
            connection.execute(select(store.modules_table.c.run_id)).scalars()
        ) == {"wrapper"}

    restored = restore_backup(engine, Path(applied["backup"]))
    assert restored["restored_pairs"] == 1
    assert restore_backup(engine, Path(applied["backup"]))["restored_pairs"] == 0
    with engine.connect() as connection:
        assert connection.execute(select(func.count()).select_from(store.runs_table)).scalar_one() == 2
        owners = dict(
            connection.execute(
                select(store.modules_table.c.module_id, store.modules_table.c.run_id)
            ).all()
        )
        assert owners == {"run": "wrapper", "ine_series": "internal"}
