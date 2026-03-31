"""
Template main.py — ponto de partida para novos pipelines Overseer.

Demonstra a utilização do overseer_sdk (RuntimeContext, LoggerManager,
SSHTunnelManager, SlackNotifier, DatabaseManagerBase) e a emissão de
eventos Lineage para o orquestrador.

Copiar para ``pipelines/<SEU_PIPELINE>/src/main.py`` e adaptar.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── SDK imports ──────────────────────────────────────────────────────
from overseer_sdk.runtime_context import runtime_ctx
from overseer_sdk.logger import get_log_manager, get_logger
from overseer_sdk.ssh_tunnel import SSHTunnelManager
from overseer_sdk.slack_notifier import SlackNotifier

# ── Lineage emitter (shared Overseer module) ────────────────────────
_OVERSEER_ROOT = Path(__file__).resolve().parents[3]
if str(_OVERSEER_ROOT) not in sys.path:
    sys.path.insert(0, str(_OVERSEER_ROOT))
try:
    from overseer_monitor.lineage_emitter import LineageEmitter

    _lineage_emit = LineageEmitter()
except ImportError:
    _lineage_emit = None

# ── Local imports (pipeline-specific) ────────────────────────────────
# from db_manager import MyDatabaseManager
# from my_reader import MyReader

PIPELINE_ID = "template_pipeline"
PIPELINE_NAME = "Template Pipeline"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Overseer runner for {PIPELINE_NAME}.",
        allow_abbrev=False,
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def run() -> int:
    args = build_parser().parse_args()

    log_manager = get_log_manager(system_log_name=f"{PIPELINE_ID}_system.log")
    logger = get_logger("main")

    logger.info("=" * 60)
    logger.info(f"🚀 {PIPELINE_NAME} — início")
    logger.info("=" * 60)
    logger.info(runtime_ctx.summary())

    emit = _lineage_emit
    start_time = datetime.now()
    status = "success"
    error_message: Optional[str] = None
    ssh_tunnel: Optional[SSHTunnelManager] = None
    # db_manager = None

    try:
        # 1. Carrega configurações
        if emit:
            emit.emit_start("config_loading", critical=True)
        # TODO: carregar config/ e secrets/
        if emit:
            emit.emit_end("config_loading", status="OK", message="Config loaded")

        # 2. Infraestrutura (SSH + BD)
        if emit:
            emit.emit_start("infrastructure", critical=True)

        # if runtime_ctx.db_is_local:
        #     db_host, db_port = "127.0.0.1", 3306
        # else:
        #     ssh_config = ...
        #     ssh_tunnel = SSHTunnelManager(...)
        #     ssh_tunnel.start()
        #     db_host, db_port = "localhost", ssh_tunnel.get_local_port()
        #
        # db_manager = MyDatabaseManager(host=db_host, port=db_port, ...)
        # db_manager.connect()
        # db_manager.ensure_tables()

        if emit:
            emit.emit_end("infrastructure", status="OK", message="Ready")

        # 3. Lógica principal
        if emit:
            emit.emit_start("processing", critical=False)
        # TODO: implementar lógica de ETL
        logger.info("✅ Processamento concluído (template)")
        if emit:
            emit.emit_end("processing", status="OK", message="Done")

        return 0

    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        logger.critical(f"❌ ERRO CRÍTICO: {exc}")
        raise

    finally:
        end_time = datetime.now()

        # Slack
        slack = SlackNotifier(config_path=Path("secrets/slack.json"))
        if slack.is_enabled:
            slack.notify_run(
                pipeline_name=PIPELINE_NAME,
                status=status,
                stats={},
                start_time=start_time,
                end_time=end_time,
                error_message=error_message,
            )

        # Cleanup
        # if db_manager:
        #     db_manager.disconnect()
        if ssh_tunnel:
            ssh_tunnel.stop()

        logger.info("🔒 Recursos libertados")


if __name__ == "__main__":
    raise SystemExit(run())
