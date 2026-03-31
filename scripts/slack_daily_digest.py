from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from overseer_monitor.notifiers.slack import SlackNotifier
from src.pm_runtime.db import get_engine
from src.pm_runtime.settings import settings


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Envia resumo diario de runs para Slack.")
    p.add_argument("--date", dest="for_date", default=None, help="Data UTC no formato YYYY-MM-DD. Default: hoje UTC.")
    p.add_argument("--top", type=int, default=5, help="Top N pipelines/erros no resumo.")
    p.add_argument("--slack-config", default=None, help="Caminho para slack.json. Default: secrets/slack.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    target = parse_utc_date(args.for_date)
    start_dt = datetime.combine(target, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    runs = load_runs_in_range(start_dt, end_dt)
    message = build_digest_message(target, runs, top_n=max(1, min(args.top, 20)))

    notifier = build_notifier(args.slack_config)
    if not notifier or not notifier.enabled:
        print("Slack nao configurado; resumo nao enviado.")
        return 1

    ok = notifier.send(message)
    if not ok:
        print("Falha ao enviar resumo diario para Slack.")
        return 2
    print("Resumo diario enviado para Slack.")
    return 0


def parse_utc_date(raw: str | None) -> date:
    if not raw:
        return datetime.now(timezone.utc).date()
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Data invalida: {raw}. Usa YYYY-MM-DD.") from exc


def build_notifier(config_path: str | None) -> SlackNotifier | None:
    if config_path:
        return SlackNotifier(config_path=config_path)
    candidate = ROOT / "secrets" / "slack.json"
    if candidate.exists():
        return SlackNotifier(config_path=candidate)
    return None


def load_runs_in_range(start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
    table = safe_name(settings.runs_table)
    engine = get_engine()
    cols = table_columns(engine, table)
    if not cols:
        return []

    time_expr = time_expression(cols)
    if not time_expr:
        return []

    pipeline_expr = pipeline_expression(cols)
    status_expr = "UPPER(COALESCE(status, 'UNKNOWN'))" if "status" in cols else "'UNKNOWN'"
    error_expr = "COALESCE(errorMessage, errorPreview, '')" if "errorMessage" in cols else ("COALESCE(errorPreview, '')" if "errorPreview" in cols else "''")

    sql = text(
        f"""
        SELECT
          CAST(id AS SIGNED) AS id,
          {pipeline_expr} AS pipeline_id,
          {status_expr} AS status,
          {error_expr} AS error_message,
          {time_expr} AS started_at
        FROM {table}
        WHERE {time_expr} >= :start_dt
          AND {time_expr} < :end_dt
        ORDER BY {time_expr} ASC
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"start_dt": start_dt.strftime("%Y-%m-%d %H:%M:%S"), "end_dt": end_dt.strftime("%Y-%m-%d %H:%M:%S")}).mappings().all()
    return [dict(r) for r in rows]


def build_digest_message(target_date: date, runs: list[dict[str, Any]], top_n: int) -> str:
    total = len(runs)
    ok = sum(1 for r in runs if str(r.get("status") or "").upper() == "OK")
    nok = sum(1 for r in runs if str(r.get("status") or "").upper() == "NOK")
    success = (ok / total * 100.0) if total else 100.0

    by_pipeline_total: Counter[str] = Counter()
    by_pipeline_nok: Counter[str] = Counter()
    error_counter: Counter[str] = Counter()

    for r in runs:
        pipeline = str(r.get("pipeline_id") or "pipeline-sem-nome")
        status = str(r.get("status") or "UNKNOWN").upper()
        by_pipeline_total[pipeline] += 1
        if status == "NOK":
            by_pipeline_nok[pipeline] += 1
            err = normalize_error(str(r.get("error_message") or "erro_sem_detalhe"))
            error_counter[err] += 1

    top_failed = by_pipeline_nok.most_common(top_n)
    top_errors = error_counter.most_common(top_n)
    active_pipelines = len(by_pipeline_total)

    lines: list[str] = []
    lines.append(f":bar_chart: Resumo diario pipelines ({target_date.isoformat()} UTC)")
    lines.append(f"Total runs: {total} | OK: {ok} | NOK: {nok} | Success rate: {success:.1f}% | Pipelines ativas: {active_pipelines}")

    if top_failed:
        lines.append("")
        lines.append("Top pipelines com falhas:")
        for name, nfail in top_failed:
            ntotal = by_pipeline_total.get(name, 0)
            lines.append(f"- {name}: {nfail}/{ntotal} NOK")
    else:
        lines.append("")
        lines.append("Sem falhas registadas no periodo.")

    if top_errors:
        lines.append("")
        lines.append("Top erros:")
        for err, qty in top_errors:
            lines.append(f"- ({qty}x) {err}")

    return "\n".join(lines)


def normalize_error(text: str) -> str:
    msg = " ".join(text.strip().split())
    if not msg:
        return "erro_sem_detalhe"
    if len(msg) > 160:
        msg = msg[:157] + "..."
    return msg


def table_columns(engine, table_name: str) -> set[str]:
    sql = text(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"table_name": table_name}).mappings().all()
    return {str(r["COLUMN_NAME"]) for r in rows}


def safe_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", value or ""):
        raise ValueError(f"Nome de tabela invalido: {value!r}")
    return value


def time_expression(cols: set[str]) -> str:
    if "startDate" in cols and "LogDate" in cols:
        return "COALESCE(startDate, LogDate)"
    if "startDate" in cols:
        return "startDate"
    if "LogDate" in cols:
        return "LogDate"
    if "regDate" in cols:
        return "regDate"
    return ""


def pipeline_expression(cols: set[str]) -> str:
    if "pipelineId" in cols and "pipeline_id" in cols:
        return "COALESCE(NULLIF(pipelineId, ''), NULLIF(pipeline_id, ''), scriptName, 'pipeline-sem-nome')"
    if "pipelineId" in cols:
        return "COALESCE(NULLIF(pipelineId, ''), scriptName, 'pipeline-sem-nome')"
    if "pipeline_id" in cols:
        return "COALESCE(NULLIF(pipeline_id, ''), scriptName, 'pipeline-sem-nome')"
    return "COALESCE(scriptName, 'pipeline-sem-nome')"


if __name__ == "__main__":
    raise SystemExit(main())

