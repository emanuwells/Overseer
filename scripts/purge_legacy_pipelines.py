#!/usr/bin/env python3
"""Purge known legacy pipelines from the Overseer schema."""

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
    parser = argparse.ArgumentParser(description="Purge legacy Overseer pipeline data.")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without deleting")
    parser.add_argument("--apply", action="store_true", help="Execute purge (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply
    store.init_schema()
    result = store.purge_legacy_pipelines(dry_run=dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
