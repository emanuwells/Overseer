#!/usr/bin/env python3
"""Split legacy ``pipeline_id__HOST`` rows into logical pipeline_id + host_id."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlalchemy import delete, select, update

from overseer_core import store

def _rewrite_pipeline(conn, old_id: str, new_id: str, host_id: str) -> None:
    existing = conn.execute(
        select(store.pipelines_table.c.pipeline_id).where(
            (store.pipelines_table.c.pipeline_id == new_id)
            & (store.pipelines_table.c.host_id == host_id)
        )
    ).first()
    if existing and old_id != new_id:
        conn.execute(delete(store.pipelines_table).where(store.pipelines_table.c.pipeline_id == old_id))
        return
    conn.execute(
        update(store.pipelines_table)
        .where(store.pipelines_table.c.pipeline_id == old_id)
        .values(pipeline_id=new_id, host_id=host_id)
    )


def _rewrite_child_tables(conn, old_id: str, new_id: str, host_id: str) -> None:
    for table in (
        store.runs_table,
        store.modules_table,
        store.logs_table,
        store.heartbeats_table,
        store.triggers_table,
    ):
        conn.execute(
            update(table)
            .where(table.c.pipeline_id == old_id)
            .values(pipeline_id=new_id, host_id=host_id)
        )


def migrate(*, default_host: str = "", dry_run: bool = False) -> int:
    store.init_schema()
    engine = store.get_engine()
    changes: list[tuple[str, str, str]] = []

    with engine.connect() as conn:
        rows = conn.execute(select(store.pipelines_table)).mappings().all()
        for row in rows:
            pid = str(row["pipeline_id"])
            current_host = str(row.get("host_id") or "")
            logical, legacy_host = store.split_legacy_pipeline_id(pid)
            if legacy_host:
                changes.append((pid, logical, legacy_host))
            elif not current_host and default_host:
                changes.append((pid, pid, default_host))

    if dry_run:
        for old_id, new_id, host_id in changes:
            print(f"would migrate pipeline {old_id!r} -> pipeline_id={new_id!r} host_id={host_id!r}")
        print(f"total: {len(changes)} pipeline deployment(s)")
        return 0

    with engine.begin() as conn:
        for old_id, new_id, host_id in changes:
            if old_id == new_id:
                conn.execute(
                    update(store.pipelines_table)
                    .where(store.pipelines_table.c.pipeline_id == new_id)
                    .values(host_id=host_id)
                )
                _rewrite_child_tables(conn, old_id, new_id, host_id)
            else:
                _rewrite_pipeline(conn, old_id, new_id, host_id)
                _rewrite_child_tables(conn, old_id, new_id, host_id)

    print(f"Migrados {len(changes)} deployment(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrar sufixo pipeline__host para host_id.")
    parser.add_argument("--default-host", default="", help="host_id opcional para pipelines sem sufixo.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return migrate(default_host=args.default_host, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
