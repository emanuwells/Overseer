"""
Gestor de Base de Dados MariaDB para Webapp Medidata.

Estende ``DatabaseManagerBase`` do ``overseer_sdk`` com tabelas e
operações UPSERT específicas do Medidata (medidata_scrape_runs,
medidata_indicator_records_raw).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from overseer_sdk.db_manager_base import DatabaseManagerBase


class DatabaseManager(DatabaseManagerBase):
    """
    Gestor de operações na base de dados MAIATRON.

    Tabelas:
    - ``medidata_scrape_runs`` — metadados de execução
    - ``medidata_indicator_records_raw`` — dados raw dos indicadores
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str = "MAIATRON",
    ):
        super().__init__(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
        )

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Cria as tabelas de scraping se não existirem (auto-DDL)."""

        ddl_runs = """
        CREATE TABLE IF NOT EXISTS medidata_scrape_runs (
            run_id VARCHAR(64) PRIMARY KEY,
            started_at DATETIME NOT NULL,
            finished_at DATETIME NULL,
            status VARCHAR(32) NOT NULL,
            source_list_url TEXT NOT NULL,
            total_indicators INT NOT NULL DEFAULT 0,
            error_message TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_msr_started_at (started_at),
            INDEX idx_msr_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        ddl_raw = """
        CREATE TABLE IF NOT EXISTS medidata_indicator_records_raw (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            indicator_id VARCHAR(128) NOT NULL,
            area VARCHAR(255) NULL,
            title VARCHAR(512) NULL,
            application VARCHAR(255) NULL,
            source_kind VARCHAR(16) NOT NULL,
            source_url_table TEXT NULL,
            source_url_json TEXT NULL,
            event_ts DATETIME NULL,
            payload_json JSON NOT NULL,
            payload_hash CHAR(64) NOT NULL,
            first_seen_at DATETIME NOT NULL,
            last_seen_at DATETIME NOT NULL,
            last_run_id VARCHAR(64) NOT NULL,
            seen_count BIGINT NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_medidata_raw (indicator_id, source_kind, payload_hash),
            INDEX idx_mir_indicator_id (indicator_id),
            INDEX idx_mir_event_ts (event_ts),
            INDEX idx_mir_last_seen_at (last_seen_at),
            INDEX idx_mir_last_run_id (last_run_id),
            CONSTRAINT fk_mir_last_run FOREIGN KEY (last_run_id)
                REFERENCES medidata_scrape_runs(run_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        self._execute_update(ddl_runs)
        self._execute_update(ddl_raw)

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def start_run(self, run_id: str, source_list_url: str) -> None:
        """Insere registo de run com status=running."""
        sql = """
            INSERT INTO medidata_scrape_runs
            (run_id, started_at, status, source_list_url, total_indicators)
            VALUES (%s, %s, %s, %s, %s)
        """
        self._execute_update(
            sql,
            (run_id, datetime.now(), "running", source_list_url, 0),
        )

    def finish_run(
        self,
        run_id: str,
        status: str,
        total_indicators: int,
        error_message: Optional[str] = None,
    ) -> None:
        """Atualiza registo de run com status final."""
        sql = """
            UPDATE medidata_scrape_runs
            SET finished_at = %s,
                status = %s,
                total_indicators = %s,
                error_message = %s
            WHERE run_id = %s
        """
        self._execute_update(
            sql,
            (datetime.now(), status, total_indicators, error_message, run_id),
        )

    # ------------------------------------------------------------------
    # UPSERT
    # ------------------------------------------------------------------

    def upsert_indicator(
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
        event_ts: Optional[datetime],
        payload_json: str,
        payload_hash: str,
    ) -> Tuple[bool, str]:
        """
        UPSERT na tabela medidata_indicator_records_raw.
        Dedup por (indicator_id, source_kind, payload_hash).
        """
        now = datetime.now()
        sql = """
            INSERT INTO medidata_indicator_records_raw
            (
                indicator_id, area, title, application,
                source_kind, source_url_table, source_url_json,
                event_ts, payload_json, payload_hash,
                first_seen_at, last_seen_at, last_run_id, seen_count
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSON), %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                area = VALUES(area),
                title = VALUES(title),
                application = VALUES(application),
                source_url_table = VALUES(source_url_table),
                source_url_json = VALUES(source_url_json),
                event_ts = VALUES(event_ts),
                payload_json = VALUES(payload_json),
                last_seen_at = VALUES(last_seen_at),
                last_run_id = VALUES(last_run_id),
                seen_count = seen_count + 1,
                updated_at = CURRENT_TIMESTAMP
        """
        try:
            self._execute_update(
                sql,
                (
                    indicator_id, area, title, application,
                    source_kind, source_url_table, source_url_json,
                    event_ts, payload_json, payload_hash,
                    now, now, run_id, 1,
                ),
            )
            self.stats["records_written"] += 1
            return True, "upsert"
        except Exception as exc:
            self.stats["records_failed"] += 1
            return False, "error"

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Obtém a última run bem-sucedida (para API)."""
        sql = """
            SELECT run_id, status, started_at, finished_at, total_indicators, error_message
            FROM medidata_scrape_runs
            WHERE status IN ('success', 'warning')
            ORDER BY finished_at DESC, started_at DESC
            LIMIT 1
        """
        rows = self._execute_query(sql)
        return rows[0] if rows else None
