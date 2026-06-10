#!/usr/bin/env python3
"""Remove runs and related telemetry for a pipeline from the Overseer schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from overseer_core import store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge Overseer data for one pipeline_id.")
    parser.add_argument("pipeline_id", help="Logical pipeline id (e.g. p_monitor_recent)")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without deleting")
    parser.add_argument("--keep-pipeline", action="store_true", help="Do not deactivate catalog row")
    args = parser.parse_args()

    store.init_schema()
    result = store.purge_pipeline_data(
        args.pipeline_id,
        deactivate=not args.keep_pipeline,
        dry_run=args.dry_run,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
