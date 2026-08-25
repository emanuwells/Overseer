"""Central Slack notifications for Overseer API (failures, resolution, @channel)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from overseer_sdk.slack_notifier import SlackNotifier

from . import deployment_health, store
from .pipeline_names import resolve_display_name
from .repo_paths import repo_root

logger = logging.getLogger("overseer.slack")

FAILURE_ALERT_LIMIT = 3


def mention_channel_enabled() -> bool:
    flag = os.getenv("OVERSEER_SLACK_MENTION_CHANNEL", "true").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def with_channel_mention(text: str) -> str:
    if not mention_channel_enabled():
        return text
    if text.lstrip().startswith("<!channel>"):
        return text
    return f"<!channel> {text}"


def get_slack_notifier() -> SlackNotifier:
    webhook = (os.getenv("OVERSEER_SLACK_WEBHOOK_URL") or "").strip()
    channel = (os.getenv("OVERSEER_SLACK_CHANNEL") or "#overseer").strip()
    if webhook:
        return SlackNotifier(config={"webhook_url": webhook, "channel": channel})
    secret_path = Path(os.getenv("OVERSEER_SLACK_CONFIG") or repo_root() / "secrets" / "slack.json")
    notifier = SlackNotifier(config_path=secret_path)
    if channel and not notifier.channel:
        notifier.channel = channel
    return notifier


def _run_row_id(run: dict[str, Any]) -> int:
    run_id = str(run.get("run_id") or "")
    return deployment_health.run_row_id(run_id, 0)


def _run_url(run: dict[str, Any]) -> str | None:
    template = (os.getenv("OVERSEER_RUN_URL") or "").strip()
    if not template:
        return None
    row_id = _run_row_id(run)
    pipeline_id = store.logical_pipeline_id(str(run.get("pipeline_id") or ""))
    return (
        template.replace("{row_id}", str(row_id))
        .replace("{run_id}", str(run.get("run_id") or ""))
        .replace("{pipeline_id}", pipeline_id)
    )


def _host_label(run: dict[str, Any]) -> str:
    return str(run.get("hostname") or run.get("host_id") or "-")


def failure_alert_number(run: dict[str, Any]) -> int | None:
    """Próximo aviso do episódio de falha, ou ``None`` após atingir o limite."""
    pipeline_id = str(run.get("pipeline_id") or "")
    host_id = str(run.get("host_id") or "")
    current_run_id = str(run.get("run_id") or "")
    sent_alerts = 0
    for previous in store.list_runs(limit=1000, pipeline_id=pipeline_id, host_id=host_id):
        if str(previous.get("run_id") or "") == current_run_id:
            continue
        status = str(previous.get("status") or "").lower()
        if status in {"running", "queued"}:
            continue
        if status != "failed":
            break
        metadata = previous.get("metadata")
        if isinstance(metadata, dict) and metadata.get("slack_notified"):
            sent_alerts += 1
            if sent_alerts >= FAILURE_ALERT_LIMIT:
                return None
    return sent_alerts + 1


def notify_failed_run(run: dict[str, Any], *, alert_number: int = 1) -> bool:
    """Alerta imediato limitado por episódio de falha. Inclui @channel."""
    notifier = get_slack_notifier()
    if not notifier.is_enabled:
        logger.info("Slack disabled; skip failed-run alert for %s", run.get("run_id"))
        return False

    pipeline_id = str(run.get("pipeline_id") or "-")
    pipeline_name = resolve_display_name(
        pipeline_id,
        str(run.get("host_id") or ""),
        str(run.get("pipeline_name") or pipeline_id),
        store.catalog_name_index(),
    )
    error = str(run.get("error_message") or "").strip()
    if len(error) > 220:
        error = error[:217] + "..."

    lines = [
        f":x: *Pipeline FAILED* — aviso imediato {alert_number}/{FAILURE_ALERT_LIMIT}",
        f"*Pipeline:* `{pipeline_name}` (`{pipeline_id}`)",
        f"*Host:* `{_host_label(run)}`",
        f"*Duração:* `{run.get('duration_sec') or '-'}s`",
    ]
    if error:
        lines.append(f"*Erro:* {error}")
    if alert_number >= FAILURE_ALERT_LIMIT:
        lines.append(
            "_Este é o último aviso imediato. O pipeline passará para o digest diário "
            "(08:30) até ficar resolvido._"
        )

    run_url = _run_url(run)
    if run_url:
        lines.append(f"*Run:* <{run_url}|Abrir detalhe (#{_run_row_id(run)})>")
    else:
        lines.append(f"*Run ID:* `{run.get('run_id')}`")

    text = with_channel_mention("\n".join(lines))
    try:
        return bool(notifier.send_message(text))
    except Exception as exc:
        logger.error("Failed to send Slack alert: %s", exc)
        return False


def notify_resolved_run(run: dict[str, Any], failed_run: dict[str, Any] | None = None) -> bool:
    """Alerta imediato quando uma falha fica resolvida (run ok após failed)."""
    notifier = get_slack_notifier()
    if not notifier.is_enabled:
        logger.info("Slack disabled; skip resolved alert for %s", run.get("run_id"))
        return False

    pipeline_id = str(run.get("pipeline_id") or "-")
    pipeline_name = resolve_display_name(
        pipeline_id,
        str(run.get("host_id") or ""),
        str(run.get("pipeline_name") or pipeline_id),
        store.catalog_name_index(),
    )
    lines = [
        ":white_check_mark: *Pipeline RESOLVIDO* — alerta imediato",
        f"*Pipeline:* `{pipeline_name}` (`{pipeline_id}`)",
        f"*Host:* `{_host_label(run)}`",
        f"*Run OK:* `{run.get('run_id')}`",
    ]
    if failed_run:
        lines.append(f"*Falha anterior:* `{failed_run.get('run_id')}`")
        failed_at = failed_run.get("ended_at") or failed_run.get("started_at")
        if failed_at:
            lines.append(f"*Falhou em:* {failed_at}")

    run_url = _run_url(run)
    if run_url:
        lines.append(f"*Run:* <{run_url}|Abrir detalhe (#{_run_row_id(run)})>")

    text = with_channel_mention("\n".join(lines))
    try:
        return bool(notifier.send_message(text))
    except Exception as exc:
        logger.error("Failed to send Slack resolved alert: %s", exc)
        return False
