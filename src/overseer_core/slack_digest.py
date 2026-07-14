"""Resumo operacional diário enviado para Slack."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import store
from .slack_alerts import get_slack_notifier, with_channel_mention

logger = logging.getLogger("overseer.slack_digest")

DIGEST_TZ = ZoneInfo("Europe/Lisbon")


def digest_enabled() -> bool:
    flag = os.getenv("OVERSEER_SLACK_DIGEST_ENABLED", "").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return False
    if flag in {"1", "true", "yes", "on"}:
        return True
    return get_slack_notifier().is_enabled


def digest_hour() -> int:
    try:
        return max(0, min(23, int(os.getenv("OVERSEER_SLACK_DIGEST_HOUR", "8"))))
    except ValueError:
        return 8


def digest_minute() -> int:
    try:
        return max(0, min(59, int(os.getenv("OVERSEER_SLACK_DIGEST_MINUTE", "30"))))
    except ValueError:
        return 30


def next_digest_at(now: datetime | None = None) -> datetime:
    """Próximo envio agendado em Europe/Lisbon (default 08:30)."""
    current = now or datetime.now(DIGEST_TZ)
    target = current.replace(
        hour=digest_hour(),
        minute=digest_minute(),
        second=0,
        microsecond=0,
    )
    if current >= target:
        target += timedelta(days=1)
    return target


def _fmt_num(value: Any, decimals: int = 1) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num.is_integer():
        return str(int(num))
    return f"{num:.{decimals}f}".rstrip("0").rstrip(".")


def runs_last_24h() -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
    recent: list[dict[str, Any]] = []
    for run in store.list_runs(limit=2000):
        started = store.parse_dt(run.get("started_at"))
        if started and started >= cutoff:
            recent.append(run)
    return recent


def unresolved_deployments() -> list[dict[str, Any]]:
    """Deployments cuja última run ainda está em failed (não resolvido)."""
    open_rows = [
        row
        for row in store.list_pipelines()
        if row.get("active", True) and str(row.get("last_status") or "").lower() == "failed"
    ]
    open_rows.sort(key=lambda row: str(row.get("last_started_at") or ""))
    return open_rows


def stale_deployments() -> list[dict[str, Any]]:
    """Deployments activos sem run dentro da janela esperada pelo schedule."""
    stale_rows = [
        row
        for row in store.list_pipelines()
        if row.get("active", True) and row.get("is_stale")
    ]
    stale_rows.sort(key=lambda row: int(row.get("stale_hours") or 0), reverse=True)
    return stale_rows


def _deployment_key(pipeline_id: str, host_id: str) -> str:
    return f"{pipeline_id}::{host_id or '-'}"


def aggregate_runs_by_deployment(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for run in runs:
        pid = str(run.get("pipeline_id") or "-")
        host = str(run.get("host_id") or run.get("hostname") or "-")
        key = _deployment_key(pid, host)
        if key not in buckets:
            from .pipeline_names import resolve_display_name

            buckets[key] = {
                "pipeline_id": pid,
                "host_id": host,
                "name": resolve_display_name(
                    pid,
                    host,
                    str(run.get("pipeline_name") or pid),
                    store.catalog_name_index(),
                ),
                "total": 0,
                "ok": 0,
                "failed": 0,
                "warning": 0,
                "running": 0,
            }
        bucket = buckets[key]
        bucket["total"] += 1
        status = str(run.get("status") or "").lower()
        if status == "ok":
            bucket["ok"] += 1
        elif status == "failed":
            bucket["failed"] += 1
        elif status == "warning":
            bucket["warning"] += 1
        elif status == "running":
            bucket["running"] += 1
    return sorted(buckets.values(), key=lambda row: (-int(row["total"]), row["pipeline_id"], row["host_id"]))


def _run_status_label(bucket: dict[str, Any]) -> str:
    if int(bucket.get("failed") or 0) > 0:
        return f"failed `{bucket['failed']}`"
    if int(bucket.get("warning") or 0) > 0:
        return f"warning `{bucket['warning']}`"
    if int(bucket.get("running") or 0) > 0:
        return f"running `{bucket['running']}`"
    return "ok"


def _failure_error_message(last_run_id: str | None) -> str:
    if not last_run_id:
        return ""
    run = store.get_run(last_run_id) or {}
    err = str(run.get("error_message") or "").strip()
    if len(err) > 60:
        return err[:57] + "..."
    return err


def _digest_status_icon(unresolved: list[dict[str, Any]], stale: list[dict[str, Any]], failed_24h: int) -> tuple[str, str]:
    if unresolved:
        return ":rotating_light:", f"{len(unresolved)} falha(s) em aberto"
    if failed_24h > 0:
        return ":warning:", f"{failed_24h} falha(s) nas 24h (já resolvidas)"
    if stale:
        return ":warning:", f"{len(stale)} pipeline(s) stale"
    return ":white_check_mark:", "Operação estável nas últimas 24h"


def build_digest_text() -> str:
    pipelines = store.list_pipelines()
    active = [row for row in pipelines if row.get("active", True)]
    runs = runs_last_24h()
    ok = sum(1 for row in runs if row.get("status") == "ok")
    failed_24h = sum(1 for row in runs if row.get("status") == "failed")
    warning = sum(1 for row in runs if row.get("status") == "warning")
    running = sum(1 for row in runs if row.get("status") == "running")
    total = len(runs)
    success_rate = round((ok / total) * 100, 1) if total else 100.0

    unresolved = unresolved_deployments()
    stale = stale_deployments()
    now = datetime.now(DIGEST_TZ)
    period_label = now.strftime("%Y-%m-%d Europe/Lisbon")
    status_icon, status_line = _digest_status_icon(unresolved, stale, failed_24h)

    by_deployment = aggregate_runs_by_deployment(runs)
    ran_keys = {_deployment_key(row["pipeline_id"], row["host_id"]) for row in by_deployment}
    silent = [
        row
        for row in active
        if _deployment_key(str(row.get("pipeline_id") or ""), str(row.get("host_id") or "")) not in ran_keys
    ]

    lines = [
        f"{status_icon} *Overseer Daily Digest*",
        f"*Periodo:* `{period_label}`",
        f"*Resumo:* {status_line}",
        "",
        ":gear: *Pipelines*",
        (
            f"- Activos: `{len(active)}` | Com run 24h: `{len(by_deployment)}` | "
            f"Sem run 24h: `{len(silent)}`"
        ),
        (
            f"- Runs 24h: `{total}` | ok `{ok}` | failed `{failed_24h}` | "
            f"warning `{warning}` | running `{running}` | sucesso `{_fmt_num(success_rate)}%`"
        ),
    ]

    lines.extend(["", ":arrow_forward: *Runs por pipeline (24h)*"])
    if by_deployment:
        for row in by_deployment[:14]:
            label = row["name"] if row["name"] != row["pipeline_id"] else row["pipeline_id"]
            lines.append(
                f"- `{label}` @ `{row['host_id']}` — "
                f"`{row['total']}` run(s) · {_run_status_label(row)}"
            )
        if len(by_deployment) > 14:
            lines.append(f"- _… e mais {len(by_deployment) - 14} deployment(s)_")
    else:
        lines.append("- `nenhuma run nas últimas 24h`")

    if silent:
        silent_names = [
            f"`{row.get('name') or row.get('pipeline_id')}` @ `{row.get('host_id') or '-'}`"
            for row in silent[:6]
        ]
        lines.append(f"- Sem run 24h: {', '.join(silent_names)}")
        if len(silent) > 6:
            lines.append(f"  _… e mais {len(silent) - 6}_")

    lines.extend(["", ":rotating_light: *Falhas em aberto*"])
    if unresolved:
        for row in unresolved[:8]:
            pid = row.get("pipeline_id") or "-"
            name = row.get("name") or pid
            host = row.get("host_id") or "-"
            since = row.get("last_started_at") or row.get("last_ended_at") or "?"
            err = _failure_error_message(row.get("last_run_id"))
            err_suffix = f" — `{err}`" if err else ""
            lines.append(f"- `{name}` @ `{host}` — desde `{since}`{err_suffix}")
        if len(unresolved) > 8:
            lines.append(f"- _… e mais {len(unresolved) - 8}_")
    else:
        lines.append("- `nenhuma`")

    lines.extend(["", ":hourglass_flowing_sand: *Stale (fora de cadência)*"])
    if stale:
        for row in stale[:8]:
            pid = row.get("pipeline_id") or "-"
            name = row.get("name") or pid
            host = row.get("host_id") or "-"
            stale_hours = row.get("stale_hours")
            hours_label = f"{stale_hours}h" if stale_hours is not None else "?"
            schedule = row.get("schedule") or "manual"
            lines.append(
                f"- `{name}` @ `{host}` — `{hours_label}` · schedule `{schedule}`"
            )
        if len(stale) > 8:
            lines.append(f"- _… e mais {len(stale) - 8}_")
    else:
        lines.append("- `nenhum`")

    text = "\n".join(lines)
    # Um digest saudável é informativo e não deve notificar todo o canal.
    # Falhas abertas e deployments fora de cadência continuam acionáveis.
    return with_channel_mention(text) if unresolved or stale else text


def send_daily_digest() -> bool:
    if not digest_enabled():
        logger.info("Slack digest desactivado ou webhook ausente")
        return False
    notifier = get_slack_notifier()
    if not notifier.is_enabled:
        logger.info("Slack digest: webhook não configurado")
        return False
    text = build_digest_text()
    try:
        return bool(notifier.send_message(text))
    except Exception as exc:
        logger.error("Falha ao enviar digest Slack: %s", exc)
        return False
