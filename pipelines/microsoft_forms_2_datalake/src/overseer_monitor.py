"""
Módulo de monitorização de performance para pipelines.

Responsável por recolher métricas (tempo, CPU, memória), guardar um registo
na tabela `logs` do servidor BAZE e expor utilitários para alimentar o frontend.
O foco é ser reaproveitável noutros pipelines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import os
import socket

import psutil
import pymysql
import pymysql.cursors

from overseer_sdk.logger import get_logger

MAX_LOG_ERROR_LEN = int(os.getenv("PERF_ERROR_MAX_LEN", "65000"))


def _sanitize_table_name(table_name: str) -> str:
    """Remove caracteres perigosos do nome da tabela para evitar SQL injection."""
    parts: List[str] = []
    for raw_part in str(table_name or "").split("."):
        safe = "".join(ch for ch in raw_part if ch.isalnum() or ch == "_")
        if safe:
            parts.append(safe)
    return ".".join(parts)


class OverseerMonitor:
    """Recolhe métricas de execução de um pipeline e persiste-as na BD."""

    def __init__(
        self,
        script_name: str,
        table_name: str = "pipeline_runs",
        db_params: Optional[Dict[str, Any]] = None,
        frontend_base_url: Optional[str] = None,
    ):
        self.logger = get_logger("overseer_monitor")
        self.script_name = script_name
        self.table_name = _sanitize_table_name(table_name)
        self.db_params = db_params or {}
        self.frontend_base_url = frontend_base_url

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status: str = "running"
        self.error_message: Optional[str] = None
        self.stage_timings: Dict[str, Dict[str, Any]] = {}
        self.log_id: Optional[int] = None

        self.process = psutil.Process()
        self.start_cpu_times: Optional[psutil._common.pcputimes] = None  # type: ignore[attr-defined]
        self.peak_rss: int = 0
        self.hostname: str = socket.gethostname()

    def set_db_params(self, db_params: Dict[str, Any]) -> None:
        """Atualiza parâmetros de ligação à BD para o momento do insert."""
        self.db_params = db_params
        if db_params.get("table"):
            self.table_name = _sanitize_table_name(str(db_params["table"]))

    def set_table_name(self, table_name: str) -> None:
        """Atualiza o nome da tabela de logs garantindo higienização."""
        self.table_name = _sanitize_table_name(table_name)

    def start(self) -> None:
        """Marca o início da execução."""
        if self.start_time is not None:
            return

        self.start_time = datetime.now()
        self.start_cpu_times = self.process.cpu_times()
        self.peak_rss = self.process.memory_info().rss
        self.logger.debug("Overseer monitor iniciado.")

    def _refresh_peak_memory(self) -> None:
        """Guarda o pico de memória RSS observado."""
        try:
            current_rss = self.process.memory_info().rss
            self.peak_rss = max(self.peak_rss, current_rss)
        except Exception:
            # psutil pode falhar se o processo terminar entretanto
            pass

    def mark_stage_start(self, name: str) -> None:
        """Marca o início de uma fase (dbconn, loading, email, ...)."""
        if self.start_time is None:
            self.start()

        self._refresh_peak_memory()
        self.stage_timings[name] = {
            "start": datetime.now(),
            "cpu_start": self.process.cpu_times(),
        }
        self.logger.debug(f"Stage '{name}' iniciado.")

    def mark_stage_end(self, name: str) -> None:
        """Marca o fim de uma fase e calcula métricas básicas."""
        stage = self.stage_timings.get(name)
        if not stage or stage.get("end"):
            return

        self._refresh_peak_memory()
        end_time = datetime.now()
        cpu_end = self.process.cpu_times()

        cpu_start = stage.get("cpu_start")
        cpu_time = 0.0
        if cpu_start:
            cpu_time = max(
                0.0,
                (cpu_end.user - cpu_start.user)
                + (cpu_end.system - cpu_start.system),
            )

        stage["end"] = end_time
        stage["wall_time"] = (end_time - stage["start"]).total_seconds()
        stage["cpu_time"] = cpu_time
        self.logger.debug(
            f"Stage '{name}' concluído em {stage['wall_time']:.3f}s "
            f"(CPU {stage['cpu_time']:.3f}s)."
        )

    def _get_stage_metric(self, name: str, key: str) -> float:
        stage = self.stage_timings.get(name, {})
        return float(stage.get(key, 0.0))

    def _close_open_stages(self) -> None:
        """Fecha fases que ficaram sem fim explícito (útil em exceções)."""
        for name, data in list(self.stage_timings.items()):
            if data and not data.get("end"):
                self.mark_stage_end(name)

    def _cpu_time_delta(self) -> float:
        if not self.start_cpu_times or not self.end_time:
            return 0.0

        end_cpu = self.process.cpu_times()
        return max(
            0.0,
            (end_cpu.user - self.start_cpu_times.user)
            + (end_cpu.system - self.start_cpu_times.system),
        )

    def _calculate_cpu_usage(self, cpu_time: float, duration: float) -> float:
        """Calcula % média de CPU baseada no tempo de CPU versus wall-time."""
        if duration <= 0:
            return 0.0
        cores = psutil.cpu_count(logical=True) or 1
        usage = (cpu_time / (duration * cores)) * 100
        return round(min(max(usage, 0.0), 100.0), 2)

    def finish(
        self,
        status: str,
        error_message: Optional[str] = None,
        db_manager: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Finaliza a recolha, grava o registo na BD e devolve os dados inseridos.
        """
        if self.start_time is None:
            self.start()

        self.end_time = datetime.now()
        self._refresh_peak_memory()
        self._close_open_stages()

        duration = (self.end_time - self.start_time).total_seconds()
        cpu_time = self._cpu_time_delta()
        usage_cpu = self._calculate_cpu_usage(cpu_time, duration)
        usage_mem_mb = round(self.peak_rss / (1024 * 1024), 2)
        normalized_status = "OK" if status.lower() == "success" else "NOK"

        truncated_error = self._truncate_error(error_message)

        record = {
            "scriptName": self.script_name,
            "LogDate": self.start_time,
            "startDate": self.start_time,
            "endDate": self.end_time,
            "execTime": round(duration, 3),
            "usageCPU": usage_cpu,
            "usageMemoria": usage_mem_mb,
            # Temporariamente não usamos tempos por fase no registo da BD
            "dbconn_wt": None,
            "dbconn_pt": None,
            "loading_wt": None,
            "loading_pt": None,
            "email_wt": None,
            "email_pt": None,
            "status": normalized_status,
            "errorMessage": truncated_error,
            "regDate": datetime.now(),
            "modDate": datetime.now(),
            "hostname": self.hostname,
        }

        self.log_id = self._persist_record(record, db_manager)
        record["id"] = self.log_id
        record["frontend_url"] = self.get_frontend_url(self.log_id)
        return record

    def _persist_record(
        self, record: Dict[str, Any], db_manager: Optional[Any] = None
    ) -> Optional[int]:
        """Insere o registo na tabela de logs (ou devolve None se falhar)."""
        connection, owns_connection = self._get_connection(db_manager)
        if connection is None:
            self.logger.warning(
                "Sem ligação à BD: não foi possível gravar métricas na tabela de logs."
            )
            return None

        preferred_columns = [
            "scriptName",
            "pipelineId",
            "LogDate",
            "startDate",
            "endDate",
            "execTime",
            "usageCPU",
            "usageMemoria",
            "logMessage",
            "dbconn_wt",
            "dbconn_pt",
            "loading_wt",
            "loading_pt",
            "email_wt",
            "email_pt",
            "status",
            "errorMessage",
            "owner",
            "criticality",
            "OS",
            "regDate",
            "modDate",
            "hostname",
        ]

        table_types = self._get_table_column_types(connection)
        if not table_types:
            self.logger.warning(
                f"Tabela {self.table_name} sem colunas visíveis; registo não gravado."
            )
            return None

        payload = dict(record)
        payload.setdefault("pipelineId", self.script_name)
        payload.setdefault("logMessage", record.get("errorMessage"))
        payload.setdefault("OS", os.name)

        status_type = str(table_types.get("status") or "").lower()
        if status_type.startswith("enum(") and "success" in status_type and "failed" in status_type:
            status_map = {"OK": "Success", "NOK": "Failed", "SUCCESS": "Success", "FAILED": "Failed"}
            payload["status"] = status_map.get(str(payload.get("status") or "").upper(), payload.get("status"))

        criticality_type = str(table_types.get("criticality") or "").lower()
        if criticality_type.startswith("enum(") and "low" in criticality_type:
            crit = str(payload.get("criticality") or "").strip().lower()
            crit_map = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}
            if crit in crit_map:
                payload["criticality"] = crit_map[crit]

        exec_type = str(table_types.get("execTime") or "").lower()
        if exec_type.startswith("time"):
            try:
                total = max(0, int(float(payload.get("execTime") or 0)))
                h = total // 3600
                m = (total % 3600) // 60
                s = total % 60
                payload["execTime"] = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception:
                pass

        columns = [c for c in preferred_columns if c in table_types]
        if not columns:
            self.logger.warning(
                f"Tabela {self.table_name} não contém colunas compatíveis para insert."
            )
            return None

        placeholders = ", ".join(["%s"] * len(columns))
        query = (
            f"INSERT INTO {self.table_name} "
            f"({', '.join(columns)}) VALUES ({placeholders})"
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(payload.get(col) for col in columns))
                connection.commit()
                inserted_id = getattr(cursor, "lastrowid", None)
                self.logger.info(
                    f"Registo de overseer gravado na tabela {self.table_name} "
                    f"(id={inserted_id})."
                )
                return inserted_id
        except Exception as exc:
            self.logger.warning(f"Falha ao gravar métricas na tabela {self.table_name}: {exc}")
            return None
        finally:
            if owns_connection:
                try:
                    connection.close()
                except Exception:
                    pass

    def _get_table_column_types(self, connection: pymysql.Connection) -> Dict[str, str]:
        """Obtém colunas visíveis da tabela alvo (com suporte a schema.table)."""
        table_ref = str(self.table_name or "").strip()
        if not table_ref:
            return {}

        if "." in table_ref:
            schema_name, table_name = table_ref.split(".", 1)
        else:
            schema_name = ""
            table_name = table_ref

        with connection.cursor() as cursor:
            if not schema_name:
                cursor.execute("SELECT DATABASE() AS dbname")
                row = cursor.fetchone() or {}
                schema_name = str(row.get("dbname") or "")
            if not schema_name:
                return {}

            cursor.execute(
                """
                SELECT COLUMN_NAME, COLUMN_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                """,
                (schema_name, table_name),
            )
            return {
                str(row.get("COLUMN_NAME")): str(row.get("COLUMN_TYPE") or "")
                for row in cursor.fetchall()
            }
    def _get_connection(
        self, db_manager: Optional[Any] = None
    ) -> Tuple[Optional[pymysql.Connection], bool]:
        """
        Resolve a ligação a usar.

        Returns:
            Tupla (connection, owns_connection)
        """
        if db_manager and getattr(db_manager, "connection", None):
            return db_manager.connection, False

        if self.db_params:
            try:
                conn = pymysql.connect(
                    charset="utf8mb4",
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                    **self.db_params,
                )
                return conn, True
            except Exception as exc:
                self.logger.error(f"Não foi possível abrir ligação para gravar logs: {exc}")
                return None, False

        return None, False

    def get_frontend_url(self, log_id: Optional[int] = None) -> Optional[str]:
        """
        Devolve URL para o frontend de monitorização, opcionalmente com o runId.
        """
        if not self.frontend_base_url:
            return None

        base = self.frontend_base_url.rstrip("/")
        if log_id:
            return f"{base}?runId={log_id}"
        return base

    def _truncate_error(self, error_message: Optional[str]) -> Optional[str]:
        if not error_message:
            return None
        clean = error_message.strip()
        if not clean:
            return None
        if len(clean) > MAX_LOG_ERROR_LEN:
            return clean[: MAX_LOG_ERROR_LEN - 3] + "..."
        return clean


