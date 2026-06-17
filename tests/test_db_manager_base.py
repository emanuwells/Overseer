from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from overseer_sdk.db_manager_base import DatabaseManagerBase


class ConcreteDBManager(DatabaseManagerBase):
    """Implementacao concreta minima para testar a base abstracta."""

    def ensure_tables(self) -> None:
        self._execute_update("CREATE TABLE IF NOT EXISTS test (id INT)")


@pytest.fixture()
def manager() -> ConcreteDBManager:
    return ConcreteDBManager(
        host="localhost", port=3306, user="test",
        password="secret", database="testdb",
    )


# ------------------------------------------------------------------
# __init__
# ------------------------------------------------------------------


def test_init_stores_params(manager: ConcreteDBManager) -> None:
    assert manager.host == "localhost"
    assert manager.port == 3306
    assert manager.user == "test"
    assert manager.password == "secret"
    assert manager.database == "testdb"
    assert manager.autocommit is True
    assert manager.connection is None


def test_init_custom_autocommit() -> None:
    mgr = ConcreteDBManager(
        host="h", port=1, user="u", password="p", database="d",
        autocommit=False,
    )
    assert mgr.autocommit is False


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------


def test_default_stats(manager: ConcreteDBManager) -> None:
    stats = manager.get_stats()
    assert stats["records_attempted"] == 0
    assert stats["inserts"] == 0
    assert stats["errors"] == 0


def test_get_stats_returns_copy(manager: ConcreteDBManager) -> None:
    s1 = manager.get_stats()
    s1["inserts"] = 999
    s2 = manager.get_stats()
    assert s2["inserts"] == 0


def test_reset_stats(manager: ConcreteDBManager) -> None:
    manager.stats["errors"] = 5
    manager.reset_stats()
    assert manager.stats["errors"] == 0


# ------------------------------------------------------------------
# connect / disconnect
# ------------------------------------------------------------------


@patch("overseer_sdk.db_manager_base.pymysql.connect")
def test_connect_success(mock_connect: MagicMock, manager: ConcreteDBManager) -> None:
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    manager.connect()

    mock_connect.assert_called_once_with(
        host="localhost", port=3306, user="test",
        password="secret", database="testdb",
        charset="utf8mb4",
        cursorclass=pytest.importorskip("pymysql.cursors").DictCursor,
        autocommit=True,
    )
    assert manager.connection is mock_conn


@patch("overseer_sdk.db_manager_base.pymysql.connect")
def test_connect_failure(mock_connect: MagicMock, manager: ConcreteDBManager) -> None:
    mock_connect.side_effect = RuntimeError("connection refused")
    with pytest.raises(RuntimeError, match="connection refused"):
        manager.connect()


def test_disconnect_with_connection(manager: ConcreteDBManager) -> None:
    mock_conn = MagicMock()
    manager.connection = mock_conn
    manager.disconnect()
    mock_conn.close.assert_called_once()


def test_disconnect_without_connection(manager: ConcreteDBManager) -> None:
    manager.connection = None
    manager.disconnect()  # should not raise


def test_disconnect_handles_close_error(manager: ConcreteDBManager) -> None:
    mock_conn = MagicMock()
    mock_conn.close.side_effect = RuntimeError("close failed")
    manager.connection = mock_conn
    manager.disconnect()  # should not raise


# ------------------------------------------------------------------
# _execute_query / _execute_update
# ------------------------------------------------------------------


def test_execute_query(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    result = manager._execute_query("SELECT * FROM test")
    assert result == [{"id": 1}, {"id": 2}]
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test", None)


def test_execute_query_with_params(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": 1}]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    result = manager._execute_query("SELECT * FROM test WHERE id=%s", (1,))
    assert result == [{"id": 1}]
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id=%s", (1,))


def test_execute_query_raises_on_error(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("query error")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    with pytest.raises(RuntimeError, match="query error"):
        manager._execute_query("BAD SQL")


def test_execute_update(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.execute.return_value = 3
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    affected = manager._execute_update("INSERT INTO test VALUES (%s)", (42,))
    assert affected == 3


def test_execute_update_raises_on_error(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("update error")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    with pytest.raises(RuntimeError, match="update error"):
        manager._execute_update("BAD SQL")


# ------------------------------------------------------------------
# ensure_tables (concrete)
# ------------------------------------------------------------------


def test_ensure_tables(manager: ConcreteDBManager) -> None:
    mock_cursor = MagicMock()
    mock_cursor.execute.return_value = 0
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    manager.connection = mock_conn

    manager.ensure_tables()
    mock_cursor.execute.assert_called_once()


# ------------------------------------------------------------------
# Context manager
# ------------------------------------------------------------------


@patch("overseer_sdk.db_manager_base.pymysql.connect")
def test_context_manager_enter(mock_connect: MagicMock) -> None:
    mock_connect.return_value = MagicMock()
    mgr = ConcreteDBManager(
        host="h", port=1, user="u", password="p", database="d",
    )
    with mgr as ctx:
        assert ctx is mgr
        assert mgr.connection is not None


@patch("overseer_sdk.db_manager_base.pymysql.connect")
def test_context_manager_exit_disconnects(mock_connect: MagicMock) -> None:
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mgr = ConcreteDBManager(
        host="h", port=1, user="u", password="p", database="d",
    )
    with mgr:
        pass
    mock_conn.close.assert_called_once()
