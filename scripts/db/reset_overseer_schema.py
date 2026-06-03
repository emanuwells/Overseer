from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pm_runtime.db import get_engine
from src.pm_runtime.settings import settings

KEEP_TABLES = {
    "pipeline_runs",
    "pipeline_module_events",
    "orchestrator_runs_local",
    "orchestrator_triggers_local",
    "orchestrator_steps_local",
    "orchestrator_events_local",
    "overseer_runners",
    "pipeline_script_logs",
    "logs_archive",
    "pipeline_catalog",
    "overseer_pipeline_permissions",
    "overseer_identity_mappings",
    "overseer_permission_requests",
    "overseer_identity_mapping_requests",
}

DROP_CANDIDATES = {
    "logs",  # legacy when RUNS_TABLE=pipeline_runs
    "pipeline_script_logs_backup",
}

TRUNCATE_TABLES = [
    "pipeline_module_events",
    "orchestrator_events_local",
    "orchestrator_steps_local",
    "orchestrator_triggers_local",
    "orchestrator_runs_local",
    "overseer_runners",
    "pipeline_script_logs",
]


def list_tables(engine) -> list[str]:
    sql = text(
        """
        SELECT TABLE_NAME AS name
          FROM information_schema.TABLES
         WHERE TABLE_SCHEMA = DATABASE()
         ORDER BY TABLE_NAME
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [str(r["name"]) for r in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit/reset Overseer schema")
    parser.add_argument("--confirm", action="store_true", help="Execute TRUNCATE on operational tables")
    parser.add_argument("--drop-orphans", action="store_true", help="DROP legacy/orphan tables")
    parser.add_argument("--audit-only", action="store_true", help="Only print table audit")
    args = parser.parse_args()

    runs_table = settings.runs_table.strip()
    keep = set(KEEP_TABLES)
    keep.add(runs_table)

    engine = get_engine()
    existing = list_tables(engine)

    print(f"RUNS_TABLE={runs_table}")
    print(f"Tables in schema ({len(existing)}):")
    for name in existing:
        tag = "keep" if name in keep else ("drop?" if name in DROP_CANDIDATES else "orphan?")
        print(f"  - {name} [{tag}]")

    orphans = [t for t in existing if t not in keep]
    if orphans:
        print(f"\nTables not in keep list ({len(orphans)}): {', '.join(orphans)}")

    if args.audit_only:
        return 0

    if not args.confirm:
        print("\nDry-run: pass --confirm to TRUNCATE operational tables.")
        if args.drop_orphans:
            print("Pass --drop-orphans with --confirm to drop legacy tables.")
        return 0

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        if args.drop_orphans:
            for table in sorted(set(orphans) & DROP_CANDIDATES):
                print(f"Dropping {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))

        if runs_table in existing:
            print(f"Truncating {runs_table}...")
            conn.execute(text(f"TRUNCATE TABLE `{runs_table}`"))

        for table in TRUNCATE_TABLES:
            if table in existing:
                print(f"Truncating {table}...")
                conn.execute(text(f"TRUNCATE TABLE `{table}`"))

        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print("Reset complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
