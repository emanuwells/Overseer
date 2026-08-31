#!/usr/bin/env python3
"""Purga telemetria expirada com backup e restauro transacionais."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Connection, Engine

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from overseer_core.store import (  # noqa: E402
    get_engine,
    heartbeats_table,
    logs_table,
    modules_table,
    runs_table,
    triggers_table,
    utcnow,
)

BACKUP_FORMAT = "overseer-retention-telemetry-v1"
DEFAULT_BACKUP_DIR = Path("/home/eferreira/Dev/backups/overseer/retention")
TABLES = {
    "runs": runs_table,
    "modules": modules_table,
    "logs": logs_table,
    "triggers": triggers_table,
    "heartbeats": heartbeats_table,
}


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return value


def _serialized(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: _json_value(value) for key, value in row.items()} for row in rows]


def _write_backup(backup_dir: Path, cutoff: datetime, data: dict[str, list[dict[str, Any]]]) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_dir / f"retention_{stamp}.json"
    payload = {
        "format": BACKUP_FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cutoff": _json_value(cutoff),
        "tables": {name: _serialized(rows) for name, rows in data.items()},
    }
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=backup_dir, prefix=".retention_", suffix=".tmp", delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    temporary.replace(destination)
    return destination


def _collect(connection: Connection, cutoff: datetime, *, lock: bool) -> dict[str, list[dict[str, Any]]]:
    run_statement = select(runs_table).where(runs_table.c.started_at < cutoff)
    if lock:
        run_statement = run_statement.with_for_update()
    runs = [dict(row) for row in connection.execute(run_statement).mappings()]
    run_ids = [str(row["run_id"]) for row in runs]
    modules = (
        [dict(row) for row in connection.execute(select(modules_table).where(modules_table.c.run_id.in_(run_ids))).mappings()]
        if run_ids
        else []
    )
    logs = (
        [dict(row) for row in connection.execute(select(logs_table).where(logs_table.c.run_id.in_(run_ids))).mappings()]
        if run_ids
        else []
    )
    triggers = [
        dict(row)
        for row in connection.execute(
            select(triggers_table).where(triggers_table.c.created_at < cutoff)
        ).mappings()
    ]
    heartbeats = [
        dict(row)
        for row in connection.execute(
            select(heartbeats_table).where(heartbeats_table.c.seen_at < cutoff)
        ).mappings()
    ]
    return {
        "runs": runs,
        "modules": modules,
        "logs": logs,
        "triggers": triggers,
        "heartbeats": heartbeats,
    }


def purge_retention_with_backup(
    engine: Engine,
    *,
    days: int = 30,
    apply: bool = False,
    backup_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if days < 1:
        raise ValueError("days must be >= 1")
    cutoff = (now or utcnow()) - timedelta(days=days)
    with engine.begin() as connection:
        data = _collect(connection, cutoff, lock=apply)
        result: dict[str, Any] = {
            "mode": "apply" if apply else "dry-run",
            "days": days,
            "cutoff": _json_value(cutoff),
            "counts": {name: len(rows) for name, rows in data.items()},
            "backup": None,
        }
        if not apply or not any(data.values()):
            return result
        if backup_dir is None:
            raise ValueError("backup_dir é obrigatório no modo apply.")

        backup = _write_backup(backup_dir, cutoff, data)
        run_ids = [str(row["run_id"]) for row in data["runs"]]
        if run_ids:
            connection.execute(delete(modules_table).where(modules_table.c.run_id.in_(run_ids)))
            connection.execute(delete(logs_table).where(logs_table.c.run_id.in_(run_ids)))
            connection.execute(delete(runs_table).where(runs_table.c.run_id.in_(run_ids)))
        if data["triggers"]:
            connection.execute(delete(triggers_table).where(triggers_table.c.created_at < cutoff))
        if data["heartbeats"]:
            connection.execute(delete(heartbeats_table).where(heartbeats_table.c.seen_at < cutoff))
        result["backup"] = str(backup)
        return result


def _restore_value(column: Any, value: Any) -> Any:
    if value is None or not isinstance(value, str):
        return value
    if isinstance(column.type, type(runs_table.c.started_at.type)):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return value


def _restore_rows(connection: Connection, table: Any, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    primary_keys = list(table.primary_key.columns)
    existing = 0
    for row in rows:
        condition = None
        for column in primary_keys:
            clause = column == row[column.name]
            condition = clause if condition is None else condition & clause
        if connection.execute(select(table).where(condition).limit(1)).first():
            existing += 1
    if existing == len(rows):
        return 0
    if existing:
        raise RuntimeError(f"Restauro parcial detetado em {table.name}; operação abortada.")
    converted = [
        {column.name: _restore_value(column, row.get(column.name)) for column in table.columns}
        for row in rows
    ]
    connection.execute(insert(table), converted)
    return len(rows)


def restore_backup(engine: Engine, backup_path: Path) -> dict[str, Any]:
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    if payload.get("format") != BACKUP_FORMAT:
        raise ValueError("Formato de backup desconhecido.")
    data = payload.get("tables")
    if not isinstance(data, dict):
        raise ValueError("Backup incompleto.")
    order = ("runs", "modules", "logs", "triggers", "heartbeats")
    with engine.begin() as connection:
        restored = {
            name: _restore_rows(connection, TABLES[name], list(data.get(name) or []))
            for name in order
        }
    return {"mode": "restore", "restored": restored}


def main() -> None:
    parser = argparse.ArgumentParser(description="Retenção de telemetria com backup transacional.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", type=Path)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = parser.parse_args()
    result = (
        restore_backup(get_engine(), args.restore)
        if args.restore
        else purge_retention_with_backup(
            get_engine(),
            days=args.days,
            apply=args.apply,
            backup_dir=args.backup_dir if args.apply else None,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
