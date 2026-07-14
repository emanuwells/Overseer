#!/usr/bin/env python3
"""Read-only audit of Overseer DB tables and telemetry volume."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlalchemy import inspect, text  # noqa: E402

from overseer_core import store  # noqa: E402

EXPECTED = {
    "overseer_pipelines",
    "overseer_pipeline_nodes",
    "overseer_pipeline_edges",
    "overseer_runs",
    "overseer_modules",
    "overseer_logs",
    "overseer_heartbeats",
    "overseer_triggers",
}


def main() -> int:
    store.init_schema()
    engine = store.get_engine()
    tables = set(inspect(engine).get_table_names())
    extra = sorted(tables - EXPECTED)
    missing = sorted(EXPECTED - tables)

    print("=== SCHEMA ===")
    print(f"tables={len(tables)} extra={extra or 'none'} missing={missing or 'none'}")

    status = store.database_status()
    print("=== COUNTS ===")
    for key, value in sorted((status.get("tables") or {}).items()):
        print(f"{key}={value}")

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT status, COUNT(*) AS c FROM overseer_runs GROUP BY status ORDER BY c DESC")
        ).all()
        print("=== RUNS BY STATUS ===")
        for status_name, count in rows:
            print(f"{status_name}={count}")

        rows = conn.execute(
            text(
                """
                SELECT pipeline_id, host_id, COUNT(*) AS c
                FROM overseer_runs
                GROUP BY pipeline_id, host_id
                ORDER BY c DESC
                LIMIT 15
                """
            )
        ).all()
        print("=== TOP DEPLOYMENTS (runs) ===")
        for pipeline_id, host_id, count in rows:
            host = host_id or "-"
            print(f"{pipeline_id}@{host}={count}")

        orphan = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM overseer_runs r
                LEFT JOIN overseer_pipelines p
                  ON r.pipeline_id = p.pipeline_id
                 AND COALESCE(r.host_id, '') = COALESCE(p.host_id, '')
                WHERE p.pipeline_id IS NULL
                """
            )
        ).scalar_one()
        print(f"runs_without_catalog={orphan}")

        stuck = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM overseer_runs
                WHERE LOWER(status) IN ('running', 'queued')
                  AND started_at < DATE_SUB(NOW(), INTERVAL 6 HOUR)
                """
            )
        ).scalar_one()
        print(f"stuck_running_6h={stuck}")

        row = conn.execute(
            text("SELECT MIN(started_at), MAX(started_at), COUNT(*) FROM overseer_runs")
        ).one()
        print(f"runs_range={row[0]} -> {row[1]} total={row[2]}")

        suspect = conn.execute(
            text(
                """
                SELECT pipeline_id, COUNT(*) AS c FROM overseer_runs
                WHERE pipeline_id LIKE '%test%'
                   OR pipeline_id LIKE '%demo%'
                   OR pipeline_id IN ('health_probe', 'p_monitor_recent')
                GROUP BY pipeline_id ORDER BY c DESC
                """
            )
        ).all()
        print("=== SUSPECT PIPELINES ===")
        if suspect:
            for pipeline_id, count in suspect:
                print(f"{pipeline_id}={count}")
        else:
            print("none")

    dry = store.purge_retention(30, dry_run=True)
    print("=== RETENTION DRY-RUN (30d) ===")
    for key in ("runs", "modules", "logs", "triggers", "heartbeats"):
        print(f"{key}={dry.get(key)}")

    legacy = store.purge_legacy_pipelines(dry_run=True)
    legacy_runs = sum(
        int(item.get("runs", 0) or 0) for item in (legacy.get("pipelines") or {}).values()
    )
    print(f"legacy_pipeline_runs_dry={legacy_runs}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
