"""Digest diário Slack (08:30) com falhas em aberto até resolução."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import store
from .helpers import env_flag
from .slack_alerts import get_slack_notifier, with_channel_mention

logger = logging.getLogger("overseer.slack_digest")

DIGEST_TZ = ZoneInfo("Europe/Lisbon")


def digest_enabled() -> bool:
    raw = os.getenv("OVERSEER_SLACK_DIGEST_ENABLED", "").strip().lower()
    if raw:
        return env_flag("OVERSEER_SLACK_DIGEST_ENABLED")
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


def _failure_error_message(last_run_id: str | None) -> str:
    if not last_run_id:
        return ""
    run = store.get_run(last_run_id) or {}
    err = str(run.get("error_message") or "").strip()
    if len(err) > 80:
        return err[:77] + "..."
    return err


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
    schedule_label = f"{digest_hour():02d}:{digest_minute():02d}"

    lines = [
        f":bar_chart: *Overseer — digest diário* ({now.strftime('%Y-%m-%d %H:%M')} Europe/Lisbon)",
        f"_Agendamento fixo: {schedule_label} todos os dias._",
        f"*Pipelines activos:* {len(active)}",
        f"*Runs (24h):* {total} · ok {ok} · failed {failed_24h} · warning {warning} · running {running}",
        f"*Taxa de sucesso (24h):* {success_rate}%",
    ]

    if unresolved:
        lines.append(f"*Falhas em aberto ({len(unresolved)}) — ainda não resolvidas:*")
        for row in unresolved[:12]:
            pid = row.get("pipeline_id") or "-"
            name = row.get("name") or pid
            host = row.get("host_id") or "-"
            since = row.get("last_started_at") or row.get("last_ended_at") or "?"
            err = _failure_error_message(row.get("last_run_id"))
            suffix = f" — {err}" if err else ""
            lines.append(f"• `{name}` (`{pid}`) @ `{host}` — desde {since}{suffix}")
        lines.append("_Estas falhas serão repetidas neste digest até a próxima run OK._")
    else:
        lines.append("_Sem falhas em aberto — todos os pipelines com última run não-failed._")

    if stale:
        lines.append(f"*Pipelines stale ({len(stale)}) — sem run dentro da janela esperada:*")
        for row in stale[:12]:
            pid = row.get("pipeline_id") or "-"
            name = row.get("name") or pid
            host = row.get("host_id") or "-"
            last_run = row.get("last_started_at") or "sem run"
            stale_hours = row.get("stale_hours")
            hours_label = f"{stale_hours}h" if stale_hours is not None else "sem histórico"
            schedule = row.get("schedule") or "manual"
            lines.append(
                f"• `{name}` (`{pid}`) @ `{host}` — última run {last_run} · {hours_label} · schedule `{schedule}`"
            )
    else:
        lines.append("_Sem pipelines stale._")

    recent_failures = [row for row in runs if row.get("status") == "failed"]
    if recent_failures and not unresolved:
        lines.append("*Falhas nas últimas 24h (já resolvidas):*")
        for row in sorted(recent_failures, key=lambda r: str(r.get("started_at") or ""), reverse=True)[:5]:
            pid = row.get("pipeline_id") or "-"
            host = row.get("host_id") or row.get("hostname") or "-"
            lines.append(f"• `{pid}` @ `{host}`")

    return with_channel_mention("\n".join(lines))


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
