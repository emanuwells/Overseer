"""
Sistema de Logging Centralizado partilhado por todos os pipelines Overseer.

Fornece logging colorido (se ``colorlog`` disponível), rotativo e
com múltiplos níveis para todo o sistema.

Utilização::

    from overseer_sdk.logger import get_logger, get_log_manager

    log = get_logger("my_module")
    log.info("Tudo bem!")
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional

try:
    import colorlog
except ImportError:
    colorlog = None  # type: ignore[assignment]


class LoggerManager:
    """
    Gestor centralizado de logging com suporte para:
    - Logs rotativos em ficheiro
    - Output colorido na consola (se ``colorlog`` disponível)
    - Diferentes níveis de verbosidade
    - Logs separados por módulo
    """

    def __init__(
        self,
        log_dir: str = "logs",
        max_bytes: int = 10_485_760,
        backup_count: int = 5,
        system_log_name: str = "overseer_system.log",
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.system_log_name = system_log_name
        self._loggers: Dict[str, logging.Logger] = {}

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_stream(stream):  # noqa: ANN001
        """Garante que a consola aceita UTF-8 sem falhar em emojis."""
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
            return stream
        except Exception:
            pass
        try:
            if hasattr(stream, "buffer"):
                return io.TextIOWrapper(
                    stream.buffer,
                    encoding="utf-8",
                    errors="replace",
                    line_buffering=True,
                )
        except Exception:
            pass
        return stream

    # ------------------------------------------------------------------

    def get_logger(self, name: str, level: int = logging.INFO) -> logging.Logger:
        if name in self._loggers:
            return self._loggers[name]

        lgr = logging.getLogger(name)
        lgr.setLevel(level)
        lgr.propagate = False

        if lgr.handlers:
            lgr.handlers.clear()

        # Console handler
        console_stream = self._normalize_stream(sys.stdout)
        if colorlog is not None:
            console_handler = colorlog.StreamHandler(console_stream)
            console_fmt = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        else:
            console_handler = logging.StreamHandler(console_stream)
            console_fmt = logging.Formatter(
                "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        console_handler.setLevel(level)
        console_handler.setFormatter(console_fmt)
        lgr.addHandler(console_handler)

        # File format (shared)
        file_fmt = logging.Formatter(
            "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Main (system) log file
        main_log = self.log_dir / self.system_log_name
        main_handler = RotatingFileHandler(
            main_log,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(file_fmt)
        lgr.addHandler(main_handler)

        # Module-specific log file
        mod_log = self.log_dir / f"{name}.log"
        mod_handler = RotatingFileHandler(
            mod_log,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        mod_handler.setLevel(logging.DEBUG)
        mod_handler.setFormatter(file_fmt)
        lgr.addHandler(mod_handler)

        self._loggers[name] = lgr
        return lgr

    # ------------------------------------------------------------------

    def create_operation_log(self, operation_name: str) -> Path:
        """Cria um ficheiro de log para uma operação específica."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{operation_name}_{timestamp}.log"

        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        for lgr in self._loggers.values():
            lgr.addHandler(handler)
        return log_file

    def log_operation_summary(self, logger_name: str, summary: dict) -> None:
        lgr = self.get_logger(logger_name)
        lgr.info("=" * 80)
        lgr.info("RESUMO DA OPERAÇÃO")
        lgr.info("=" * 80)
        for key, value in summary.items():
            lgr.info(f"{key}: {value}")
        lgr.info("=" * 80)


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------

_log_manager: Optional[LoggerManager] = None


def get_log_manager(
    log_dir: str = "logs",
    system_log_name: str = "overseer_system.log",
) -> LoggerManager:
    """Devolve (ou cria) o ``LoggerManager`` singleton."""
    global _log_manager
    if _log_manager is None:
        _log_manager = LoggerManager(log_dir=log_dir, system_log_name=system_log_name)
    return _log_manager


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Atalho: devolve um logger pelo nome, criando o manager se necessário."""
    manager = get_log_manager()
    return manager.get_logger(name, level)
