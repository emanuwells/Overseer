#!/usr/bin/env python3
"""Consolida a run interna do INE na run externa do manifest Overseer."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Connection, Engine

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from overseer_core.store import (  # noqa: E402
    get_engine,
    json_dump,
    json_load,
    logs_table,
    modules_table,
    parse_dt,
    runs_table,
    utcnow,
)

PIPELINE_ID = "ine_pipeline"
BACKUP_FORMAT = "overseer-ine-run-dedup-v1"
DEFAULT_BACKUP_DIR = Path("/home/eferreira/Dev/backups/overseer/ine-run-dedup")


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return value


def _serialize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: _json_value(value) for key, value in row.items()} for row in rows]


def _write_backup(backup_dir: Path, payload: dict[str, Any]) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_dir / f"ine_dedup_{stamp}.json"
    document = {
        "format": BACKUP_FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **payload,
    }
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=backup_dir, prefix=".ine_dedup_", suffix=".tmp", delete=False
    ) as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    temporary.replace(destination)
    return destination


def _candidate_pairs(connection: Connection, *, lock: bool) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    statement = select(runs_table).where(runs_table.c.pipeline_id == PIPELINE_ID)
    if lock:
        statement = statement.with_for_update()
    rows = [dict(row) for row in connection.execute(statement).mappings()]
    wrappers = [
        row
        for row in rows
        if str(row.get("trigger_type") or "") == "cron"
        and (json_load(row.get("metadata_json")) or {}).get("runner") == "manifest"
    ]
    internals = [row for row in rows if str(row.get("trigger_type") or "") == "pipeline"]
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used_internal: set[str] = set()
    for wrapper in sorted(wrappers, key=lambda row: row["started_at"]):
        wrapper_started = parse_dt(wrapper.get("started_at"))
        matches = []
        for internal in internals:
            if internal["run_id"] in used_internal or internal.get("host_id") != wrapper.get("host_id"):
                continue
            internal_started = parse_dt(internal.get("started_at"))
            if wrapper_started and internal_started and abs((internal_started - wrapper_started).total_seconds()) <= 180:
                matches.append(internal)
        if len(matches) > 1:
            raise RuntimeError(f"Seleção ambígua para a run {wrapper['run_id']}.")
        if matches:
            used_internal.add(str(matches[0]["run_id"]))
            pairs.append((wrapper, matches[0]))
    return pairs


def _severity(status: Any) -> int:
    raw = str(status or "").lower()
    if raw in {"failed", "nok", "error"}:
        return 2
    if raw in {"warning", "warn", "parcial"}:
        return 1
    return 0


def _merged_status(wrapper: dict[str, Any], internal: dict[str, Any]) -> str:
    source = internal if _severity(internal.get("status")) > _severity(wrapper.get("status")) else wrapper
    return str(source.get("status") or "ok").lower()


def deduplicate_ine_runs(
    engine: Engine,
    *,
    apply: bool = False,
    backup_dir: Path | None = None,
) -> dict[str, Any]:
    with engine.begin() as connection:
        pairs = _candidate_pairs(connection, lock=apply)
        wrapper_ids = [str(wrapper["run_id"]) for wrapper, _ in pairs]
        internal_ids = [str(internal["run_id"]) for _, internal in pairs]
        all_ids = wrapper_ids + internal_ids
        modules = (
            [dict(row) for row in connection.execute(select(modules_table).where(modules_table.c.run_id.in_(all_ids))).mappings()]
            if all_ids
            else []
        )
        logs = (
            [dict(row) for row in connection.execute(select(logs_table).where(logs_table.c.run_id.in_(all_ids))).mappings()]
            if all_ids
            else []
        )
        result: dict[str, Any] = {
            "mode": "apply" if apply else "dry-run",
            "pairs": len(pairs),
            "oldest": _json_value(pairs[0][0]["started_at"]) if pairs else None,
            "newest": _json_value(pairs[-1][0]["started_at"]) if pairs else None,
            "moved_modules": sum(1 for row in modules if row["run_id"] in internal_ids),
            "moved_logs": sum(1 for row in logs if row["run_id"] in internal_ids),
            "backup": None,
        }
        if not apply or not pairs:
            return result
        if backup_dir is None:
            raise ValueError("backup_dir é obrigatório no modo apply.")

        backup = _write_backup(
            backup_dir,
            {
                "pairs": [{"wrapper": wrapper["run_id"], "internal": internal["run_id"]} for wrapper, internal in pairs],
                "runs": _serialize([row for pair in pairs for row in pair]),
                "modules": _serialize(modules),
                "logs": _serialize(logs),
            },
        )
        for wrapper, internal in pairs:
            wrapper_id = str(wrapper["run_id"])
            internal_id = str(internal["run_id"])
            wrapper_meta = json_load(wrapper.get("metadata_json")) or {}
            wrapper_meta["embedded_run"] = {
                "run_id": internal_id,
                "trigger_type": internal.get("trigger_type"),
                "metadata": json_load(internal.get("metadata_json")) or {},
            }
            ended_candidates = [value for value in (wrapper.get("ended_at"), internal.get("ended_at")) if value]
            ended_at = max(ended_candidates) if ended_candidates else None
            started_at = min(wrapper["started_at"], internal["started_at"])
            duration = (ended_at - started_at).total_seconds() if ended_at else wrapper.get("duration_sec")
            connection.execute(
                update(modules_table).where(modules_table.c.run_id == internal_id).values(run_id=wrapper_id)
            )
            connection.execute(
                update(logs_table).where(logs_table.c.run_id == internal_id).values(run_id=wrapper_id)
            )
            connection.execute(
                update(runs_table)
                .where(runs_table.c.run_id == wrapper_id)
                .values(
                    status=_merged_status(wrapper, internal),
                    started_at=started_at,
                    ended_at=ended_at,
                    duration_sec=duration,
                    error_message=wrapper.get("error_message") or internal.get("error_message"),
                    metadata_json=json_dump(wrapper_meta),
                    updated_at=utcnow(),
                )
            )
            connection.execute(delete(runs_table).where(runs_table.c.run_id == internal_id))
        remaining = connection.execute(
            select(runs_table.c.run_id).where(runs_table.c.run_id.in_(internal_ids))
        ).all()
        if remaining:
            raise RuntimeError("Deduplicação incompleta; rollback automático.")
        result["backup"] = str(backup)
        return result


def _datetime_value(value: Any) -> Any:
    if isinstance(value, str) and ("T" in value or value.endswith("Z")):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return value
    return value


def restore_backup(engine: Engine, backup_path: Path) -> dict[str, Any]:
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    if payload.get("format") != BACKUP_FORMAT:
        raise ValueError("Formato de backup desconhecido.")
    runs = list(payload.get("runs") or [])
    modules = list(payload.get("modules") or [])
    logs = list(payload.get("logs") or [])
    pairs = list(payload.get("pairs") or [])
    if not pairs or len(runs) != len(pairs) * 2:
        raise ValueError("Backup incompleto.")

    original_runs = {str(row["run_id"]): row for row in runs}
    with engine.begin() as connection:
        internal_ids = [str(pair["internal"]) for pair in pairs]
        existing_internal = set(
            connection.execute(
                select(runs_table.c.run_id).where(runs_table.c.run_id.in_(internal_ids))
            ).scalars()
        )
        if len(existing_internal) == len(internal_ids):
            return {"mode": "restore", "restored_pairs": 0}
        if existing_internal:
            raise RuntimeError("Restauro parcial detetado; operação abortada.")

        for pair in pairs:
            wrapper_id = str(pair["wrapper"])
            internal_id = str(pair["internal"])
            wrapper = original_runs[wrapper_id]
            internal = original_runs[internal_id]
            connection.execute(
                update(runs_table)
                .where(runs_table.c.run_id == wrapper_id)
                .values(**{key: _datetime_value(value) for key, value in wrapper.items()})
            )
            connection.execute(
                insert(runs_table).values(**{key: _datetime_value(value) for key, value in internal.items()})
            )

        for table, rows, key in ((modules_table, modules, "event_id"), (logs_table, logs, "log_id")):
            for row in rows:
                connection.execute(
                    update(table)
                    .where(getattr(table.c, key) == row[key])
                    .values(**{name: _datetime_value(value) for name, value in row.items()})
                )
    return {"mode": "restore", "restored_pairs": len(pairs)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolida runs duplicadas do INE.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", type=Path)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = parser.parse_args()
    result = (
        restore_backup(get_engine(), args.restore)
        if args.restore
        else deduplicate_ine_runs(
            get_engine(), apply=args.apply, backup_dir=args.backup_dir if args.apply else None
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
