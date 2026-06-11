#!/usr/bin/env python3
"""Backfill sequential run_local_id values (1..N) on overseer_runs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from overseer_core.store import backfill_run_local_ids, count_runs, init_schema  # noqa: E402


def main() -> int:
    init_schema()
    updated = backfill_run_local_ids()
    print(f"run_local_id backfill complete: {updated} row(s) updated; total runs={count_runs()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