class OverseerLogRepository:
    """Helper para ler dados da tabela de logs e alimentar o frontend/API."""

    def __init__(
        self,
        db_params: Dict[str, Any],
        table_name: str = "pipeline_runs",
        connection: Optional[pymysql.Connection] = None,
    ):
        self.logger = get_logger("overseer_repo")
        self.table_name = _sanitize_table_name(table_name)
        self.db_params = db_params
        self.connection = connection
        self._owns_connection = connection is None

    def __enter__(self) -> "OverseerLogRepository":
        self._ensure_connection()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._owns_connection and self.connection:
            try:
                self.connection.close()
            except Exception:
                pass

    def _ensure_connection(self) -> None:
        if self.connection:
            return
        self.connection = pymysql.connect(
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            **self.db_params,
        )

    def _get_connection(self) -> pymysql.Connection:
        self._ensure_connection()
        if not self.connection:
            raise RuntimeError("Ligação à BD não disponível.")
        return self.connection

    def fetch_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        script_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Devolve uma lista de registos de logs para alimentar o frontend."""
        conn = self._get_connection()
        clauses = []
        params: List[Any] = []

        if script_name:
            clauses.append("scriptName = %s")
            params.append(script_name)
        if status:
            clauses.append("status = %s")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = (
            f"SELECT id, scriptName, LogDate, startDate, endDate, execTime, usageCPU, "
            f"usageMemoria, dbconn_wt, dbconn_pt, loading_wt, loading_pt, email_wt, "
            f"email_pt, status, errorMessage, regDate, modDate "
            f"FROM {self.table_name} "
            f"{where_sql} "
            f"ORDER BY startDate DESC "
            f"LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())

    def fetch_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um registo específico (para detalhe no frontend)."""
        conn = self._get_connection()
        query = (
            f"SELECT id, scriptName, LogDate, startDate, endDate, execTime, usageCPU, "
            f"usageMemoria, dbconn_wt, dbconn_pt, loading_wt, loading_pt, email_wt, "
            f"email_pt, status, errorMessage, regDate, modDate "
            f"FROM {self.table_name} "
            f"WHERE id = %s"
        )
        with conn.cursor() as cursor:
            cursor.execute(query, (log_id,))
            return cursor.fetchone()






