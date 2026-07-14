from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, inspect, text

from overseer_core import store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "overseer.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path.as_posix()}")
    store._engine = None  # noqa: SLF001
    store.init_schema()
    yield
    store._engine = None  # noqa: SLF001


def test_drop_legacy_tables_dry_run_and_apply(sqlite_store) -> None:
    legacy = Table(
        "pipeline_runs",
        MetaData(),
        Column("id", Integer, primary_key=True),
    )
    legacy.create(store.get_engine())
    with store.get_engine().begin() as conn:
        conn.execute(text("INSERT INTO pipeline_runs (id) VALUES (1)"))

    dry = store.drop_legacy_tables(dry_run=True)
    assert "pipeline_runs" in dry["would_drop"]
    assert dry["row_counts"]["pipeline_runs"] == 1

    applied = store.drop_legacy_tables(dry_run=False)
    assert "pipeline_runs" in applied["dropped"]
    assert "pipeline_runs" not in inspect(store.get_engine()).get_table_names()


def test_governance_tables_not_in_drop_list() -> None:
    assert "overseer_identity_mappings" in store.GOVERNANCE_TABLES
    assert "overseer_identity_mappings" not in store.LEGACY_DROP_TABLES
