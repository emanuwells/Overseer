from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from src.pm_runtime.settings import settings
from src.pm_runtime.db import get_engine


def main() -> int:
    args = parse_args()
    logs_table = safe_name(settings.runs_table)
    archive_table = safe_name(args.archive_table)
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    cutoff_iso = cutoff_dt.strftime("%Y-%m-%d %H:%M:%S")
    batch_id = uuid.uuid4().hex

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {archive_table} LIKE {logs_table}"))
        ensure_archive_columns(conn, archive_table)

        logs_cols = table_columns(conn, logs_table)
        archive_cols = table_columns(conn, archive_table)
        time_expr = time_expr_for(logs_cols)
        if not time_expr:
            raise RuntimeError(f"Tabela '{logs_table}' sem coluna temporal valida (startDate/LogDate/regDate).")

        total = int(
            conn.execute(
                text(f"SELECT COUNT(*) AS c FROM {logs_table} WHERE {time_expr} < :cutoff"),
                {"cutoff": cutoff_iso},
            )
            .mappings()
            .first()["c"]
        )
        if total == 0:
            write_status(batch_id, 0, 0, args.days)
            return 0

        common_cols = [c for c in logs_cols if c in archive_cols]
        if "archived_at" not in archive_cols or "archive_batch_id" not in archive_cols:
            raise RuntimeError("Tabela de arquivo sem colunas de auditoria.")

        insert_sql = text(
            f"""
            INSERT INTO {archive_table} ({", ".join(common_cols)}, archived_at, archive_batch_id)
            SELECT {", ".join(common_cols)}, UTC_TIMESTAMP(), :batch_id
            FROM {logs_table}
            WHERE {time_expr} < :cutoff
            """
        )
        inserted = conn.execute(insert_sql, {"batch_id": batch_id, "cutoff": cutoff_iso}).rowcount or 0
        if inserted != total:
            raise RuntimeError(f"Contagem divergente no arquivo: esperado={total}, inserido={inserted}.")

        deleted = conn.execute(
            text(f"DELETE FROM {logs_table} WHERE {time_expr} < :cutoff"),
            {"cutoff": cutoff_iso},
        ).rowcount or 0
        if deleted != total:
            raise RuntimeError(f"Contagem divergente no delete: esperado={total}, apagado={deleted}.")

    write_status(batch_id, total, total, args.days)
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Arquiva logs antigos para tabela de arquivo.")
    p.add_argument("--days", type=int, default=30, help="Arquivar registos mais antigos que N dias.")
    p.add_argument("--archive-table", default="logs_archive", help="Tabela de arquivo.")
    return p.parse_args()


def safe_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", value or ""):
        raise ValueError(f"Nome de tabela invalido: {value!r}")
    return value


def table_columns(conn, table_name: str) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
            """
        ),
        {"table_name": table_name},
    ).mappings().all()
    return [str(r["COLUMN_NAME"]) for r in rows]


def ensure_archive_columns(conn, archive_table: str) -> None:
    cols = set(table_columns(conn, archive_table))
    if "archived_at" not in cols:
        conn.execute(text(f"ALTER TABLE {archive_table} ADD COLUMN archived_at DATETIME NULL"))
    if "archive_batch_id" not in cols:
        conn.execute(text(f"ALTER TABLE {archive_table} ADD COLUMN archive_batch_id VARCHAR(64) NULL"))


def time_expr_for(cols: list[str]) -> str:
    if "startDate" in cols and "LogDate" in cols:
        return "COALESCE(startDate, LogDate)"
    if "startDate" in cols:
        return "startDate"
    if "LogDate" in cols:
        return "LogDate"
    if "regDate" in cols:
        return "regDate"
    return ""


def write_status(batch_id: str, moved: int, deleted: int, days: int) -> None:
    status = {
        "ok": True,
        "batch_id": batch_id,
        "moved": moved,
        "deleted": deleted,
        "days": days,
        "last_archive_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    path = ROOT / "runtime" / "archive_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
