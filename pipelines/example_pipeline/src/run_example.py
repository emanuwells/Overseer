"""
Example Pipeline — demonstra o padrão canónico Overseer.

Segue o contrato standard:
  - RuntimeContext  (portabilidade multi-máquina)
  - OverseerMonitor (registo standalone em pipeline_runs)
  - LineageEmitter  (módulos para lineage do orchestrator)
  - SlackNotifier   (notificações obrigatórias)
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# ── Path bootstrap ──────────────────────────────────────────────────────
_PIPELINE_DIR = Path(__file__).resolve().parent.parent
_OVERSEER_ROOT = _PIPELINE_DIR.parents[1]
if str(_OVERSEER_ROOT) not in sys.path:
    sys.path.insert(0, str(_OVERSEER_ROOT))

# ── SDK ─────────────────────────────────────────────────────────────────
from overseer_sdk.runtime_context import RuntimeContext  # noqa: E402
from overseer_sdk.logger import LoggerManager  # noqa: E402
from overseer_sdk.slack_notifier import SlackNotifier  # noqa: E402

runtime_ctx = RuntimeContext.detect()

# ── Monitor / Lineage ───────────────────────────────────────────────────
try:
    from overseer_monitor.lineage_emitter import LineageEmitter
    _lineage_emit = LineageEmitter()
except ImportError:
    _lineage_emit = None

try:
    from overseer_monitor import OverseerMonitor
except ImportError:
    OverseerMonitor = None  # type: ignore[misc,assignment]

# ── Constants ───────────────────────────────────────────────────────────
PIPELINE_ID = "example_pipeline"
PIPELINE_OWNER = "data.team"
PIPELINE_CRITICALITY = "medium"


def main() -> None:
    logger = LoggerManager(pipeline_id=PIPELINE_ID).get_logger("example")
    emit = _lineage_emit
    start_time = datetime.now()
    status = "success"
    error_message: str | None = None

    # ── Slack (obrigatório) ──────────────────────────────────────────
    slack_notifier: SlackNotifier | None = None
    slack_path = _PIPELINE_DIR / "secrets" / "slack.json"
    if slack_path.exists():
        slack_notifier = SlackNotifier(str(slack_path))
    else:
        logger.warning("slack.json não encontrado — Slack desativado")

    # ── OverseerMonitor (standalone) ─────────────────────────────────
    monitor = None
    if not runtime_ctx.orchestrator_managed and OverseerMonitor is not None:
        monitor = OverseerMonitor(
            script_name=PIPELINE_ID,
            table_name="Overseer.pipeline_runs",
            db_params=None,
        )

    logger.info("=" * 60)
    logger.info("EXAMPLE PIPELINE — INÍCIO")
    logger.info(f"Managed by orchestrator: {runtime_ctx.orchestrator_managed}")
    logger.info(f"RuntimeContext: {runtime_ctx.summary()}")
    logger.info("=" * 60)

    try:
        # ── 1. Trabalho simulado ─────────────────────────────────────
        if emit:
            emit.emit_start("example_work", critical=True)

        logger.info("A executar trabalho de exemplo...")
        time.sleep(1)  # simula processamento
        logger.info("Trabalho concluído com sucesso")

        if emit:
            emit.emit_end("example_work", status="OK", message="Done")

    except Exception as exc:
        logger.critical(f"ERRO CRÍTICO: {exc}")
        logger.debug(traceback.format_exc())
        status = "failed"
        error_message = str(exc)
        raise

    finally:
        end_time = datetime.now()

        # Monitor finish (standalone)
        if monitor is not None:
            try:
                monitor.finish(status, error_message, context={
                    "pipeline_id": PIPELINE_ID,
                    "trigger_type": os.environ.get("OVERSEER_TRIGGER_TYPE", "manual"),
                    "owner": PIPELINE_OWNER,
                    "criticality": PIPELINE_CRITICALITY,
                })
            except Exception as mon_exc:
                logger.warning(f"OverseerMonitor finish falhou: {mon_exc}")

        # Slack notification
        if emit:
            emit.emit_start("slack_notification", critical=False)
        if slack_notifier:
            slack_notifier.notify_run(
                pipeline_name="Example Pipeline",
                status=status,
                stats={"Duration (s)": f"{(end_time - start_time).total_seconds():.2f}"},
                start_time=start_time,
                end_time=end_time,
                error_message=error_message,
                hostname=runtime_ctx.hostname,
            )
        if emit:
            emit.emit_end("slack_notification", status="OK", message="Slack notified")

        logger.info("EXAMPLE PIPELINE — FIM")


if __name__ == "__main__":
    main()
