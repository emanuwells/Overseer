#!/usr/bin/env python3
"""Rewrite git history to remove Cursor co-author trailers."""

from __future__ import annotations

import sys

from git_filter_repo import FilteringOptions, RepoFilter


def message_callback(message: bytes, *_args) -> bytes:
    cleaned = message.replace(b"Co-authored-by: Cursor <cursoragent@cursor.com>", b"")
    cleaned = cleaned.replace(b"\r\n", b"\n")
    while b"\n\n\n" in cleaned:
        cleaned = cleaned.replace(b"\n\n\n", b"\n\n")
    return cleaned.rstrip() + b"\n"


def main() -> int:
    args = FilteringOptions.parse_args(["--force"])
    RepoFilter(args, message_callback=message_callback).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
