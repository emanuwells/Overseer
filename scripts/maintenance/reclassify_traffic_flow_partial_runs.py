#!/usr/bin/env python3
"""Reclassifica runs parciais Traffic Flow de failed para warning."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import and_, exists, select, update
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from overseer_core.store import (  # noqa: E402
    get_engine,
    logs_table,
    modules_table,
    runs_table,
)


PIPELINE_ID = "traffic_flow"
MODULE_ID = "traffic_flow"
SINCE_UTC = datetime(2026, 8, 25, 4, 15, 3)
FAILED_CAMERA_MARKER = "- Maia Nascente: ok=False"
HEALTHY_CAMERA_MARKER = "- Maia Poente: ok=True"
BACKUP_FORMAT = "overseer-traffic-flow-status-v1"
DEFAULT_BACKUP_DIR = Path(
    "/home/eferreira/Dev/backups/overseer/traffic_flow-status-reclassification"
)


def _candidate_statement(*, lock: bool = False):
    failed_camera_seen = exists(
        select(logs_table.c.log_id).where(
            and_(
                logs_table.c.run_id == runs_table.c.run_id,
                logs_table.c.message.contains(FAILED_CAMERA_MARKER),
            )
        )
    )
    healthy_camera_seen = exists(
        select(logs_table.c.log_id).where(
            and_(
                logs_table.c.run_id == runs_table.c.run_id,
                logs_table.c.message.contains(HEALTHY_CAMERA_MARKER),
            )
        )
    )
    statement = (
        select(
            runs_table.c.run_id,
            runs_table.c.status,
            runs_table.c.started_at,
        )
        .where(
            and_(
                runs_table.c.pipeline_id == PIPELINE_ID,
                runs_table.c.status == "failed",
                runs_table.c.started_at >= SINCE_UTC,
                failed_camera_seen,
                healthy_camera_seen,
            )
        )
        .order_by(runs_table.c.started_at)
    )
    return statement.with_for_update() if lock else statement


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return value


def _write_backup(
    backup_dir: Path,
    runs: list[dict[str, Any]],
    modules: list[dict[str, Any]],
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_dir / f"traffic_flow_status_{timestamp}.json"
    payload = {
        "format": BACKUP_FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "criteria": {
            "pipeline_id": PIPELINE_ID,
            "since_utc": SINCE_UTC.isoformat() + "Z",
            "failed_camera_marker": FAILED_CAMERA_MARKER,
            "healthy_camera_marker": HEALTHY_CAMERA_MARKER,
        },
        "runs": [{key: _json_value(value) for key, value in row.items()} for row in runs],
        "modules": [{key: _json_value(value) for key, value in row.items()} for row in modules],
    }

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=backup_dir,
        prefix=".traffic_flow_status_",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    temporary.replace(destination)
    return destination


def reclassify_partial_runs(
    engine: Engine,
    *,
    apply: bool = False,
    backup_dir: Path | None = None,
) -> dict[str, Any]:
    """Pré-visualiza ou aplica a reclassificação de runs parciais."""
    with engine.begin() as connection:
        candidates = [
            dict(row)
            for row in connection.execute(
                _candidate_statement(lock=apply)
            ).mappings()
        ]
        run_ids = [row["run_id"] for row in candidates]
        modules: list[dict[str, Any]] = []
        if run_ids:
            modules = [
                dict(row)
                for row in connection.execute(
                    select(
                        modules_table.c.event_id,
                        modules_table.c.run_id,
                        modules_table.c.module_id,
                        modules_table.c.status,
                    ).where(
                        and_(
                            modules_table.c.run_id.in_(run_ids),
                            modules_table.c.module_id == MODULE_ID,
                            modules_table.c.status == "failed",
                        )
                    )
                ).mappings()
            ]

        if len(modules) != len(candidates):
            raise RuntimeError(
                "Seleção insegura: cada run candidata deve ter exatamente um módulo "
                f"{MODULE_ID!r} failed (runs={len(candidates)}, modules={len(modules)})."
            )

        result: dict[str, Any] = {
            "mode": "apply" if apply else "dry-run",
            "candidates": len(candidates),
            "modules": len(modules),
            "oldest": _json_value(candidates[0]["started_at"]) if candidates else None,
            "newest": _json_value(candidates[-1]["started_at"]) if candidates else None,
            "backup": None,
            "updated_runs": 0,
            "updated_modules": 0,
        }
        if not apply or not candidates:
            return result
        if backup_dir is None:
            raise ValueError("backup_dir é obrigatório no modo apply.")

        backup = _write_backup(backup_dir, candidates, modules)
        module_ids = [row["event_id"] for row in modules]
        updated_runs = connection.execute(
            update(runs_table)
            .where(and_(runs_table.c.run_id.in_(run_ids), runs_table.c.status == "failed"))
            .values(status="warning")
        ).rowcount
        updated_modules = connection.execute(
            update(modules_table)
            .where(
                and_(
                    modules_table.c.event_id.in_(module_ids),
                    modules_table.c.status == "failed",
                )
            )
            .values(status="warning")
        ).rowcount
        if updated_runs != len(candidates) or updated_modules != len(modules):
            raise RuntimeError(
                "Contagem alterada durante a transação; rollback automático "
                f"(runs={updated_runs}/{len(candidates)}, "
                f"modules={updated_modules}/{len(modules)})."
            )
        result.update(
            backup=str(backup),
            updated_runs=updated_runs,
            updated_modules=updated_modules,
        )
        return result


def restore_backup(engine: Engine, backup_path: Path) -> dict[str, Any]:
    """Restaura os estados guardados por :func:`reclassify_partial_runs`."""
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    if payload.get("format") != BACKUP_FORMAT:
        raise ValueError("Formato de backup desconhecido.")
    runs = payload.get("runs") or []
    modules = payload.get("modules") or []
    if not runs or len(runs) != len(modules):
        raise ValueError("Backup incompleto ou vazio.")
    if any(row.get("status") != "failed" for row in runs + modules):
        raise ValueError("O backup contém estados de origem inesperados.")

    run_ids = [str(row["run_id"]) for row in runs]
    module_ids = [int(row["event_id"]) for row in modules]
    with engine.begin() as connection:
        current_run_statuses = list(
            connection.execute(
                select(runs_table.c.status).where(runs_table.c.run_id.in_(run_ids))
            ).scalars()
        )
        current_module_statuses = list(
            connection.execute(
                select(modules_table.c.status).where(modules_table.c.event_id.in_(module_ids))
            ).scalars()
        )
        if len(current_run_statuses) != len(runs) or len(current_module_statuses) != len(modules):
            raise RuntimeError("O backup referencia linhas inexistentes; restauro abortado.")
        if set(current_run_statuses) == {"failed"} and set(current_module_statuses) == {"failed"}:
            return {"mode": "restore", "restored_runs": 0, "restored_modules": 0}
        if set(current_run_statuses) != {"warning"} or set(current_module_statuses) != {"warning"}:
            raise RuntimeError("Estado atual não corresponde integralmente ao backup; restauro abortado.")

        restored_runs = connection.execute(
            update(runs_table)
            .where(and_(runs_table.c.run_id.in_(run_ids), runs_table.c.status == "warning"))
            .values(status="failed")
        ).rowcount
        restored_modules = connection.execute(
            update(modules_table)
            .where(
                and_(
                    modules_table.c.event_id.in_(module_ids),
                    modules_table.c.status == "warning",
                )
            )
            .values(status="failed")
        ).rowcount
        if restored_runs != len(runs) or restored_modules != len(modules):
            raise RuntimeError("Restauro incompleto; rollback automático.")
        return {
            "mode": "restore",
            "restored_runs": restored_runs,
            "restored_modules": restored_modules,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reclassifica falhas parciais Traffic Flow como warning."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Aplica a reclassificação.")
    mode.add_argument("--restore", type=Path, help="Restaura um backup criado pelo script.")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Diretório externo para backups (default: {DEFAULT_BACKUP_DIR}).",
    )
    args = parser.parse_args()

    if args.restore:
        result = restore_backup(get_engine(), args.restore)
    else:
        result = reclassify_partial_runs(
            get_engine(),
            apply=args.apply,
            backup_dir=args.backup_dir if args.apply else None,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
