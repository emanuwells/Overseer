"""
Script Principal de Scraping Webapp Medidata → MariaDB
Versão: 3.0.0
Autor: Emanuel Ferreira (emanuel.ferreira@cm-maia.pt)

Orquestra todo o processo: scraping web, validação e persistência.
Usa ``overseer_sdk`` para módulos partilhados (logger, SSH, Slack, RuntimeContext).
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Overseer SDK imports (shared modules)
# ---------------------------------------------------------------------------
_OVERSEER_ROOT = Path(__file__).resolve().parents[3]
if str(_OVERSEER_ROOT) not in sys.path:
    sys.path.insert(0, str(_OVERSEER_ROOT))

from overseer_sdk.runtime_context import runtime_ctx
from overseer_sdk.logger import get_log_manager, get_logger
from overseer_sdk.ssh_tunnel import SSHTunnelManager
from overseer_sdk.slack_notifier import SlackNotifier
from overseer_sdk.validator import DataValidator

# Lineage emitter
try:
    from overseer_monitor.lineage_emitter import LineageEmitter
    _lineage_emit = LineageEmitter()
except ImportError:
    _lineage_emit = None

# ---------------------------------------------------------------------------
# Local pipeline modules
# ---------------------------------------------------------------------------
from db_manager import DatabaseManager
from scraper import MedidataScraper


DEFAULT_FRONTEND_URL = (
    os.getenv("OVERSEER_MONITOR_URL")
    or os.getenv("OVERSEER_FRONTEND_URL")
    or "http://baze2.cm-maia.pt/D4CMMaia/Bruin_Monitor/index.html"
)
DEFAULT_BASE_URL = "http://webapp.cm-maia.local/medidata/"
DEFAULT_LIST_URL = DEFAULT_BASE_URL + "listagem.aspx"
MAX_ERROR_MESSAGE_LENGTH = int(os.getenv("PERF_ERROR_MAX_LEN", "65000"))

PIPELINE_ID = "webapp_medidata"


class ScrapeOrchestrator:
    """
    Orquestrador principal do pipeline Webapp Medidata.

    Coordena todos os módulos:
      1. Carregar configs/mappings
      2. Estabelecer SSH tunnel (se necessário, detectado por RuntimeContext)
      3. Conectar à BD
      4. Descobrir indicadores na listagem do Medidata
      5. Fazer scrape de cada indicador (HTML table + JSON)
      6. Validar e persistir na BD (UPSERT com dedup por hash)
      7. Gerar resumo + notificar Slack
    """

    def __init__(
        self,
        config_dir: Path = Path("config"),
        secrets_dir: Path = Path("secrets"),
    ):
        self.logger = get_logger("orchestrator")
        self.config_dir = config_dir
        self.secrets_dir = secrets_dir

        # Configs loaded later
        self.mappings: Dict[str, Any] = {}
        self.db_config: Dict[str, Any] = {}
        self.monitoring_config: Dict[str, str] = {}

        # Modules
        self.ssh_tunnel: Optional[SSHTunnelManager] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.scraper: Optional[MedidataScraper] = None
        self.validator = DataValidator()
        self.slack_notifier = SlackNotifier(config_path=self.secrets_dir / "slack.json")
        self.error_events: List[Dict[str, str]] = []

        self.stats = {
            "source_indicators": 0,
            "scraped_indicators": 0,
            "scrape_failed": 0,
            "db_records_written": 0,
            "db_records_failed": 0,
            "warning_count": 0,
            "mapping_matches": 0,
            "mapping_misses": 0,
        }

    # ------------------------------------------------------------------
    # Heartbeat & error tracking
    # ------------------------------------------------------------------

    def emit_module_log_heartbeat(self, stage: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = (
            f"[heartbeat] stage={stage} ts={stamp} "
            f"scraped={self.stats['scraped_indicators']} "
            f"failed={self.stats['scrape_failed']} "
            f"db_ok={self.stats['db_records_written']} "
            f"db_err={self.stats['db_records_failed']}"
        )
        for name in ("main", "orchestrator", "db_manager", "scraper", "validator"):
            try:
                get_logger(name).info(summary)
            except Exception:
                continue

    def add_error_event(self, category: str, context: str, message: str) -> None:
        if len(self.error_events) >= 20:
            return
        self.error_events.append(
            {"category": category, "context": context, "message": message}
        )

    def _compose_error_log(
        self, critical_message: Optional[str], log_path: Optional[Path]
    ) -> Optional[str]:
        entries: List[str] = []
        if critical_message:
            entries.append(f"CRITICAL: {critical_message}")
        for idx, event in enumerate(self.error_events, start=1):
            cat = event.get("category", "erro")
            ctx = event.get("context", "")
            msg = event.get("message", "")
            entries.append(f"{idx:02d}. {cat} | {ctx} -> {msg}")

        base_summary = "\n".join(entries).strip() if entries else ""
        log_excerpt = ""
        if log_path and base_summary:
            try:
                raw = Path(log_path).read_text(encoding="utf-8", errors="replace").strip()
                if raw:
                    log_excerpt = raw
            except OSError:
                pass

        parts: List[str] = []
        if base_summary:
            parts.append("Resumo de erros")
            parts.append(base_summary)
        if log_excerpt:
            parts.append("")
            parts.append("=== LOG COMPLETO ===")
            parts.append(log_excerpt)

        blob = "\n".join(parts).strip()
        if blob and len(blob) > MAX_ERROR_MESSAGE_LENGTH:
            blob = blob[: MAX_ERROR_MESSAGE_LENGTH - 3] + "..."
        return blob or None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def load_config(self) -> None:
        self.logger.info("A carregar configurações...")

        # Mappings
        mappings_file = self.config_dir / "mappings.json"
        if not mappings_file.exists():
            raise FileNotFoundError(f"Ficheiro de mapeamentos não encontrado: {mappings_file}")
        with open(mappings_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.mappings = raw.get("series_config", raw)
        self.logger.info(f"Mapeamentos carregados ({len(self.mappings)} séries)")

        # DB credentials
        db_config_file = self.secrets_dir / "database.json"
        if not db_config_file.exists():
            raise FileNotFoundError(f"Credenciais de BD não encontradas: {db_config_file}")
        with open(db_config_file, "r", encoding="utf-8") as f:
            self.db_config = json.load(f)
        self.logger.info("Credenciais de BD carregadas")

        # Monitoring config (optional)
        monitoring_defaults = {
            "logs_table": "Overseer.pipeline_runs",
            "script_name": "Webapp_Medidata_Scraper",
            "frontend_base_url": DEFAULT_FRONTEND_URL,
        }
        monitoring_file = self.config_dir / "monitoring.json"
        if not monitoring_file.exists():
            alt = self.secrets_dir / "monitoring.json"
            monitoring_file = alt if alt.exists() else monitoring_file

        if monitoring_file.exists():
            with open(monitoring_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                monitoring_defaults.update(loaded)
            self.logger.info(f"Configuração de monitorização carregada de {monitoring_file}")
        else:
            self.logger.info("Config de monitorização não encontrada; a usar defaults.")

        self.monitoring_config = monitoring_defaults

    # ------------------------------------------------------------------
    # Infrastructure setup (auto-detect via RuntimeContext)
    # ------------------------------------------------------------------

    def setup_infrastructure(self) -> None:
        """
        Configura SSH tunnel + DB connection.

        Usa ``runtime_ctx.db_is_local`` para decidir:
        - Se ``True``: conecta directamente a localhost:3306
        - Se ``False``: cria SSH tunnel primeiro
        """
        db_conf = self.db_config["database"]

        if runtime_ctx.db_is_local:
            # Direct connection — running on the DB server
            self.logger.info(
                "RuntimeContext: DB é local (%s) — conexão directa sem SSH",
                runtime_ctx.hostname,
            )
            db_host = db_conf.get("host", "localhost")
            db_port = int(db_conf.get("port", 3306))
        elif "ssh" in self.db_config:
            # Remote — need SSH tunnel
            self.logger.info(
                "RuntimeContext: DB é remota — a estabelecer túnel SSH"
            )
            ssh_config = self.db_config["ssh"]
            self.ssh_tunnel = SSHTunnelManager(
                ssh_host=ssh_config["host"],
                ssh_port=ssh_config["port"],
                ssh_user=ssh_config["user"],
                ssh_key_path=str(self.secrets_dir / ssh_config["key_filename"]),
                remote_bind_host=ssh_config.get("remote_bind_host", "localhost"),
                remote_bind_port=ssh_config.get("remote_bind_port", 3306),
            )
            self.ssh_tunnel.start()
            self.logger.info(f"Túnel SSH ativo na porta {self.ssh_tunnel.get_local_port()}")
            db_host = "127.0.0.1"
            db_port = self.ssh_tunnel.get_local_port()
        else:
            # No SSH config — connect directly using configured host
            self.logger.info(
                "Sem config SSH — conexão directa para %s:%s",
                db_conf.get("host", "localhost"),
                db_conf.get("port", 3306),
            )
            db_host = db_conf.get("host", "localhost")
            db_port = int(db_conf.get("port", 3306))

        # Database connection
        self.db_manager = DatabaseManager(
            host=db_host,
            port=db_port,
            user=db_conf["user"],
            password=db_conf["password"],
            database=db_conf.get("database", "MAIATRON"),
        )
        self.db_manager.connect()
        self.db_manager.ensure_tables()
        self.logger.info("Conexão à BD estabelecida + tabelas verificadas")

    def setup_scraper(self) -> None:
        self.logger.info("A inicializar scraper...")
        self.scraper = MedidataScraper(self.mappings)
        self.logger.info("Scraper pronto")

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: C901
        start_time = datetime.now()
        end_time: Optional[datetime] = None
        status = "success"
        error_message: Optional[str] = None
        self.error_events = []
        run_id = str(uuid.uuid4())
        log_manager = get_log_manager()
        operation_log = log_manager.create_operation_log("scrape")

        self.logger.info("=" * 80)
        self.logger.info("INÍCIO DO SCRAPING WEBAPP MEDIDATA")
        self.logger.info("=" * 80)
        self.logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Run ID: {run_id}")
        self.logger.info(f"RuntimeContext: {runtime_ctx.summary()}")
        self.logger.info(f"Log desta operação: {operation_log}")
        self.emit_module_log_heartbeat("startup")

        emit = _lineage_emit  # may be None if import failed

        try:
            # ── 1. Carregar configurações ────────────────────────────
            if emit:
                emit.emit_start("config_loading", critical=True)
            self.load_config()
            if emit:
                emit.emit_end(
                    "config_loading",
                    status="OK",
                    message=f"Loaded {len(self.mappings)} mappings",
                )

            # ── 2. Infraestrutura (SSH + DB) ─────────────────────────
            if emit:
                emit.emit_start("ssh_tunnel", critical=True)
            if emit:
                emit.emit_start("db_connection", critical=True, parent_module_id="ssh_tunnel")
            self.setup_infrastructure()
            if emit:
                tunnel_msg = (
                    f"Tunnel active on port {self.ssh_tunnel.get_local_port()}"
                    if self.ssh_tunnel
                    else "Direct connection (db_is_local=True)"
                )
                emit.emit_end("ssh_tunnel", status="OK", message=tunnel_msg)
                emit.emit_end("db_connection", status="OK", message="Database connected + tables ensured")

            # ── 3. Inicializar scraper ───────────────────────────────
            if emit:
                emit.emit_start("scraper_init", critical=True)
            self.setup_scraper()
            if emit:
                emit.emit_end("scraper_init", status="OK", message="Scraper initialized")

            # ── 4. Descobrir indicadores ─────────────────────────────
            if emit:
                emit.emit_start("source_discovery", critical=True)

            base_url = self.db_config.get("scrape", {}).get("base_url", DEFAULT_BASE_URL)
            list_url = self.db_config.get("scrape", {}).get("list_url", DEFAULT_LIST_URL)
            list_file = self.db_config.get("scrape", {}).get("list_file", None)

            indicators = self.scraper.discover_sources(
                base_url=base_url, list_url=list_url, list_file=list_file,
            )
            self.stats["source_indicators"] = len(indicators)

            if not indicators:
                self.logger.warning("Nenhum indicador encontrado!")
                if emit:
                    emit.emit_end("source_discovery", status="OK", message="No indicators found")
                return

            self.logger.info(f"Descobertos {len(indicators)} indicadores")
            if emit:
                emit.emit_end("source_discovery", status="OK", message=f"Found {len(indicators)} indicators")

            # Register run in DB
            self.db_manager.start_run(run_id, list_url)

            # ── 5. Scrape de todos os indicadores ────────────────────
            if emit:
                emit.emit_start("indicator_scraping", critical=False)

            scraped_results, scrape_warnings = self.scraper.scrape_all(indicators)
            self.stats["scraped_indicators"] = len(
                [r for r in scraped_results if not r.get("has_issue")]
            )
            self.stats["scrape_failed"] = len(
                [r for r in scraped_results if r.get("has_issue")]
            )

            for result in scraped_results:
                if result.get("has_issue"):
                    self.add_error_event(
                        category="scrape",
                        context=f"indicator={result.get('id', '?')}",
                        message="scrape had issues",
                    )

            self.logger.info(
                f"Scraping concluído: {self.stats['scraped_indicators']} OK, "
                f"{self.stats['scrape_failed']} com erro"
            )
            if emit:
                emit.emit_end(
                    "indicator_scraping",
                    status="NOK" if self.stats["scrape_failed"] > 0 else "OK",
                    message=f"Scraped {self.stats['scraped_indicators']}, failed {self.stats['scrape_failed']}",
                )

            self.emit_module_log_heartbeat("scraping_done")

            # ── 6. Mapping precheck ──────────────────────────────────
            if emit:
                emit.emit_start("mapping_precheck", critical=False)

            precheck = self.scraper.run_mapping_precheck(indicators)
            self.stats["mapping_matches"] = precheck.get("mapped", 0)
            self.stats["mapping_misses"] = precheck.get("unmapped", 0)

            if precheck.get("unmapped", 0) > 0:
                self.stats["warning_count"] += 1
                self.logger.warning(f"Mapping precheck: {precheck.get('unmapped', 0)} indicadores sem mapping")

            if emit:
                emit.emit_end(
                    "mapping_precheck",
                    status="OK",
                    message=f"Mapped={precheck.get('mapped', 0)}, Unmapped={precheck.get('unmapped', 0)}",
                )

            # ── 7. Persistir na BD ───────────────────────────────────
            if emit:
                emit.emit_start("db_persistence", critical=False)

            for result in scraped_results:
                if result.get("has_issue") and not result.get("data") and not result.get("json_data"):
                    continue

                indicator_id = result.get("id", "unknown")
                area = result.get("area")
                title = result.get("title")
                application = result.get("application")

                # Persist table data
                for row in result.get("data", []):
                    self._persist_single_record(
                        run_id=run_id,
                        indicator_id=indicator_id,
                        area=area,
                        title=title,
                        application=application,
                        source_kind="table",
                        source_url_table=result.get("url_table"),
                        source_url_json=None,
                        payload=row,
                    )

                # Persist JSON data
                for row in result.get("json_data", []):
                    self._persist_single_record(
                        run_id=run_id,
                        indicator_id=indicator_id,
                        area=area,
                        title=title,
                        application=application,
                        source_kind="json",
                        source_url_table=None,
                        source_url_json=result.get("url_json"),
                        payload=row,
                    )

            db_stats = self.db_manager.get_stats()
            self.stats["db_records_written"] = db_stats["records_written"]
            self.stats["db_records_failed"] = db_stats["records_failed"]

            self.logger.info(
                f"Persistência: {self.stats['db_records_written']} escritos, "
                f"{self.stats['db_records_failed']} falhados"
            )
            if emit:
                emit.emit_end(
                    "db_persistence",
                    status="OK" if self.stats["db_records_failed"] == 0 else "NOK",
                    message=f"Written={self.stats['db_records_written']}, Failed={self.stats['db_records_failed']}",
                )

            # ── 8. Resumo ────────────────────────────────────────────
            if emit:
                emit.emit_start("run_summary", critical=False)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if self.stats["scrape_failed"] > 0 or self.stats["db_records_failed"] > 0:
                status = "warning"
                self.stats["warning_count"] += 1

            # Finalize run in DB
            self.db_manager.finish_run(
                run_id=run_id,
                status=status,
                total_indicators=self.stats["source_indicators"],
                error_message=error_message,
            )

            self.logger.info("=" * 80)
            self.logger.info("SCRAPING CONCLUÍDO")
            self.logger.info("=" * 80)

            summary = {
                "Duração (s)": f"{duration:.2f}",
                "Indicadores descobertos": self.stats["source_indicators"],
                "Indicadores scrapeados": self.stats["scraped_indicators"],
                "Indicadores com erro": self.stats["scrape_failed"],
                "Registos BD escritos": self.stats["db_records_written"],
                "Registos BD falhados": self.stats["db_records_failed"],
                "Mapping matches": self.stats["mapping_matches"],
                "Mapping misses": self.stats["mapping_misses"],
                "Warnings": self.stats["warning_count"],
                "Run ID": run_id,
            }

            log_manager.log_operation_summary("orchestrator", summary)
            if emit:
                emit.emit_end(
                    "run_summary",
                    status="OK",
                    message=f"Duration={duration:.2f}s run_id={run_id}",
                )

        except Exception as exc:
            self.logger.critical(f"ERRO CRITICO: {exc}")
            self.logger.debug(traceback.format_exc())
            status = "failed"
            error_message = str(exc)
            self.add_error_event(category="critical", context="orchestrator_run", message=str(exc))

            if self.db_manager:
                try:
                    self.db_manager.finish_run(
                        run_id=run_id,
                        status="failed",
                        total_indicators=self.stats.get("source_indicators", 0),
                        error_message=error_message,
                    )
                except Exception:
                    pass

            raise

        finally:
            final_end_time = end_time or datetime.now()
            self.emit_module_log_heartbeat("finalize")

            # Slack notification
            if emit:
                emit.emit_start("slack_notification", critical=False)
            if self.slack_notifier:
                self.slack_notifier.notify_run(
                    pipeline_name="Webapp Medidata Scraper",
                    status=status,
                    stats={
                        "Indicadores scrapeados": self.stats["scraped_indicators"],
                        "DB registos escritos": self.stats["db_records_written"],
                        "DB registos falhados": self.stats["db_records_failed"],
                        "Warnings": self.stats["warning_count"],
                    },
                    start_time=start_time,
                    end_time=final_end_time,
                    run_id=run_id,
                    error_message=error_message,
                    error_events=self.error_events,
                    hostname=runtime_ctx.hostname,
                )
            if emit:
                emit.emit_end("slack_notification", status="OK", message="Slack notified")

            # Release resources
            if self.db_manager:
                self.db_manager.disconnect()
            if self.ssh_tunnel:
                self.ssh_tunnel.stop()

            self.logger.info("Recursos libertados")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _persist_single_record(
        self,
        *,
        run_id: str,
        indicator_id: str,
        area: Optional[str],
        title: Optional[str],
        application: Optional[str],
        source_kind: str,
        source_url_table: Optional[str],
        source_url_json: Optional[str],
        payload: Any,
    ) -> int:
        """Persiste um único registo e devolve 1 se sucesso, 0 caso contrário."""
        try:
            payload_json = MedidataScraper.serialize_payload(payload)
            payload_hash = MedidataScraper.compute_payload_hash(payload)
            event_ts = MedidataScraper.infer_event_ts(payload) if isinstance(payload, dict) else None

            ok, _ = self.db_manager.upsert_indicator(
                run_id=run_id,
                indicator_id=indicator_id,
                area=area,
                title=title,
                application=application,
                source_kind=source_kind,
                source_url_table=source_url_table,
                source_url_json=source_url_json,
                event_ts=event_ts,
                payload_json=payload_json,
                payload_hash=payload_hash,
            )
            return 1 if ok else 0
        except Exception as exc:
            self.stats["db_records_failed"] += 1
            self.add_error_event(
                category="db_persist",
                context=f"indicator={indicator_id}",
                message=str(exc),
            )
            return 0


def main() -> None:
    """Função principal."""
    try:
        orchestrator = ScrapeOrchestrator()
        orchestrator.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nInterrompido pelo utilizador")
        sys.exit(1)
    except Exception as exc:
        print(f"\nErro fatal: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

