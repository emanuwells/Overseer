"""
Script Principal de Sincronização Excel → MariaDB
Versão: 0.2.0
Autor: Emanuel Ferreira (emanuel.ferreira@cm-maia.pt)

Orquestra todo o processo de leitura, validação e sincronização.
"""

import json
import os
import sys
from datetime import timedelta
from pathlib import Path, PurePath
from datetime import datetime
from typing import Dict, List, Optional
import traceback

# ---------------------------------------------------------------------------
# Overseer SDK — must patch sys.path BEFORE importing overseer_sdk
# ---------------------------------------------------------------------------
_OVERSEER_ROOT = Path(__file__).resolve().parents[3]  # project root
if str(_OVERSEER_ROOT) not in sys.path:
    sys.path.insert(0, str(_OVERSEER_ROOT))

from overseer_sdk.logger import get_log_manager, get_logger
from overseer_sdk.ssh_tunnel import SSHTunnelManager
from overseer_sdk.slack_notifier import SlackNotifier
from overseer_sdk.runtime_context import runtime_ctx

# Lineage emitter — emits structured markers to stdout for the orchestrator
try:
    from overseer_monitor.lineage_emitter import LineageEmitter
    _lineage_emit = LineageEmitter()
except ImportError:
    _lineage_emit = None

# ---------------------------------------------------------------------------
# Local pipeline modules
# ---------------------------------------------------------------------------
from db_manager import DatabaseManager
from excel_reader import ExcelReader
from forms_reader import FormsReader
from validator import RowValidator
from overseer_monitor import OverseerMonitor


DEFAULT_FRONTEND_URL = (
    os.getenv("OVERSEER_MONITOR_URL")
    or os.getenv("OVERSEER_FRONTEND_URL")
    or "http://baze2.cm-maia.pt/D4CMMaia/Bruin_Monitor/index.html"
)
MAX_ERROR_MESSAGE_LENGTH = int(os.getenv("PERF_ERROR_MAX_LEN", "65000"))


def get_end_of_period_date(period_str: str) -> datetime:
    """
    Converte uma string de período (ex: '2025-01', '2025-S1') para a data de FIM desse período.
    """
    parts = period_str.split('-')
    year = int(parts[0])

    if len(parts) == 1:  # Anual
        return datetime(year, 12, 31)

    period_part = parts[1]
    if 'S' in period_part:  # Semestral
        # Lógica explícita para evitar erros. 'S1' para semestre 1, qualquer outra coisa para semestre 2.
        if period_part == 'S1':
            month = 6
        else:
            month = 12
    elif 'T' in period_part:  # Trimestral
        quarter = int(period_part.replace('T', ''))
        month = quarter * 3
    else:  # Mensal
        month = int(period_part)

    # Para obter o último dia do mês, vamos para o primeiro dia do mês seguinte e subtraímos um dia.
    # Isto lida corretamente com anos bissextos e meses de diferentes durações.
    if month == 12:
        next_month_first_day = datetime(year + 1, 1, 1)
    else:
        next_month_first_day = datetime(year, month + 1, 1)
    
    return next_month_first_day - timedelta(days=1)


def get_start_of_period_date(period_str: str) -> datetime:
    """
    Converte uma string de período (ex: '2025-01', '2025-S1', '2025-T1')
    para a data de INÍCIO desse período, conforme a documentação.

    Args:
        period_str: A string do período.

    Returns:
        Um objeto datetime representando o início do período.
    """
    parts = period_str.split('-') # type: ignore
    year = int(parts[0])

    if len(parts) == 1:  # Anual (ex: '2025')
        return datetime(year, 1, 1)

    period_part = parts[1]
    if 'S' in period_part:  # Semestral
        semester = int(period_part.replace('S', ''))
        month = 1 if semester == 1 else 7
    elif 'T' in period_part:  # Trimestral
        quarter = int(period_part.replace('T', ''))
        month = (quarter - 1) * 3 + 1
    else:  # Mensal
        month = int(period_part)

    return datetime(year, month, 1)


