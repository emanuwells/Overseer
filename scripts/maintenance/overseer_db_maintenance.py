#!/usr/bin/env python3
"""Maintenance utilities for Overseer telemetry data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from overseer_core.store import get_engine, purge_stuck_running_runs, running_run_max_age_hours  # noqa: E402


def _reconcile_cpu_metrics(*, apply: bool) -> None:
    engine = get_engine()
    try:
        with engine.begin() as conn:
            cpu_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM overseer_runs
                    WHERE CAST(JSON_UNQUOTE(JSON_EXTRACT(metadata_json, '$.usage_cpu')) AS DECIMAL(10,2)) > 100
                       OR CAST(JSON_UNQUOTE(JSON_EXTRACT(metadata_json, '$.cpu')) AS DECIMAL(10,2)) > 100
                    """
                )
            ).scalar_one()
            print(f"astronomical_cpu={cpu_count}")
            if apply and cpu_count:
                updated_cpu = conn.execute(
                    text(
                        """
                        UPDATE overseer_runs
                        SET metadata_json = JSON_SET(metadata_json, '$.usage_cpu', NULL, '$.cpu', NULL)
                        WHERE CAST(JSON_UNQUOTE(JSON_EXTRACT(metadata_json, '$.usage_cpu')) AS DECIMAL(10,2)) > 100
                           OR CAST(JSON_UNQUOTE(JSON_EXTRACT(metadata_json, '$.cpu')) AS DECIMAL(10,2)) > 100
                        """
                    )
                ).rowcount
                print(f"updated_cpu={updated_cpu}")
    except Exception as exc:
        print(f"astronomical_cpu=skipped ({exc.__class__.__name__})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Overseer DB maintenance tasks.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    parser.add_argument(
        "--running-max-age-hours",
        type=float,
        default=running_run_max_age_hours(),
        help="Delete running runs older than this many hours.",
    )
    parser.add_argument(
        "--pipeline-id",
        default=None,
        help="Restrict stuck running purge to one logical pipeline id.",
    )
    parser.add_argument("--skip-cpu", action="store_true", help="Skip MariaDB JSON CPU cleanup.")
    args = parser.parse_args()

    if not args.skip_cpu:
        _reconcile_cpu_metrics(apply=args.apply)

    stale = purge_stuck_running_runs(
        max_age_hours=args.running_max_age_hours,
        pipeline_id=args.pipeline_id,
        dry_run=not args.apply,
    )
    print(
        "stuck_running="
        f"{stale['runs']} modules={stale['modules']} logs={stale['logs']} "
        f"max_age_hours={stale['max_age_hours']} "
        f"pipeline_id={args.pipeline_id or '*'} dry_run={stale['dry_run']}"
    )


if __name__ == "__main__":
    main()
