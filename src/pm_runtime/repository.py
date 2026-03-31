from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import re
from statistics import median
from typing import Any

from sqlalchemy import text

from .settings import settings
from .db import get_engine
from .normalization import parse_decimal, parse_dt, to_iso


@dataclass
class RunRecord:
    id: int
    pipeline_id: str
    script_name: str
    hostname: str
    os_name: str
    start_date: datetime | None
    end_date: datetime | None
    status: str
    exec_time: float
    usage_cpu: float
    usage_memoria: float
    error_preview: str
    error_message: str | None
    log_message: str | None
    owner: str
    criticality: str
    trigger_type: str | None = None


class MonitorRepository:
    def load_runs(self) -> list[RunRecord]:
        return self._load_from_db()

    def load_run_by_id(self, run_id: int) -> RunRecord | None:
        engine = get_engine()
        table = _safe_table_name(settings.runs_table)
        cols = self._table_columns(table)

        pipeline_expr = _pipeline_expr(cols)
        owner_expr = "COALESCE(owner, 'unknown')" if "owner" in cols else "'unknown'"
        criticality_expr = "COALESCE(criticality, 'medium')" if "criticality" in cols else "'medium'"
        trigger_type_expr = "triggerType" if "triggerType" in cols else "NULL"
        host_expr = "COALESCE(hostname, '')" if "hostname" in cols else "''"
        os_expr = _os_expr(cols)
        status_expr = "UPPER(COALESCE(status, 'UNKNOWN'))" if "status" in cols else "'UNKNOWN'"
        exec_expr = "COALESCE(TIME_TO_SEC(execTime), execTime, 0)" if "execTime" in cols else "0"
        cpu_expr = "usageCPU" if "usageCPU" in cols else "0"
        mem_expr = "usageMemoria" if "usageMemoria" in cols else "0"
        start_expr = "startDate" if "startDate" in cols else ("LogDate" if "LogDate" in cols else "NULL")
        end_expr = "endDate" if "endDate" in cols else "NULL"
        error_preview_expr = _error_preview_expr(cols)
        error_expr = "errorMessage" if "errorMessage" in cols else "NULL"
        log_expr = "logMessage" if "logMessage" in cols else "NULL"

        sql = text(
            f"""
            SELECT
                CAST(id AS SIGNED) AS id,
                {pipeline_expr} AS pipeline_id,
                COALESCE(scriptName, 'pipeline-sem-nome') AS script_name,
                {host_expr} AS hostname,
                {os_expr} AS os_name,
                {start_expr} AS start_date,
                {end_expr} AS end_date,
                {status_expr} AS status,
                {exec_expr} AS exec_time,
                {cpu_expr} AS usage_cpu,
                {mem_expr} AS usage_memoria,
                {error_preview_expr} AS error_preview,
                {error_expr} AS error_message,
                {log_expr} AS log_message,
                {owner_expr} AS owner,
                {criticality_expr} AS criticality,
                {trigger_type_expr} AS trigger_type
            FROM {table}
            WHERE id = :run_id
            LIMIT 1
            """
        )
        with engine.connect() as conn:
            row = conn.execute(sql, {"run_id": run_id}).mappings().first()
        if not row:
            return None
        return self._to_run_record(dict(row))

    def load_error_detail(self, run_id: int) -> str | None:
        engine = get_engine()
        table = _safe_table_name(settings.runs_table)
        cols = self._table_columns(table)
        if "errorMessage" not in cols:
            return None
        sql = text(f"SELECT errorMessage AS error_message FROM {table} WHERE id = :run_id LIMIT 1")
        with engine.connect() as conn:
            row = conn.execute(sql, {"run_id": run_id}).mappings().first()
        if not row:
            return None
        value = row.get("error_message")
        return str(value) if value is not None else None

    def _table_columns(self, table: str) -> set[str]:
        engine = get_engine()
        sql = text(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
            """
        )
        with engine.connect() as conn:
            rows = conn.execute(sql, {"table_name": table}).mappings().all()
        cols = {str(r["COLUMN_NAME"]) for r in rows}
        if not cols:
            raise RuntimeError(f"Tabela '{table}' nao encontrada ou sem colunas visiveis.")
        if "id" not in cols or "scriptName" not in cols:
            raise RuntimeError(f"Tabela '{table}' sem colunas minimas obrigatorias (id, scriptName).")
        return cols

    def _load_from_db(self) -> list[RunRecord]:
        table = _safe_table_name(settings.runs_table)
        cols = self._table_columns(table)

        pipeline_expr = _pipeline_expr(cols)
        owner_expr = "COALESCE(owner, 'unknown')" if "owner" in cols else "'unknown'"
        criticality_expr = "COALESCE(criticality, 'medium')" if "criticality" in cols else "'medium'"
        trigger_type_expr = "triggerType" if "triggerType" in cols else "NULL"
        host_expr = "COALESCE(hostname, '')" if "hostname" in cols else "''"
        os_expr = _os_expr(cols)
        status_expr = "UPPER(COALESCE(status, 'UNKNOWN'))" if "status" in cols else "'UNKNOWN'"
        exec_expr = "COALESCE(TIME_TO_SEC(execTime), execTime, 0)" if "execTime" in cols else "0"
        cpu_expr = "usageCPU" if "usageCPU" in cols else "0"
        mem_expr = "usageMemoria" if "usageMemoria" in cols else "0"
        start_expr = "startDate" if "startDate" in cols else ("LogDate" if "LogDate" in cols else "NULL")
        end_expr = "endDate" if "endDate" in cols else "NULL"
        error_preview_expr = _error_preview_expr(cols)
        error_expr = "errorMessage" if "errorMessage" in cols else "NULL"
        log_expr = "logMessage" if "logMessage" in cols else "NULL"

        sql = text(
            f"""
            SELECT
                CAST(id AS SIGNED) AS id,
                {pipeline_expr} AS pipeline_id,
                COALESCE(scriptName, 'pipeline-sem-nome') AS script_name,
                {host_expr} AS hostname,
                {os_expr} AS os_name,
                {start_expr} AS start_date,
                {end_expr} AS end_date,
                {status_expr} AS status,
                {exec_expr} AS exec_time,
                {cpu_expr} AS usage_cpu,
                {mem_expr} AS usage_memoria,
                {error_preview_expr} AS error_preview,
                {error_expr} AS error_message,
                {log_expr} AS log_message,
                {owner_expr} AS owner,
                {criticality_expr} AS criticality,
                {trigger_type_expr} AS trigger_type
            FROM {table}
            ORDER BY {start_expr} DESC
            LIMIT 500000
            """
        )

        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()

        return [self._to_run_record(dict(row)) for row in rows]

    def _to_run_record(self, row: dict[str, Any]) -> RunRecord:
        return RunRecord(
            id=int(row.get("id") or 0),
            pipeline_id=str(row.get("pipeline_id") or row.get("script_name") or "pipeline-sem-nome"),
            script_name=str(row.get("script_name") or "pipeline-sem-nome"),
            hostname=str(row.get("hostname") or ""),
            os_name=str(row.get("os_name") or ""),
            start_date=parse_dt(row.get("start_date")),
            end_date=parse_dt(row.get("end_date")),
            status=_normalize_status(row.get("status")),
            exec_time=parse_decimal(row.get("exec_time")),
            usage_cpu=parse_decimal(row.get("usage_cpu")),
            usage_memoria=parse_decimal(row.get("usage_memoria")),
            error_preview=str(row.get("error_preview") or ""),
            error_message=str(row.get("error_message")) if row.get("error_message") is not None else None,
            log_message=str(row.get("log_message")) if row.get("log_message") is not None else None,
            owner=str(row.get("owner") or "unknown"),
            criticality=str(row.get("criticality") or "medium").lower(),
            trigger_type=str(row.get("trigger_type")) if row.get("trigger_type") is not None else None,
        )


def _safe_table_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", value or ""):
        raise ValueError(f"RUNS_TABLE invalida: {value!r}")
    return value


def _pipeline_expr(cols: set[str]) -> str:
    if "pipelineId" in cols and "pipeline_id" in cols:
        return "COALESCE(NULLIF(pipelineId, ''), NULLIF(pipeline_id, ''), scriptName, 'pipeline-sem-nome')"
    if "pipelineId" in cols:
        return "COALESCE(NULLIF(pipelineId, ''), scriptName, 'pipeline-sem-nome')"
    if "pipeline_id" in cols:
        return "COALESCE(NULLIF(pipeline_id, ''), scriptName, 'pipeline-sem-nome')"
    return "COALESCE(scriptName, 'pipeline-sem-nome')"


def _os_expr(cols: set[str]) -> str:
    if "osName" in cols and "OS" in cols and "osPlatform" in cols:
        return "COALESCE(NULLIF(osName, ''), NULLIF(OS, ''), NULLIF(osPlatform, ''), '')"
    if "osName" in cols and "OS" in cols:
        return "COALESCE(NULLIF(osName, ''), NULLIF(OS, ''), '')"
    if "osName" in cols and "osPlatform" in cols:
        return "COALESCE(NULLIF(osName, ''), NULLIF(osPlatform, ''), '')"
    if "OS" in cols:
        return "COALESCE(OS, '')"
    if "osName" in cols:
        return "COALESCE(osName, '')"
    if "osPlatform" in cols:
        return "COALESCE(osPlatform, '')"
    return "''"


def _normalize_status(value: Any) -> str:
    raw = str(value or "UNKNOWN").strip().upper()
    if raw in {"OK", "SUCCESS", "SUCESSO"}:
        return "OK"
    if raw in {"NOK", "FAILED", "FAIL", "ERROR", "CANCELED", "CANCELLED"}:
        return "NOK"
    return raw


def _error_preview_expr(cols: set[str]) -> str:
    if "errorPreview" in cols:
        return "COALESCE(errorPreview, '')"
    if "errorMessage" in cols:
        return "LEFT(COALESCE(errorMessage, ''), 200)"
    return "''"


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = math.ceil(0.95 * len(ordered)) - 1
    idx = max(0, min(idx, len(ordered) - 1))
    return ordered[idx]


def build_duration_label(seconds: float) -> str:
    total = int(max(seconds, 0))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def compute_pipeline_cadence_hours(sorted_runs: list[RunRecord]) -> float | None:
    if len(sorted_runs) < 2:
        return None
    intervals = []
    for i in range(len(sorted_runs) - 1):
        a, b = sorted_runs[i], sorted_runs[i + 1]
        if not a.start_date or not b.start_date:
            continue
        delta_h = abs((a.start_date - b.start_date).total_seconds()) / 3600
        if delta_h > 0:
            intervals.append(delta_h)
    if not intervals:
        return None
    return float(median(intervals))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_run_summary(run: RunRecord) -> dict[str, Any]:
    return {
        "id": run.id,
        "pipelineId": run.pipeline_id,
        "scriptName": run.script_name,
        "hostname": run.hostname,
        "osName": run.os_name,
        "startDate": to_iso(run.start_date),
        "endDate": to_iso(run.end_date),
        "status": run.status,
        "execTime": round(run.exec_time, 2),
        "usageCPU": round(run.usage_cpu, 2),
        "usageMemoria": round(run.usage_memoria, 2),
        "durationLabel": build_duration_label(run.exec_time),
        "cpuLabel": f"{run.usage_cpu:.1f}%",
        "memLabel": f"{run.usage_memoria:.1f} MB",
        "errorPreview": run.error_preview[:200],
        "triggerType": run.trigger_type,
    }


def group_runs_by_pipeline(runs: list[RunRecord]) -> dict[str, list[RunRecord]]:
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for run in runs:
        grouped[run.pipeline_id].append(run)
    for pipeline_id in grouped:
        grouped[pipeline_id].sort(
            key=lambda r: r.start_date or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
    return grouped


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return max(0, int(cursor))
    except ValueError:
        return 0


def encode_cursor(offset: int, total: int) -> str | None:
    return str(offset) if offset < total else None




