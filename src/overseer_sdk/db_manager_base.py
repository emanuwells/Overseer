"""
Base abstracta para gestores de base de dados (PyMySQL raw).

Cada pipeline estende ``DatabaseManagerBase`` com as suas tabelas
e operações específicas (UPSERT, DDL, etc.).

Utilização::

    from overseer_sdk.db_manager_base import DatabaseManagerBase

    class MyDatabaseManager(DatabaseManagerBase):
        def ensure_tables(self):
            self._execute_update("CREATE TABLE IF NOT EXISTS ...")
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import pymysql.cursors


logger = logging.getLogger("overseer_sdk.db")


class DatabaseManagerBase(ABC):
    """
    Base para gestores de BD dos pipelines Overseer.

    Funcionalidades comuns:
    - ``connect()`` / ``disconnect()``
    - ``_execute_query()`` / ``_execute_update()``
    - Tracking de stats (inserts, updates, errors, …)
    - Context-manager (``with``)

    O método ``ensure_tables()`` deve ser implementado por cada sub-classe.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        *,
        autocommit: bool = True,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.autocommit = autocommit

        self.connection: Optional[pymysql.Connection] = None
        self.stats: Dict[str, int] = self._default_stats()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @staticmethod
    def _default_stats() -> Dict[str, int]:
        return {
            "records_attempted": 0,
            "records_written": 0,
            "records_failed": 0,
            "inserts": 0,
            "updates": 0,
            "errors": 0,
            "skipped": 0,
        }

    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()

    def reset_stats(self) -> None:
        self.stats = self._default_stats()

    # ------------------------------------------------------------------
    # Conexão
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Estabelece conexão com a base de dados."""
        logger.info("A conectar a %s@%s:%s/%s", self.user, self.host, self.port, self.database)
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=self.autocommit,
            )
            logger.info("Conexão estabelecida com sucesso")
        except Exception as exc:
            logger.error("Falha na conexão: %s", exc)
            raise

    def disconnect(self) -> None:
        """Encerra a conexão com a base de dados."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Conexão encerrada")
            except Exception as exc:
                logger.error("Erro ao encerrar conexão: %s", exc)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executa uma query SELECT e devolve lista de dicts."""
        try:
            with self.connection.cursor() as cursor:  # type: ignore[union-attr]
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as exc:
            logger.error("Erro ao executar query: %s", exc)
            raise

    def _execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Executa INSERT / UPDATE / DDL e devolve nº de linhas afectadas."""
        try:
            with self.connection.cursor() as cursor:  # type: ignore[union-attr]
                affected = cursor.execute(query, params)
                return affected
        except Exception as exc:
            logger.error("Erro ao executar atualização: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Auto-DDL (cada pipeline implementa)
    # ------------------------------------------------------------------

    @abstractmethod
    def ensure_tables(self) -> None:
        """Cria as tabelas do pipeline se não existirem."""
        ...

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DatabaseManagerBase":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        self.disconnect()
