#!/usr/bin/env python3
"""Scan git history for non-placeholder Slack webhook URLs (no secret output)."""

from __future__ import annotations

import re
import subprocess
import sys

PLACEHOLDER = re.compile(
    r"hooks\.slack\.com/services/(?:XXX/YYY/ZZZ|test\b|[A-Za-z0-9_-]{1,8})\b"
)
WEBHOOK = re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+")


def main() -> int:
    out = subprocess.check_output(["git", "log", "--all", "-p", "--no-color"], text=True, errors="replace")
    hits: list[tuple[str, str]] = []
    commit = ""
    for line in out.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1]
        if line.startswith("+") and "hooks.slack.com" in line:
            for match in WEBHOOK.findall(line):
                if not PLACEHOLDER.search(match) and len(match) > 45:
                    hits.append((commit[:12], match[:50] + "..."))
    if not hits:
        print("no_suspect_webhooks_in_history")
        return 0
    print(f"suspect_hits={len(hits)}")
    for commit_id, preview in hits[:20]:
        print(f"{commit_id} {preview}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
