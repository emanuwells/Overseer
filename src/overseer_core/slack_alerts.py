"""Central Slack notifications for Overseer API (failures, resolution, @channel)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from overseer_sdk.slack_notifier import SlackNotifier

from . import deployment_health, store
from .helpers import env_flag
from .repo_paths import repo_root

logger = logging.getLogger("overseer.slack")


def mention_channel_enabled() -> bool:
    return env_flag("OVERSEER_SLACK_MENTION_CHANNEL", default=True)


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
    template = (os.getenv("OVERSEER_MAIATRON_RUN_URL") or "").strip()
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


def _send_slack_alert(run: dict[str, Any], lines: list[str], *, label: str) -> bool:
    """Envia alerta Slack com boilerplate partilhado (notifier + run URL + @channel)."""
    notifier = get_slack_notifier()
    if not notifier.is_enabled:
        logger.info("Slack disabled; skip %s alert for %s", label, run.get("run_id"))
        return False

    run_url = _run_url(run)
    if run_url:
        lines.append(f"*Run:* <{run_url}|Abrir no MAIATRON (#{_run_row_id(run)})>")
    elif label == "failed-run":
        lines.append(f"*Run ID:* `{run.get('run_id')}`")

    text = with_channel_mention("\n".join(lines))
    try:
        return bool(notifier.send_message(text))
    except Exception as exc:
        logger.error("Failed to send Slack %s alert: %s", label, exc)
        return False


def notify_failed_run(run: dict[str, Any]) -> bool:
    """Alerta imediato quando uma run falha. Inclui @channel."""
    pipeline_id = str(run.get("pipeline_id") or "-")
    pipeline_name = str(run.get("pipeline_name") or pipeline_id)
    error = str(run.get("error_message") or "").strip()
    if len(error) > 220:
        error = error[:217] + "..."

    lines = [
        ":x: *Pipeline FAILED* — alerta imediato",
        f"*Pipeline:* `{pipeline_name}` (`{pipeline_id}`)",
        f"*Host:* `{_host_label(run)}`",
        f"*Duração:* `{run.get('duration_sec') or '-'}s`",
    ]
    if error:
        lines.append(f"*Erro:* {error}")
    lines.append("_Será relembrado no digest diário (08:30) até ficar resolvido._")
    return _send_slack_alert(run, lines, label="failed-run")


def notify_resolved_run(run: dict[str, Any], failed_run: dict[str, Any] | None = None) -> bool:
    """Alerta imediato quando uma falha fica resolvida (run ok após failed)."""
    pipeline_id = str(run.get("pipeline_id") or "-")
    pipeline_name = str(run.get("pipeline_name") or pipeline_id)
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
    return _send_slack_alert(run, lines, label="resolved")
