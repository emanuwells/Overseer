#!/usr/bin/env python3
"""Substitui linhas de cron D4MAIA por wrappers Overseer (com backup prévio)."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime


def read_crontab() -> list[str]:
    proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return proc.stdout.splitlines()


def write_crontab(lines: list[str]) -> None:
    payload = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-json", required=True)
    parser.add_argument("--backup-dir", default=str(pathlib.Path.home() / "backups"))
    args = parser.parse_args()

    catalog = json.loads(pathlib.Path(args.catalog_json).read_text(encoding="utf-8"))
    pipelines = catalog.get("pipelines") or []

    current = read_crontab()
    backup_dir = pathlib.Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_path = backup_dir / f"crontab-eferreira-{stamp}.bak"
    backup_path.write_text("\n".join(current) + ("\n" if current else ""), encoding="utf-8")

    out: list[str] = []
    replaced: set[str] = set()

    for line in current:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out.append(line)
            continue

        matched = False
        for item in pipelines:
            cron_match = str(item.get("cron_match") or "")
            if cron_match and cron_match in line and not line.strip().startswith("#"):
                schedule = str(item.get("schedule") or "").strip()
                run_sh = str(item.get("run_sh") or "")
                log = str(item.get("log") or "/dev/null")
                pid = str(item.get("id") or "")
                if not schedule or not run_sh:
                    continue
                new_line = (
                    f"{schedule} {run_sh} >> {log} 2>&1 "
                    f"# overseer:{pid}"
                )
                out.append(new_line)
                replaced.add(pid)
                matched = True
                break

        if not matched:
            out.append(line)

    write_crontab(out)
    print(f"Backup: {backup_path}")
    print(f"Substituídas {len(replaced)} linhas: {', '.join(sorted(replaced))}")
    missing = {str(p.get("id")) for p in pipelines} - replaced
    if missing:
        print(f"AVISO: não encontradas no crontab: {', '.join(sorted(missing))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
