from __future__ import annotations

import io
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from overseer_sdk.logger import LoggerManager, get_log_manager, get_logger


@pytest.fixture(autouse=True)
def _reset_singleton():
    import overseer_sdk.logger as _mod
    original = _mod._log_manager
    _mod._log_manager = None
    yield
    _mod._log_manager = original


# ------------------------------------------------------------------
# LoggerManager.__init__
# ------------------------------------------------------------------


def test_init_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "new_logs"
    mgr = LoggerManager(log_dir=str(log_dir))
    assert log_dir.is_dir()
    assert mgr.max_bytes == 10_485_760
    assert mgr.backup_count == 5


# ------------------------------------------------------------------
# _normalize_stream
# ------------------------------------------------------------------


def test_normalize_stream_reconfigure() -> None:
    stream = io.StringIO()
    result = LoggerManager._normalize_stream(stream)
    assert result is not None


def test_normalize_stream_fallback_buffer() -> None:
    class FakeStream:
        buffer = io.BytesIO()
    result = LoggerManager._normalize_stream(FakeStream())
    assert result is not None


def test_normalize_stream_no_reconfigure_no_buffer() -> None:
    class Minimal:
        pass
    result = LoggerManager._normalize_stream(Minimal())
    assert isinstance(result, Minimal)


# ------------------------------------------------------------------
# get_logger (manager method)
# ------------------------------------------------------------------


def test_get_logger_creates_logger(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    lgr = mgr.get_logger("test_module")
    assert isinstance(lgr, logging.Logger)
    assert lgr.name == "test_module"
    assert lgr.level == logging.INFO
    assert len(lgr.handlers) == 3  # console + system file + module file


def test_get_logger_returns_cached(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    lgr1 = mgr.get_logger("cached_mod")
    lgr2 = mgr.get_logger("cached_mod")
    assert lgr1 is lgr2


def test_get_logger_custom_level(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    lgr = mgr.get_logger("debug_mod", level=logging.DEBUG)
    assert lgr.level == logging.DEBUG


def test_get_logger_creates_module_log_file(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    mgr = LoggerManager(log_dir=str(log_dir))
    mgr.get_logger("mymod")
    assert (log_dir / "mymod.log").exists()


def test_get_logger_creates_system_log_file(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    mgr = LoggerManager(log_dir=str(log_dir), system_log_name="sys.log")
    mgr.get_logger("anymod")
    assert (log_dir / "sys.log").exists()


def test_get_logger_without_colorlog(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    with patch("overseer_sdk.logger.colorlog", None):
        lgr = mgr.get_logger("plain_mod")
        assert isinstance(lgr, logging.Logger)


def test_get_logger_clears_existing_handlers(tmp_path: Path) -> None:
    lgr = logging.getLogger("pre_existing")
    lgr.addHandler(logging.StreamHandler())
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    result = mgr.get_logger("pre_existing")
    assert result.name == "pre_existing"


# ------------------------------------------------------------------
# create_operation_log
# ------------------------------------------------------------------


def test_create_operation_log(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    mgr.get_logger("op_test")
    log_file = mgr.create_operation_log("deploy")
    assert log_file.exists()
    assert "deploy" in log_file.name


# ------------------------------------------------------------------
# log_operation_summary
# ------------------------------------------------------------------


def test_log_operation_summary(tmp_path: Path) -> None:
    mgr = LoggerManager(log_dir=str(tmp_path / "logs"))
    mgr.log_operation_summary("summary_mod", {"total": 10, "errors": 0})
    lgr = mgr.get_logger("summary_mod")
    assert lgr is not None


# ------------------------------------------------------------------
# Module-level helpers (singleton)
# ------------------------------------------------------------------


def test_get_log_manager_singleton(tmp_path: Path) -> None:
    import overseer_sdk.logger as _mod
    _mod._log_manager = None
    mgr1 = get_log_manager(log_dir=str(tmp_path / "logs"))
    mgr2 = get_log_manager()
    assert mgr1 is mgr2


def test_get_logger_module_level(tmp_path: Path) -> None:
    import overseer_sdk.logger as _mod
    _mod._log_manager = None
    with patch.object(LoggerManager, "__init__", lambda self, **kw: (
        setattr(self, "log_dir", Path(tmp_path / "logs")),
        self.log_dir.mkdir(exist_ok=True),
        setattr(self, "max_bytes", 10_485_760),
        setattr(self, "backup_count", 5),
        setattr(self, "system_log_name", "overseer_system.log"),
        setattr(self, "_loggers", {}),
    )[-1]):
        lgr = get_logger("helper_mod")
        assert isinstance(lgr, logging.Logger)
