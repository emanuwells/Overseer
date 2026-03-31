"""One-time cleanup: find and expire stale 'running' rows in both tables."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.pm_runtime.db import get_engine

engine = get_engine()

with engine.connect() as conn:
    # ---- Report stale runs ----
    print("=== pipeline_runs WHERE status='running' ===")
    rows1 = conn.execute(
        text("SELECT id, pipelineId, scriptName, status, startDate, endDate FROM pipeline_runs WHERE LOWER(status)='running'")
    ).fetchall()
    for r in rows1:
        print(dict(r._mapping))
    print(f"  → {len(rows1)} row(s)\n")

    print("=== orchestrator_runs_local WHERE status='running' ===")
    rows2 = conn.execute(
        text("SELECT run_local_id, pipeline_id, status, created_at FROM orchestrator_runs_local WHERE LOWER(status)='running'")
    ).fetchall()
    for r in rows2:
        print(dict(r._mapping))
    print(f"  → {len(rows2)} row(s)\n")

    if not rows1 and not rows2:
        print("Nothing to fix — no stale running runs.")
        sys.exit(0)

    # ---- Fix them ----
    print("Fixing stale runs ...")

    r1 = conn.execute(text(
        """UPDATE pipeline_runs
              SET status = 'Failed',
                  endDate = NOW(),
                  errorMessage = CONCAT(COALESCE(errorMessage,''), '[auto-expired] stale running run cleaned up')
            WHERE LOWER(status)='running'"""
    ))
    print(f"  pipeline_runs updated: {r1.rowcount}")

    r2 = conn.execute(text(
        """UPDATE orchestrator_runs_local
              SET status = 'failed',
                  ended_at = UTC_TIMESTAMP(),
                  error_message = CONCAT(COALESCE(error_message,''), '[auto-expired] stuck running >60 min')
            WHERE LOWER(status)='running'"""
    ))
    print(f"  orchestrator_runs_local updated: {r2.rowcount}")

    conn.commit()
    print("Done.")
