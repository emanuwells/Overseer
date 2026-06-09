"""Central Slack notifications for Overseer API (pipeline failures)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from overseer_sdk.slack_notifier import SlackNotifier

from . import monitoring_export, store

logger = logging.getLogger("overseer.slack")

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _notifier() -> SlackNotifier:
    webhook = (os.getenv("OVERSEER_SLACK_WEBHOOK_URL") or "").strip()
    channel = (os.getenv("OVERSEER_SLACK_CHANNEL") or "#overseer").strip()
    if webhook:
        return SlackNotifier(config={"webhook_url": webhook, "channel": channel})
    secret_path = Path(os.getenv("OVERSEER_SLACK_CONFIG") or _REPO_ROOT / "secrets" / "slack.json")
    notifier = SlackNotifier(config_path=secret_path)
    if channel and not notifier.channel:
        notifier.channel = channel
    return notifier


def _run_row_id(run: dict[str, Any]) -> int:
    run_id = str(run.get("run_id") or "")
    return monitoring_export._run_row_id(run_id, 0)


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


def notify_failed_run(run: dict[str, Any]) -> bool:
    """Send a single Slack message for a failed pipeline run. Returns True if sent."""
    notifier = _notifier()
    if not notifier.is_enabled:
        logger.info("Slack disabled; skip failed-run alert for %s", run.get("run_id"))
        return False

    pipeline_id = str(run.get("pipeline_id") or "-")
    pipeline_name = str(run.get("pipeline_name") or pipeline_id)
    error = str(run.get("error_message") or "").strip()
    if len(error) > 220:
        error = error[:217] + "..."

    lines = [
        f":x: *Pipeline FAILED* — {pipeline_name}",
        f"*Pipeline:* `{pipeline_id}`",
        f"*Host:* `{run.get('hostname') or run.get('host_id') or '-'}`",
        f"*Duração:* `{run.get('duration_sec') or '-'}s`",
    ]
    if error:
        lines.append(f"*Erro:* {error}")

    run_url = _run_url(run)
    if run_url:
        lines.append(f"*Run:* <{run_url}|Abrir no MAIATRON (#{_run_row_id(run)})>")
    else:
        lines.append(f"*Run ID:* `{run.get('run_id')}`")

    text = "\n".join(lines)
    try:
        return bool(notifier.send_message(text))
    except Exception as exc:
        logger.error("Failed to send Slack alert: %s", exc)
        return False
