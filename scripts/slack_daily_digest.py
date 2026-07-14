#!/usr/bin/env python3
"""Envia o digest diário Overseer para Slack (manual ou cron no container)."""

from __future__ import annotations

import argparse
import sys

from overseer_core.slack_digest import build_digest_text, send_daily_digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Overseer Slack daily digest")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar mensagem sem enviar")
    args = parser.parse_args()

    if args.dry_run:
        print(build_digest_text())
        return 0

    ok = send_daily_digest()
    if ok:
        print("Digest Slack enviado.")
        return 0
    print("Digest não enviado (webhook ausente ou digest desactivado).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