class SyncOrchestrator:
    """
    Orquestrador principal do sistema de sincronização.
    Coordena todos os módulos para realizar a sincronização completa.
    """

    def __init__(self, config_dir: Path = Path("config"), secrets_dir: Path = Path("secrets")):
        """
        Inicializa o orquestrador.

        Args:
            config_dir: Diretório de configuração
            secrets_dir: Diretório de secrets (credenciais)
        """
        self.logger = get_logger("orchestrator")
        self.config_dir = config_dir
        self.secrets_dir = secrets_dir

        self.config = None
        self.db_config = None
        self.paths_config = None
        self.monitoring_config: Dict[str, str] = {}

        self.ssh_tunnel = None
        self.db_manager = None
        self.excel_reader = None
        self.forms_reader = None
        self.validator = RowValidator()
        self.slack_notifier = SlackNotifier(self.secrets_dir / "slack.json")
        self.overseer_monitor: Optional[OverseerMonitor] = None
        self.error_events: List[Dict[str, str]] = []

        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "forms_processed": 0,
            "forms_failed": 0,
            "total_records": 0,
            "records_inserted": 0,
            "records_updated": 0,
            "records_skipped": 0,
            "records_failed": 0,
            "series_updated": 0
        }

        self.module_logger_names = [
            "main",
            "orchestrator",
            "db_manager",
            "excel_reader",
            "forms_reader",
            "validator",
            "row_validator",
            "slack_notifier",
            "ssh_tunnel",
            "overseer_monitor",
            "overseer_frontend",
            "logger",
        ]

    def emit_module_log_heartbeat(self, stage: str) -> None:
        """Escreve uma linha de log em todos os módulos para garantir visibilidade no Lineage."""
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = (
            f"[heartbeat] stage={stage} ts={stamp} "
            f"forms_ok={self.stats['forms_processed']} forms_err={self.stats['forms_failed']} "
            f"records_total={self.stats['total_records']} records_failed={self.stats['records_failed']}"
        )
        for name in self.module_logger_names:
            try:
                get_logger(name).info(summary)
            except Exception:
                continue

    def load_config(self):
        """
        Carrega todas as configurações necessárias.

        Raises:
            FileNotFoundError: Se ficheiros de configuração não existirem
        """
        self.logger.info("📋 A carregar configurações...")

        # Carrega mappings
        mappings_file = self.config_dir / "mappings.json"
        if not mappings_file.exists():
            raise FileNotFoundError(f"Ficheiro de mapeamentos não encontrado: {mappings_file}")

        with open(mappings_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.logger.info("✅ Mapeamentos carregados")

        # Carrega credenciais de BD
        db_config_file = self.secrets_dir / "database.json"
        if not db_config_file.exists():
            raise FileNotFoundError(f"Credenciais de BD não encontradas: {db_config_file}")

        with open(db_config_file, 'r', encoding='utf-8') as f:
            self.db_config = json.load(f)
        self.logger.info("✅ Credenciais de BD carregadas")

        # Carrega paths
        paths_file = self.secrets_dir / "paths.json"
        if not paths_file.exists():
            raise FileNotFoundError(f"Configuração de paths não encontrada: {paths_file}")

        with open(paths_file, 'r', encoding='utf-8') as f:
            self.paths_config = json.load(f)
        self.logger.info("✅ Paths carregados")

        # Configuração opcional de monitorização
        monitoring_defaults = {
            "logs_table": "Overseer.pipeline_runs",
            "script_name": "Microsoft_Forms_2_Datalake",
            "frontend_base_url": DEFAULT_FRONTEND_URL
        }
        monitoring_file = self.secrets_dir / "monitoring.json"
        if not monitoring_file.exists():
            alt_path = self.config_dir / "monitoring.json"
            monitoring_file = alt_path if alt_path.exists() else monitoring_file

        if monitoring_file.exists():
            with open(monitoring_file, "r", encoding="utf-8") as f:
                loaded_monitoring = json.load(f)
                monitoring_defaults.update(loaded_monitoring)
            self.logger.info(f"✅ Configuração de monitorização carregada de {monitoring_file}")
        else:
            self.logger.info("Configuração de monitorização não encontrada; a usar defaults.")

        self.monitoring_config = monitoring_defaults

    def _resolve_excel_directory(self) -> Path:
        """
        Resolve o caminho dos ficheiros Excel/Forms de forma independente do utilizador/máquina.
        A configuração pode conter o caminho completo (mesmo com um utilizador antigo) ou só o sufixo
        a partir da pasta OneDrive (ex.: `OneDrive - Câmara Municipal da Maia\\Sharepoints\\...`). Tenta
        várias combinações razoáveis até encontrar uma pasta existente.
        """
        if not self.paths_config or "excel_directory" not in self.paths_config:
            raise FileNotFoundError("Configuração 'excel_directory' não encontrada em secrets/paths.json")

        raw_path = self.paths_config["excel_directory"]
        expanded = Path(os.path.expandvars(raw_path)).expanduser()
        path_parts = Path(raw_path).parts

        def _add_candidate(candidates: List[Path], path: Optional[Path]):
            if path and str(path) not in {str(c) for c in candidates}:
                candidates.append(path)

        onedrive_idx: Optional[int] = None
        for idx, part in enumerate(path_parts):
            if "onedrive" in part.lower():
                onedrive_idx = idx
                break

        suffix_from_onedrive = Path(*path_parts[onedrive_idx:]) if onedrive_idx is not None else Path(*path_parts)
        suffix_without_onedrive = (
            Path(*path_parts[onedrive_idx + 1 :]) if onedrive_idx is not None and onedrive_idx + 1 < len(path_parts) else None
        )

        candidates: List[Path] = []
        _add_candidate(candidates, expanded)
        _add_candidate(candidates, Path.home() / suffix_from_onedrive)

        onedrive_envs = [
            os.getenv("OneDriveCommercial"),
            os.getenv("OneDrive"),
            os.getenv("ONEDRIVE"),
            os.getenv("OneDriveConsumer"),
        ]
        for env_path in onedrive_envs:
            if not env_path:
                continue
            od_root = Path(env_path)
            _add_candidate(candidates, od_root / suffix_from_onedrive)
            if suffix_without_onedrive:
                _add_candidate(candidates, od_root / suffix_without_onedrive)

        for od_dir in Path.home().glob("OneDrive*"):
            if od_dir.is_dir():
                _add_candidate(candidates, od_dir / suffix_from_onedrive)
                if suffix_without_onedrive:
                    _add_candidate(candidates, od_dir / suffix_without_onedrive)

        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"Diretório Excel não encontrado. Última tentativa: {expanded}. "
            "Atualiza secrets/paths.json ou confirma que a pasta OneDrive/SharePoint está sincronizada."
        )

    def setup_infrastructure(self):
        """
        Estabelece túnel SSH (se necessário) e conexão à BD.
        Usa RuntimeContext para decidir se o acesso é local ou remoto.
        """
        db_config = self.db_config['database']

        if runtime_ctx.db_is_local:
            # ── Acesso directo (pipeline corre no servidor de BD) ──
            self.logger.info("🗄️  BD local detectada — conexão directa")
            db_host = db_config.get('host', '127.0.0.1')
            db_port = int(db_config.get('port', 3306))
        elif 'ssh' in self.db_config:
            # ── Acesso remoto — túnel SSH ──
            self.logger.info("🔐 A estabelecer túnel SSH...")
            ssh_config = self.db_config['ssh']
            self.ssh_tunnel = SSHTunnelManager(
                ssh_host=ssh_config['host'],
                ssh_port=ssh_config['port'],
                ssh_user=ssh_config['user'],
                ssh_key_path=str(self.secrets_dir / ssh_config['key_filename']),
                remote_bind_host=ssh_config.get('remote_bind_host', 'localhost'),
                remote_bind_port=ssh_config.get('remote_bind_port', 3306),
            )
            self.ssh_tunnel.start()
            self.logger.info(f"✅ Túnel SSH ativo na porta {self.ssh_tunnel.get_local_port()}")
            db_host = 'localhost'
            db_port = self.ssh_tunnel.get_local_port()
        else:
            # ── Sem config SSH — conexão directa ──
            self.logger.info("🗄️  Sem config SSH — conexão directa para %s:%s",
                           db_config.get('host', '127.0.0.1'), db_config.get('port', 3306))
            db_host = db_config.get('host', '127.0.0.1')
            db_port = int(db_config.get('port', 3306))

        self.logger.info("🗄️  A conectar à base de dados...")
        self.db_manager = DatabaseManager(
            host=db_host,
            port=db_port,
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
        )
        self.db_manager.connect()
        self.logger.info("✅ Conexão à BD estabelecida")

    def setup_excel_reader(self):
        """Inicializa o leitor de Excel com as configurações."""
        self.logger.info("📊 A inicializar leitor de Excel...")
        self.excel_reader = ExcelReader(self.config)
        self.logger.info("✅ Leitor de Excel pronto")

    def setup_forms_reader(self):
        """Inicializa o leitor de Forms com as configurações."""
        self.logger.info("📋 A inicializar leitor de Forms...")
        self.forms_reader = FormsReader(self.config)
        self.logger.info("✅ Leitor de Forms pronto")

    def add_error_event(self, category: str, context: str, message: str):
        """Guarda um erro relevante para ser resumido no Slack."""
        if len(self.error_events) >= 20:
            return
        self.error_events.append({
            "category": category,
            "context": context,
            "message": message
        })

    def _compose_error_log(
        self, critical_message: Optional[str], log_path: Optional[Path]
    ) -> Optional[str]:
        """Gera texto agregado com os erros da run + excerto do log completo."""
        entries = []
        if critical_message:
            entries.append(f"CRITICAL: {critical_message}")
        for idx, event in enumerate(self.error_events, start=1):
            category = event.get("category", "erro")
            context = event.get("context", "")
            message = event.get("message", "")
            entries.append(f"{idx:02d}. {category} | {context} -> {message}")
        base_summary = "\n".join(entries).strip() if entries else ""
        if not base_summary and not log_path:
            return None

        log_excerpt = ""
        if log_path and base_summary:
            try:
                raw = Path(log_path).read_text(encoding="utf-8", errors="replace").strip()
                if raw:
                    log_excerpt = raw
            except OSError as exc:
                self.logger.warning(f"Falha ao ler log de opera��o ({log_path}): {exc}")

        parts = []
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

    def process_forms_records(self, forms_data: Dict) -> int:
        """
        Processa registos de ficheiros Forms.

        Args:
            forms_data: Dados extraídos do ficheiro Forms
                       {'records': [...], 'source_file': '...', 'id_ind': '...'}

        Returns:
            Número de registos processados com sucesso
        """
        processed = 0
        records = forms_data.get('records', [])
        source_file = forms_data.get('source_file', 'desconhecido')

        for record in records:
            try:
                # Determinar a tabela de destino e processar o registo
                target_table = record.get('target_table', 'Indicadores')

                if target_table == 'baze21RA':
                    # Processar para baze21RA (dados anuais)
                    ano = int(record['period'])
                    success, action = self.db_manager.upsert_baze21ra(
                        nome_curto=record['serie_name'],
                        ano=ano,
                        valor=record['value']
                    )
                else:
                    # Processar para Indicadores (outras periodicidades)
                    period = record['period']
                    # A chave de busca é o INÍCIO do período para evitar duplicados
                    search_date = get_start_of_period_date(period)
                    # A data a ser guardada é o FIM do período
                    self.logger.debug(f"DEBUG: period='{period}'")
                    self.logger.debug(f"DEBUG: search_date={search_date}, record_date_before_call={get_end_of_period_date(period)}")
                    record_date = get_end_of_period_date(period)
                    
                    success, action = self.db_manager.upsert_indicadores(
                        nome=record['serie_name'],
                        valor=record['value'],
                        search_date=search_date,
                        record_date=record_date
                    )

                if success:
                    processed += 1
                    if action == "insert":
                        self.stats["records_inserted"] += 1
                    elif action == "update":
                        self.stats["records_updated"] += 1
                    elif action == "skip":
                        self.stats["records_skipped"] += 1
                else:
                    self.add_error_event(
                        category="forms_record",
                        context=f"ficheiro={source_file}, serie={record.get('serie_name')}, tabela={target_table}",
                        message="upsert devolveu erro"
                    )
                    self.stats["records_failed"] += 1

                # Apenas atualiza metadados se o registo foi inserido ou atualizado
                if action in ['insert', 'update']:
                    success_fonte, action_fonte = self.db_manager.upsert_fonte(
                        nome=record['serie_name'],
                        id_ind=record['id_ind'],
                        descricao=record['description'],
                        tabela_sql=target_table,
                        metodo_imp=record['metodo_imp']
                    )

                    if success_fonte and action_fonte in ['insert', 'update']:
                        self.stats["series_updated"] += 1

            except Exception as e:
                self.logger.error(f"Erro ao processar registo Forms: {e}")
                self.logger.debug(traceback.format_exc())
                self.add_error_event(
                    category="forms_record",
                    context=f"ficheiro={source_file}, serie={record.get('serie_name')}",
                    message=str(e)
                )
                self.stats["records_failed"] += 1

        return processed

    def process_indicadores_data(self, file_data: Dict) -> int:
        """
        Processa dados para a tabela Indicadores.

        Args:
            file_data: Dados extraídos do ficheiro Excel

        Returns:
            Número de registos processados com sucesso
        """
        nome_curto = file_data['nome_curto']
        series_config = file_data['series_config']
        processed = 0

        for row_data in file_data['data']:
            # Prepara dados para validação
            row = {
                'nome': nome_curto,
                'data': row_data['data'],
                'valor': row_data['valor'],
                'mes': row_data.get('mes')
            }

            # Valida
            valid, validated = self.validator.validate_indicadores_row(row, series_config)
            if not valid:
                self.logger.warning(f"Registo inválido: {row}")
                self.stats["records_failed"] += 1
                continue

            # UPSERT
            success, action = self.db_manager.upsert_indicadores(
                nome=validated['nome'],
                valor=validated['valor'],
                search_date=validated['data'], # Para dados não-Forms, a data de busca e registo são a mesma
                record_date=validated['data'] 
            )

            if success:
                processed += 1
                if action == "insert":
                    self.stats["records_inserted"] += 1
                elif action == "update":
                    self.stats["records_updated"] += 1
                elif action == "skip":
                    self.stats["records_skipped"] += 1
            else:
                self.stats["records_failed"] += 1

        return processed

    def process_baze21ra_data(self, file_data: Dict) -> int:
        """
        Processa dados para a tabela baze21RA.

        Args:
            file_data: Dados extraídos do ficheiro Excel

        Returns:
            Número de registos processados com sucesso
        """
        nome_curto = file_data['nome_curto']
        series_config = file_data['series_config']
        processed = 0

        for row_data in file_data['data']:
            # Extrai ano da data
            try:
                if isinstance(row_data['data'], str):
                    ano = int(row_data['data'].split('-')[0])
                else:
                    ano = int(row_data['data'])
            except:
                self.logger.error(f"Não foi possível extrair ano de: {row_data['data']}")
                self.stats["records_failed"] += 1
                continue

            # Prepara dados para validação
            row = {
                'nome_curto': nome_curto,
                'ano': ano,
                'valor': row_data['valor']
            }

            # Valida
            valid, validated = self.validator.validate_baze21ra_row(row, series_config)
            if not valid:
                self.logger.warning(f"Registo inválido: {row}")
                self.stats["records_failed"] += 1
                continue

            # UPSERT
            success, action = self.db_manager.upsert_baze21ra(
                nome_curto=validated['nome_curto'],
                ano=validated['ano'],
                valor=validated['valor']
            )

            if success:
                processed += 1
                if action == "insert":
                    self.stats["records_inserted"] += 1
                elif action == "update":
                    self.stats["records_updated"] += 1
                elif action == "skip":
                    self.stats["records_skipped"] += 1
            else:
                self.stats["records_failed"] += 1

        return processed

    def update_fonte_metadata(self, file_data: Dict):
        """
        Atualiza metadados na tabela fonte.

        Args:
            file_data: Dados do ficheiro processado
        """
        success, action = self.db_manager.upsert_fonte(
            nome=file_data['nome_curto'],
            id_ind=file_data['id_ind'],
            descricao=file_data['descricao'],
            tabela_sql=file_data['target_table']
        )

        if success:
            self.stats["series_updated"] += 1
            self.logger.info(f"📝 Metadados atualizados: {file_data['nome_curto']}")

    def process_excel_file(self, file_data: Dict):
        """
        Processa um ficheiro Excel normal.

        Args:
            file_data: Dados extraídos do ficheiro Excel
        """
        self.logger.info(f"⚙️  A processar Excel: {file_data['nome_curto']} ({file_data['frequency']})")

        try:
            # Processa dados conforme a tabela de destino
            if file_data['target_table'] == 'baze21RA':
                processed = self.process_baze21ra_data(file_data)
            else:
                processed = self.process_indicadores_data(file_data)

            # Atualiza metadados
            self.update_fonte_metadata(file_data)

            self.stats["files_processed"] += 1
            self.stats["total_records"] += len(file_data['data'])

            self.logger.info(f"✅ Ficheiro Excel processado: {processed}/{len(file_data['data'])} registos")

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar ficheiro Excel: {e}")
            self.logger.debug(traceback.format_exc())
            self.add_error_event(
                category="excel_file",
                context=f"serie={file_data.get('nome_curto', 'desconhecido')}",
                message=str(e)
            )
            self.stats["files_failed"] += 1

    def process_forms_file(self, forms_data: Dict):
        """
        Processa um ficheiro Forms.

        Args:
            forms_data: Dados extraídos do ficheiro Forms
                       {'records': [...], 'source_file': '...', 'id_ind': '...'}
        """
        source_file = forms_data.get('source_file', 'unknown')
        self.logger.info(f"⚙️  A processar Forms: {source_file}")

        try:
            records = forms_data.get('records', [])
            processed = self.process_forms_records(forms_data)

            self.stats["forms_processed"] += 1
            self.stats["total_records"] += len(records)

            self.logger.info(f"✅ Ficheiro Forms processado: {processed}/{len(records)} registos")

            self.emit_module_log_heartbeat("forms_processed")

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar ficheiro Forms: {e}")
            self.logger.debug(traceback.format_exc())
            self.add_error_event(
                category="forms_file",
                context=f"ficheiro={forms_data.get('source_file', 'desconhecido')}",
                message=str(e)
            )
            self.stats["forms_failed"] += 1

    def run(self):
        """
        Executa o processo completo de sincronização.
        """
        start_time = datetime.now()
        end_time: Optional[datetime] = None
        status = "success"
        error_message = None
        self.error_events = []
        overseer_log_entry = None
        run_id: Optional[int] = None
        run_url: Optional[str] = None
        log_manager = get_log_manager()
        operation_log = log_manager.create_operation_log("sync")

        monitoring_defaults = {
            "logs_table": "Overseer.pipeline_runs",
            "script_name": "Microsoft_Forms_2_Datalake",
            "frontend_base_url": DEFAULT_FRONTEND_URL,
        }
        runtime_monitoring = {**monitoring_defaults, **(self.monitoring_config or {})}
        self.overseer_monitor = OverseerMonitor(
            script_name=runtime_monitoring["script_name"],
            table_name=runtime_monitoring["logs_table"],
            frontend_base_url=runtime_monitoring.get("frontend_base_url"),
        )
        self.overseer_monitor.start()

        self.logger.info("="*80)
        self.logger.info("🚀 INÍCIO DA SINCRONIZAÇÃO")
        self.logger.info("="*80)
        self.logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Log desta operação: {operation_log}")
        self.logger.info(runtime_ctx.summary())
        self.emit_module_log_heartbeat("startup")

        emit = _lineage_emit  # may be None if import failed

        try:
            # 1. Carrega configurações
            if emit:
                emit.emit_start("config_loading", critical=True)
            self.load_config()
            monitoring_cfg = self.monitoring_config or {}
            if self.overseer_monitor:
                self.overseer_monitor.set_table_name(
                    monitoring_cfg.get("logs_table", runtime_monitoring["logs_table"])
                )
                self.overseer_monitor.script_name = monitoring_cfg.get(
                    "script_name", runtime_monitoring["script_name"]
                )
                self.overseer_monitor.frontend_base_url = (
                    monitoring_cfg.get("frontend_base_url")
                    or self.overseer_monitor.frontend_base_url
                )
            if emit:
                emit.emit_end("config_loading", status="OK", message="Config loaded")

            # 2. Estabelece infraestrutura (SSH + BD)
            if emit:
                emit.emit_start("ssh_tunnel", critical=True)
            if self.overseer_monitor:
                self.overseer_monitor.mark_stage_start("dbconn")
            self.setup_infrastructure()
            if emit:
                emit.emit_end("ssh_tunnel", status="OK", message="Infrastructure ready")

            # 3. Marca conexão BD nos metadados
            if emit:
                emit.emit_start("db_connection", critical=True)
            if self.overseer_monitor:
                db_config = self.db_config["database"]
                self.overseer_monitor.mark_stage_end("dbconn")
                db_host = 'localhost' if self.ssh_tunnel else db_config.get('host', '127.0.0.1')
                db_port = self.ssh_tunnel.get_local_port() if self.ssh_tunnel else int(db_config.get('port', 3306))
                self.overseer_monitor.set_db_params(
                    {
                        "host": db_host,
                        "port": db_port,
                        "user": db_config["user"],
                        "password": db_config["password"],
                        "database": db_config["database"],
                    }
                )
            if emit:
                emit.emit_end("db_connection", status="OK", message="Database connected")

            # 4. Inicializa leitores Excel e Forms
            if emit:
                emit.emit_start("reader_init", critical=True)
            self.setup_excel_reader()
            self.setup_forms_reader()
            if emit:
                emit.emit_end("reader_init", status="OK", message="Readers initialized")

            # 5. Varre diretório e separa ficheiros por tipo
            if emit:
                emit.emit_start("file_discovery", critical=True)
            excel_dir = self._resolve_excel_directory()
            self.logger.info(f"? Pasta de ficheiros Excel/Forms: {excel_dir}")
            
            all_files = [f for f in excel_dir.glob('*.xlsx') if not f.name.startswith('~$')]
            
            forms_files_to_process = []
            excel_files_to_process = []

            for file_path in all_files:
                if FormsReader.is_forms_file(file_path.name):
                    forms_files_to_process.append(file_path)
                else:
                    excel_files_to_process.append(file_path)

            if not forms_files_to_process and not excel_files_to_process:
                self.logger.warning("⚠️  Nenhum ficheiro para processar")
                if emit:
                    emit.emit_end("file_discovery", status="OK", message="No files to process")
                return
            if emit:
                emit.emit_end("file_discovery", status="OK",
                              message=f"Found {len(all_files)} files (Excel={len(excel_files_to_process)}, Forms={len(forms_files_to_process)})")

            if self.overseer_monitor:
                self.overseer_monitor.mark_stage_start("loading")

            self.logger.info(f"📁 Total de ficheiros a processar: {len(all_files)} "
                           f"(Excel: {len(excel_files_to_process)}, Forms: {len(forms_files_to_process)})")

            # 6. Processa ficheiros Excel normais
            if emit:
                emit.emit_start("excel_processing", critical=False)
            for file_path in excel_files_to_process:
                file_data = self.excel_reader.read_excel_file(file_path)
                if file_data:
                    self.process_excel_file(file_data)
            if emit:
                emit.emit_end("excel_processing", status="OK",
                              message=f"Processed {len(excel_files_to_process)} Excel files")

            # 7. Processa ficheiros Forms
            if emit:
                emit.emit_start("forms_processing", critical=False)
            for file_path in forms_files_to_process:
                forms_data = self.forms_reader.read_forms_file(str(file_path))
                if forms_data and not forms_data.get('error'):
                    self.process_forms_file(forms_data)
                else:
                    error_type = (forms_data or {}).get('error_type', 'read_error')
                    self.add_error_event(
                        category="forms_file",
                        context=f"ficheiro={file_path.name}",
                        message=(forms_data.get('error', 'falha ao ler ficheiro Forms') if forms_data else 'falha ao ler ficheiro Forms') + f" [tipo={error_type}]"
                    )
                    self.stats["forms_failed"] += 1
            if emit:
                emit.emit_end("forms_processing",
                              status="NOK" if self.stats.get("forms_failed", 0) > 0 else "OK",
                              message=f"Forms processed: {self.stats.get('forms_processed', 0)}, failed: {self.stats.get('forms_failed', 0)}")

            if self.overseer_monitor:
                self.overseer_monitor.mark_stage_end("loading")

            # 8. Resumo final
            if emit:
                emit.emit_start("summary", critical=False)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.info("="*80)
            self.logger.info("✅ SINCRONIZAÇÃO CONCLUÍDA")
            self.logger.info("="*80)

            summary = {
                "Dura��o (s)": f"{duration:.2f}",
                "Ficheiros Forms processados": self.stats["forms_processed"],
                "Ficheiros Forms com erro": self.stats["forms_failed"],
                "Total de registos": self.stats["total_records"],
                "Registos inseridos": self.stats["records_inserted"],
                "Registos atualizados": self.stats["records_updated"],
                "Registos ignorados": self.stats["records_skipped"],
                "Registos com erro": self.stats["records_failed"],
                "S�ries atualizadas": self.stats["series_updated"]
            }

            log_manager.log_operation_summary("orchestrator", summary)
            if emit:
                emit.emit_end("summary", status="OK", message=f"Duration: {duration:.2f}s")

        except Exception as e:
            self.logger.critical(f"❌ ERRO CRÍTICO: {e}")
            self.logger.debug(traceback.format_exc())
            status = "failed"
            error_message = str(e)
            self.add_error_event(
                category="critical",
                context="orchestrator_run",
                message=str(e)
            )
            raise

        finally:
            # Cleanup
            final_end_time = end_time or datetime.now()
            self.emit_module_log_heartbeat("finalize")
            log_error_blob = self._compose_error_log(error_message, operation_log)

            if self.overseer_monitor and not os.getenv("OVERSEER_ORCHESTRATOR_MANAGED"):
                overseer_log_entry = self.overseer_monitor.finish(
                    status=status,
                    error_message=log_error_blob,
                    db_manager=self.db_manager,
                )
                if overseer_log_entry:
                    run_id = overseer_log_entry.get("id")
                    run_url = overseer_log_entry.get("frontend_url")

            if emit:
                emit.emit_start("slack_notification", critical=False)
            if self.slack_notifier:
                self.slack_notifier.notify_run(
                    pipeline_name="Microsoft Forms 2 Datalake",
                    status=status,
                    stats=self.stats,
                    start_time=start_time,
                    end_time=final_end_time,
                    error_message=error_message,
                    error_events=self.error_events,
                    run_id=run_id,
                    run_url=run_url,
                    hostname=self.overseer_monitor.hostname if self.overseer_monitor else None,
                    extra_lines=[f"Log: {operation_log}"] if operation_log else None,
                )
            if emit:
                emit.emit_end("slack_notification", status="OK", message="Slack notified")

            if self.db_manager:
                self.db_manager.disconnect()
            if self.ssh_tunnel:
                self.ssh_tunnel.stop()

            self.logger.info("🔒 Recursos libertados")



def main():
    """Função principal."""
    try:
        orchestrator = SyncOrchestrator()
        orchestrator.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo utilizador")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()







