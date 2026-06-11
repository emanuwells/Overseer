#!/usr/bin/env python3
"""One-off maintenance: nullify astronomical CPU and reconcile stale running runs."""

from __future__ import annotations

from sqlalchemy import text

from overseer_core.store import get_engine


def main() -> None:
    engine = get_engine()
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
        stale_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM overseer_runs
                WHERE LOWER(status) = 'running'
                  AND started_at < (UTC_TIMESTAMP() - INTERVAL 6 HOUR)
                """
            )
        ).scalar_one()
        print(f"astronomical_cpu={cpu_count}")
        print(f"stale_running={stale_count}")

        if cpu_count:
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

        if stale_count:
            updated_stale = conn.execute(
                text(
                    """
                    UPDATE overseer_runs
                    SET status = 'failed',
                        ended_at = COALESCE(ended_at, UTC_TIMESTAMP()),
                        error_message = COALESCE(NULLIF(error_message, ''), 'stale running (reconciled)')
                    WHERE LOWER(status) = 'running'
                      AND started_at < (UTC_TIMESTAMP() - INTERVAL 6 HOUR)
                    """
                )
            ).rowcount
            print(f"updated_stale={updated_stale}")


if __name__ == "__main__":
    main()
