#!/usr/bin/env python3
"""Apply Overseer telemetry retention (default 30 days)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from overseer_core import store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge Overseer telemetry older than N days.")
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("OVERSEER_RETENTION_DAYS", "30")),
        help="Retention window in days (default: OVERSEER_RETENTION_DAYS or 30)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report counts without deleting")
    parser.add_argument("--apply", action="store_true", help="Execute purge (default is dry-run)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass auto-retention throttle and update last-purge marker",
    )
    args = parser.parse_args()

    store.init_schema()
    if args.apply:
        result = store.auto_purge_retention_if_due(force=True) if args.force else store.purge_retention(args.days, dry_run=False)
    else:
        result = store.purge_retention(args.days, dry_run=True)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
