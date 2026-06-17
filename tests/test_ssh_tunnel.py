from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from overseer_sdk.ssh_tunnel import SSHTunnelManager


@pytest.fixture()
def valid_key(tmp_path: Path) -> Path:
    key_path = tmp_path / "id_rsa"
    key_path.write_text("fake-key-content")
    return key_path


# ------------------------------------------------------------------
# __init__ / _validate_key
# ------------------------------------------------------------------


def test_init_key_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="SSH"):
        SSHTunnelManager(
            ssh_host="host", ssh_port=22, ssh_user="user",
            ssh_key_path=str(tmp_path / "missing"),
        )


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_init_invalid_key(mock_rsa: MagicMock, valid_key: Path) -> None:
    mock_rsa.side_effect = Exception("bad key format")
    with pytest.raises(ValueError, match="inv"):
        SSHTunnelManager(
            ssh_host="host", ssh_port=22, ssh_user="user",
            ssh_key_path=str(valid_key),
        )


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_init_valid_key(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="dbhost", ssh_port=22, ssh_user="deploy",
        ssh_key_path=str(valid_key),
    )
    assert mgr.ssh_host == "dbhost"
    assert mgr.ssh_port == 22
    assert mgr.ssh_user == "deploy"
    assert mgr.tunnel is None
    assert mgr.local_bind_port is None
    assert mgr.remote_bind_host == "localhost"
    assert mgr.remote_bind_port == 3306


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_init_custom_remote(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="dbhost", ssh_port=2222, ssh_user="deploy",
        ssh_key_path=str(valid_key),
        remote_bind_host="db.internal", remote_bind_port=5432,
    )
    assert mgr.remote_bind_host == "db.internal"
    assert mgr.remote_bind_port == 5432


# ------------------------------------------------------------------
# start / stop
# ------------------------------------------------------------------


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
@patch("overseer_sdk.ssh_tunnel.SSHTunnelForwarder")
def test_start_creates_tunnel(mock_forwarder: MagicMock, mock_rsa: MagicMock, valid_key: Path) -> None:
    tunnel_instance = MagicMock()
    tunnel_instance.local_bind_port = 54321
    tunnel_instance.is_active = True
    mock_forwarder.return_value = tunnel_instance

    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    port = mgr.start()

    assert port == 54321
    assert mgr.local_bind_port == 54321
    tunnel_instance.start.assert_called_once()


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
@patch("overseer_sdk.ssh_tunnel.SSHTunnelForwarder")
def test_start_returns_existing_port_if_active(mock_forwarder: MagicMock, mock_rsa: MagicMock, valid_key: Path) -> None:
    tunnel_instance = MagicMock()
    tunnel_instance.is_active = True
    tunnel_instance.local_bind_port = 11111
    mock_forwarder.return_value = tunnel_instance

    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    mgr.tunnel = tunnel_instance
    mgr.local_bind_port = 11111

    port = mgr.start()
    assert port == 11111
    tunnel_instance.start.assert_not_called()


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_stop_active_tunnel(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    tunnel_mock = MagicMock()
    tunnel_mock.is_active = True
    mgr.tunnel = tunnel_mock

    mgr.stop()
    tunnel_mock.stop.assert_called_once()


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_stop_inactive_tunnel(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    mgr.tunnel = None
    mgr.stop()  # should not raise


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_stop_handles_exception(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    tunnel_mock = MagicMock()
    tunnel_mock.is_active = True
    tunnel_mock.stop.side_effect = RuntimeError("cleanup error")
    mgr.tunnel = tunnel_mock

    mgr.stop()  # should not raise


# ------------------------------------------------------------------
# is_active / get_local_port
# ------------------------------------------------------------------


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_is_active_true(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    tunnel_mock = MagicMock()
    tunnel_mock.is_active = True
    mgr.tunnel = tunnel_mock
    assert mgr.is_active() is True


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_is_active_false_no_tunnel(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    assert mgr.is_active() is False


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_get_local_port_active(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    tunnel_mock = MagicMock()
    tunnel_mock.is_active = True
    mgr.tunnel = tunnel_mock
    mgr.local_bind_port = 9999
    assert mgr.get_local_port() == 9999


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
def test_get_local_port_inactive(mock_rsa: MagicMock, valid_key: Path) -> None:
    mgr = SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    )
    mgr.local_bind_port = 9999
    assert mgr.get_local_port() is None


# ------------------------------------------------------------------
# context manager
# ------------------------------------------------------------------


@patch("overseer_sdk.ssh_tunnel.paramiko.RSAKey.from_private_key_file")
@patch("overseer_sdk.ssh_tunnel.SSHTunnelForwarder")
def test_context_manager(mock_forwarder: MagicMock, mock_rsa: MagicMock, valid_key: Path) -> None:
    tunnel_instance = MagicMock()
    tunnel_instance.local_bind_port = 12345
    tunnel_instance.is_active = True
    mock_forwarder.return_value = tunnel_instance

    with SSHTunnelManager(
        ssh_host="host", ssh_port=22, ssh_user="user",
        ssh_key_path=str(valid_key),
    ) as mgr:
        assert mgr.local_bind_port == 12345

    tunnel_instance.stop.assert_called()
