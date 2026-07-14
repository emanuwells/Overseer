#!/usr/bin/env python3
"""Drop legacy Overseer schema tables (pre-overseer_* telemetry and orchestrator local)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from overseer_core import store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Drop legacy tables from the Overseer database schema.")
    parser.add_argument("--dry-run", action="store_true", help="Report tables and row counts without dropping")
    parser.add_argument("--apply", action="store_true", help="Execute DROP TABLE (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply
    store.init_schema()
    result = store.drop_legacy_tables(dry_run=dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
