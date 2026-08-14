#!/usr/bin/env python3
"""Atualiza linhas de cron para wrappers Overseer, com backup prévio."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime

LEGACY_OVERSEER_MARKERS: dict[str, str] = {}


def _pipeline_by_id(pipelines: list[dict], pipeline_id: str) -> dict | None:
    for item in pipelines:
        if str(item.get("id") or "") == pipeline_id:
            return item
    return None


def _schedule_generates_cron(schedule: str) -> bool:
    normalized = str(schedule or "").strip().lower()
    return bool(normalized) and normalized not in {"manual", "paused"}


def _overseer_cron_line(item: dict) -> str | None:
    schedule = str(item.get("schedule") or "").strip()
    run_sh = str(item.get("run_sh") or "")
    log = str(item.get("log") or "/dev/null")
    pid = str(item.get("id") or "")
    if not _schedule_generates_cron(schedule) or not run_sh or not pid:
        return None
    return f"{schedule} {run_sh} >> {log} 2>&1 # overseer:{pid}"


def _overseer_marker(line: str) -> str | None:
    if "# overseer:" not in line:
        return None
    return line.split("# overseer:", 1)[-1].strip()


def read_crontab() -> list[str]:
    proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return proc.stdout.splitlines()


def write_crontab(lines: list[str]) -> None:
    payload = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)


def dedupe_active_overseer_lines(lines: list[str]) -> list[str]:
    seen_markers: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "# overseer:" not in line:
            out.append(line)
            continue
        marker = line.split("# overseer:", 1)[-1].strip()
        if marker in seen_markers:
            continue
        seen_markers.add(marker)
        out.append(line)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-json", required=True)
    parser.add_argument("--backup-dir", default=str(pathlib.Path.home() / "backups"))
    parser.add_argument("--legacy-map-json", default="", help="JSON opcional com mapeamento ID antigo -> novo.")
    args = parser.parse_args()

    legacy_markers = LEGACY_OVERSEER_MARKERS
    if args.legacy_map_json:
        legacy_markers = json.loads(pathlib.Path(args.legacy_map_json).read_text(encoding="utf-8"))

    catalog = json.loads(pathlib.Path(args.catalog_json).read_text(encoding="utf-8"))
    pipelines = catalog.get("pipelines") or []

    current = read_crontab()
    backup_dir = pathlib.Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_path = backup_dir / f"crontab-overseer-{stamp}.bak"
    backup_path.write_text("\n".join(current) + ("\n" if current else ""), encoding="utf-8")

    out: list[str] = []
    replaced: set[str] = set()

    for line in current:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out.append(line)
            continue

        if "# overseer:" in line:
            legacy_migrated = False
            for legacy_id, new_id in legacy_markers.items():
                if f"# overseer:{legacy_id}" not in line:
                    continue
                out.append(f"# legacy: {line}")
                new_item = _pipeline_by_id(pipelines, new_id)
                if new_item and new_id not in replaced:
                    new_line = _overseer_cron_line(new_item)
                    if new_line:
                        out.append(new_line)
                        replaced.add(new_id)
                legacy_migrated = True
                break
            if legacy_migrated:
                continue

            marker = _overseer_marker(line)
            item = _pipeline_by_id(pipelines, marker) if marker else None
            if marker and item is None:
                if not stripped.startswith("#"):
                    out.append(f"# removed: {line}")
                else:
                    out.append(line)
                continue
            if item and not _overseer_cron_line(item):
                if not stripped.startswith("#"):
                    out.append(f"# paused: {line}")
                else:
                    out.append(line)
                if marker:
                    replaced.add(marker)
                continue

            # item existe e tem uma linha de cron válida: refresca sempre a partir
            # do catálogo (run_sh pode ter mudado, ex. runners_root movido) em vez
            # de preservar a linha antiga tal e qual.
            out.append(_overseer_cron_line(item) or line)
            for item in pipelines:
                pid = str(item.get("id") or "")
                if pid and f"# overseer:{pid}" in line:
                    replaced.add(pid)
            continue

        matched = False
        for item in pipelines:
            cron_match = str(item.get("cron_match") or "")
            if cron_match and cron_match in line and not line.strip().startswith("#"):
                new_line = _overseer_cron_line(item)
                pid = str(item.get("id") or "")
                if not pid:
                    continue
                if new_line:
                    out.append(f"# legacy: {line}")
                    out.append(new_line)
                else:
                    out.append(f"# paused: {line}")
                replaced.add(pid)
                matched = True
                break

        if not matched:
            out.append(line)

    missing = {str(p.get("id")) for p in pipelines} - replaced
    appended: set[str] = set()
    for item in pipelines:
        pid = str(item.get("id") or "")
        if not pid or pid not in missing:
            continue
        new_line = _overseer_cron_line(item)
        if not new_line:
            continue
        out.append(new_line)
        appended.add(pid)

    out = dedupe_active_overseer_lines(out)
    write_crontab(out)
    print(f"Backup: {backup_path}")
    print(f"Substituídas {len(replaced)} linhas: {', '.join(sorted(replaced))}")
    if appended:
        print(f"Adicionadas {len(appended)} linhas: {', '.join(sorted(appended))}")
    still_missing = missing - appended
    if still_missing:
        print(f"AVISO: não encontradas no crontab: {', '.join(sorted(still_missing))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
