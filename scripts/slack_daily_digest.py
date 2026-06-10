#!/usr/bin/env python3
"""Envia o digest diário Overseer para Slack (manual ou cron no container)."""

from __future__ import annotations

import sys

from overseer_core.slack_digest import send_daily_digest


def main() -> int:
    ok = send_daily_digest()
    if ok:
        print("Digest Slack enviado.")
        return 0
    print("Digest não enviado (webhook ausente ou digest desactivado).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
