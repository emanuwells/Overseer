#!/usr/bin/env python3
"""Remove Cursor co-author trailers from commit messages (stdin -> stdout)."""

from __future__ import annotations

import sys

MARKERS = (
    "Co-authored-by: Cursor <cursoragent@cursor.com>",
    "Co-authored-by: Cursor <cursoragent@cursor.com>\r",
)


def main() -> int:
    lines = sys.stdin.read().splitlines()
    cleaned = [
        line
        for line in lines
        if not line.strip().startswith("Co-authored-by: Cursor <cursoragent@cursor.com>")
    ]
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    sys.stdout.write("\n".join(cleaned))
    if cleaned:
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
