"""
Template main.py — ponto de partida canónico para novos pipelines Overseer.

Demonstra a utilização de TODOS os módulos standard:
  - overseer_sdk (RuntimeContext, LoggerManager, SSHTunnelManager, SlackNotifier)
  - overseer_monitor.lineage_emitter (LineageEmitter — eventos de módulo)
  - overseer_monitor (OverseerMonitor — registo em pipeline_runs para runs standalone)

Copiar para ``pipelines/<SEU_PIPELINE>/src/main.py`` e adaptar os TODOs.

Contrato obrigatório:
  1. Emitir LineageEmitter markers para CADA fase (config, infra, processamento, slack)
  2. Usar OverseerMonitor apenas quando standalone (não gerido pelo orchestrator)
  3. Notificar Slack no finally (obrigatório)
  4. Libertar SSH tunnel e DB no finally
  5. Usar logs_table = "Overseer.pipeline_runs" (canónico)
  6. Validar telemetria via Overseer API (GET /v1/monitoring/full) — não depender de JSON exportado
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── SDK imports (shared modules — always available) ──────────────────
_OVERSEER_ROOT = Path(__file__).resolve().parents[3]
if str(_OVERSEER_ROOT) not in sys.path:
    sys.path.insert(0, str(_OVERSEER_ROOT))

from overseer_sdk.runtime_context import RuntimeContext, runtime_ctx
from overseer_sdk.logger import get_log_manager, get_logger
from overseer_sdk.ssh_tunnel import SSHTunnelManager
from overseer_sdk.slack_notifier import SlackNotifier

# ── Lineage emitter (module-level markers → stdout → orchestrator) ──
try:
    from overseer_monitor.lineage_emitter import LineageEmitter
    _lineage_emit = LineageEmitter()
except ImportError:
    _lineage_emit = None

# ── OverseerMonitor (registo em pipeline_runs em modo standalone) ────
try:
    from overseer_monitor import OverseerMonitor
except ImportError:
    OverseerMonitor = None  # type: ignore[misc,assignment]

# ── Local imports (pipeline-specific) ────────────────────────────────
# from db_manager import MyDatabaseManager

# ── Constants ────────────────────────────────────────────────────────
PIPELINE_ID = "template_pipeline"       # TODO: alterar
PIPELINE_NAME = "Template Pipeline"     # TODO: alterar
MAX_ERROR_LENGTH = int(os.getenv("PERF_ERROR_MAX_LEN", "65000"))


class PipelineOrchestrator:
    """
    Orquestrador standard de pipeline Overseer.

    O padrão é sempre o mesmo:
      1. Carregar configs (monitoring.json, mappings, secrets)
      2. Setup infra (SSH tunnel + BD)
      3. Lógica de negócio (ETL, scraping, sync, etc.)
      4. Notificar Slack (obrigatório)
      5. Cleanup (BD, SSH, logs)
    """

    def __init__(
        self,
        config_dir: Path = Path("config"),
        secrets_dir: Path = Path("secrets"),
    ):
        self.logger = get_logger("orchestrator")
        self.config_dir = config_dir
        self.secrets_dir = secrets_dir

        # Configs
        self.monitoring_config: Dict[str, Any] = {}
        self.db_config: Dict[str, Any] = {}
        # TODO: adicionar mais configs conforme pipeline (mappings, etc.)

        # Modules
        self.ssh_tunnel: Optional[SSHTunnelManager] = None
        # self.db_manager: Optional[MyDatabaseManager] = None
        self.slack_notifier: Optional[SlackNotifier] = None
        self.error_events: List[Dict[str, str]] = []

        # Stats (adaptar por pipeline)
        self.stats: Dict[str, Any] = {
            "records_processed": 0,
            "records_failed": 0,
            "warning_count": 0,
        }

    # ------------------------------------------------------------------
    # Configuration loading
    # ------------------------------------------------------------------

    def load_config(self) -> None:
        """Carrega todas as configurações necessárias."""
        self.logger.info("A carregar configurações...")

        # Monitoring config
        monitoring_file = self.config_dir / "monitoring.json"
        monitoring_defaults = {
            "logs_table": "Overseer.pipeline_runs",
            "script_name": PIPELINE_ID,
            "frontend_base_url": "http://baze2.cm-maia.pt/MAIATRON/apps/overseer/",
        }
        if monitoring_file.exists():
            with open(monitoring_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                monitoring_defaults.update(loaded)
            self.logger.info(f"Config monitorização carregada de {monitoring_file}")
        else:
            self.logger.info("Config monitorização não encontrada; a usar defaults")
        self.monitoring_config = monitoring_defaults

        # DB credentials
        db_config_file = self.secrets_dir / "database.json"
        if not db_config_file.exists():
            raise FileNotFoundError(f"Credenciais de BD não encontradas: {db_config_file}")
        with open(db_config_file, "r", encoding="utf-8") as f:
            self.db_config = json.load(f)
        self.logger.info("Credenciais de BD carregadas")

        # Slack notifier (obrigatório)
        slack_file = self.secrets_dir / "slack.json"
        self.slack_notifier = SlackNotifier(config_path=slack_file)

        # TODO: carregar mais configs (mappings.json, etc.)

    # ------------------------------------------------------------------
    # Infrastructure setup
    # ------------------------------------------------------------------

    def setup_infrastructure(self) -> None:
        """Configura SSH tunnel (se necessário) e DB."""
        ssh_conf = self.db_config.get("ssh")
        db_conf = self.db_config.get("database", self.db_config)

        if ssh_conf and not runtime_ctx.db_is_local:
            self.logger.info("BD remota detetada — a estabelecer SSH tunnel...")
            self.ssh_tunnel = SSHTunnelManager(
                ssh_host=ssh_conf["host"],
                ssh_port=int(ssh_conf.get("port", 22)),
                ssh_user=ssh_conf["user"],
                ssh_key=str(self.secrets_dir / ssh_conf.get("key_filename", "ssh_key")),
                remote_host=ssh_conf.get("remote_bind_host", "localhost"),
                remote_port=int(ssh_conf.get("remote_bind_port", 3306)),
            )
            self.ssh_tunnel.start()
            db_host = "127.0.0.1"
            db_port = self.ssh_tunnel.get_local_port()
            self.logger.info(f"Túnel SSH ativo na porta {db_port}")
        else:
            self.logger.info("BD local — conexão directa")
            db_host = db_conf.get("host", "localhost")
            db_port = int(db_conf.get("port", 3306))

        # TODO: criar e conectar DB manager
        # self.db_manager = MyDatabaseManager(
        #     host=db_host, port=db_port,
        #     user=db_conf["user"], password=db_conf["password"],
        #     database=db_conf.get("database", "MAIATRON"),
        # )
        # self.db_manager.connect()
        # self.db_manager.ensure_tables()
        self.logger.info("Infraestrutura pronta")

    # ------------------------------------------------------------------
    # Error tracking
    # ------------------------------------------------------------------

    def add_error_event(self, category: str, context: str, message: str) -> None:
        if len(self.error_events) < 20:
            self.error_events.append(
                {"category": category, "context": context, "message": message}
            )

    def _compose_error_log(self, critical_message: Optional[str]) -> Optional[str]:
        entries: List[str] = []
        if critical_message:
            entries.append(f"CRITICAL: {critical_message}")
        for idx, event in enumerate(self.error_events, start=1):
            entries.append(
                f"{idx:02d}. {event['category']} | {event['context']} -> {event['message']}"
            )
        blob = "\n".join(entries).strip()
        if blob and len(blob) > MAX_ERROR_LENGTH:
            blob = blob[: MAX_ERROR_LENGTH - 3] + "..."
        return blob or None

    # ------------------------------------------------------------------
    # Heartbeat (log periódico de estado)
    # ------------------------------------------------------------------

    def emit_heartbeat(self, stage: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = (
            f"[heartbeat] stage={stage} ts={stamp} "
            f"processed={self.stats['records_processed']} "
            f"failed={self.stats['records_failed']} "
            f"warnings={self.stats['warning_count']}"
        )
        self.logger.info(summary)

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Executa o pipeline completo."""
        start_time = datetime.now()
        end_time: Optional[datetime] = None
        status = "success"
        error_message: Optional[str] = None
        self.error_events = []

        log_manager = get_log_manager(system_log_name=f"{PIPELINE_ID}_system.log")
        operation_log = log_manager.create_operation_log("run")

        # -- OverseerMonitor: só em modo standalone (sem orchestrator) --
        monitor = None
        if not runtime_ctx.orchestrator_managed and OverseerMonitor is not None:
            monitor = OverseerMonitor(
                script_name=PIPELINE_ID,
                table_name="Overseer.pipeline_runs",
                db_params=None,  # será preenchido após load_config
            )

        self.logger.info("=" * 80)
        self.logger.info(f"🚀 {PIPELINE_NAME} — início")
        self.logger.info("=" * 80)
        self.logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Managed by orchestrator: {runtime_ctx.orchestrator_managed}")
        self.logger.info(runtime_ctx.summary())
        self.logger.info(f"Log: {operation_log}")
        self.emit_heartbeat("startup")

        emit = _lineage_emit

        try:
            # ── 1. Configurações ─────────────────────────────────────
            if emit:
                emit.emit_start("config_loading", critical=True)
            self.load_config()

            # Atualizar monitor com DB params reais (modo standalone)
            if monitor:
                db_conf = self.db_config.get("database", self.db_config)
                monitor.set_db_params({
                    "host": db_conf.get("host", "localhost"),
                    "port": int(db_conf.get("port", 3306)),
                    "user": db_conf.get("user"),
                    "password": db_conf.get("password"),
                    "database": db_conf.get("database", "Overseer"),
                    "charset": db_conf.get("charset", "utf8mb4"),
                })
                monitor.start()

            if emit:
                emit.emit_end("config_loading", status="OK", message="Config loaded")

            # ── 2. Infraestrutura (SSH + BD) ─────────────────────────
            if emit:
                emit.emit_start("infrastructure", critical=True)
            self.setup_infrastructure()
            if emit:
                tunnel_msg = (
                    f"SSH tunnel active on port {self.ssh_tunnel.get_local_port()}"
                    if self.ssh_tunnel
                    else "Direct connection (db_is_local)"
                )
                emit.emit_end("infrastructure", status="OK", message=tunnel_msg)

            # ── 3. Lógica principal ──────────────────────────────────
            if emit:
                emit.emit_start("processing", critical=True)

            # TODO: implementar a lógica de negócio do pipeline aqui
            # Exemplo:
            # results = self.process_data()
            # self.stats["records_processed"] = results["ok"]
            # self.stats["records_failed"] = results["failed"]

            self.logger.info("✅ Processamento concluído")
            self.emit_heartbeat("processing_done")

            if emit:
                emit.emit_end(
                    "processing",
                    status="OK",
                    message=f"Processed={self.stats['records_processed']}, Failed={self.stats['records_failed']}",
                )

            # Determina status final
            if self.stats["records_failed"] > 0 or self.error_events:
                status = "warning"

        except Exception as exc:
            status = "failed"
            error_message = str(exc)
            self.logger.critical(f"❌ ERRO CRÍTICO: {exc}")
            self.logger.debug(traceback.format_exc())
            self.add_error_event("critical", "pipeline_run", str(exc))
            raise

        finally:
            end_time = datetime.now()
            self.emit_heartbeat("finalize")

            # ── Slack (obrigatório) ──────────────────────────────────
            if emit:
                emit.emit_start("slack_notification", critical=False)
            if self.slack_notifier and self.slack_notifier.is_enabled:
                try:
                    self.slack_notifier.notify_run(
                        pipeline_name=PIPELINE_NAME,
                        status=status,
                        stats=self.stats,
                        start_time=start_time,
                        end_time=end_time,
                        error_message=error_message,
                        error_events=self.error_events,
                        hostname=runtime_ctx.hostname,
                    )
                except Exception as slack_exc:
                    self.logger.warning(f"Slack notification failed: {slack_exc}")
            if emit:
                emit.emit_end("slack_notification", status="OK", message="Slack notified")

            # ── OverseerMonitor finish (modo standalone) ─────────────
            if monitor:
                composed_error = self._compose_error_log(error_message)
                monitor.finish(
                    status=status,
                    error_message=composed_error,
                    context={
                        "pipeline_id": PIPELINE_ID,
                        "trigger_type": os.getenv("P_TRIGGER_TYPE", "manual"),
                        "owner": self.monitoring_config.get("owner", "unknown"),
                        "criticality": self.monitoring_config.get("criticality", "medium"),
                    },
                )

            # ── Cleanup ──────────────────────────────────────────────
            # if self.db_manager:
            #     self.db_manager.disconnect()
            if self.ssh_tunnel:
                self.ssh_tunnel.stop()

            self.logger.info("🔒 Recursos libertados")


def main() -> int:
    """Entry point canónico."""
    orchestrator = PipelineOrchestrator()
    try:
        orchestrator.run()
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
