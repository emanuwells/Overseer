"""
Gestor de Túnel SSH partilhado para todos os pipelines Overseer.

Wraps ``sshtunnel.SSHTunnelForwarder`` com validação de chave,
logging centralizado e suporte a context-manager.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from sshtunnel import SSHTunnelForwarder
import paramiko


logger = logging.getLogger("overseer_sdk.ssh_tunnel")


class SSHTunnelManager:
    """
    Gestor de túnel SSH para conexão segura ao servidor de base de dados.
    Suporta autenticação por chave SSH.
    """

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_user: str,
        ssh_key_path: str,
        remote_bind_host: str = "localhost",
        remote_bind_port: int = 3306,
    ):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_key_path = Path(ssh_key_path)
        self.remote_bind_host = remote_bind_host
        self.remote_bind_port = remote_bind_port

        self.tunnel: Optional[SSHTunnelForwarder] = None
        self.local_bind_port: Optional[int] = None

        self._validate_key()

    # ------------------------------------------------------------------

    def _validate_key(self) -> None:
        if not self.ssh_key_path.exists():
            logger.error("Chave SSH não encontrada: %s", self.ssh_key_path)
            raise FileNotFoundError(f"Chave SSH não existe: {self.ssh_key_path}")

        try:
            paramiko.RSAKey.from_private_key_file(str(self.ssh_key_path))
            logger.debug("Chave SSH validada: %s", self.ssh_key_path)
        except Exception as exc:
            logger.error("Chave SSH inválida: %s", exc)
            raise ValueError(f"Chave SSH inválida: {exc}") from exc

    # ------------------------------------------------------------------

    def start(self) -> int:
        """Inicia o túnel SSH. Devolve a porta local atribuída."""
        if self.tunnel and self.tunnel.is_active:
            logger.warning("Túnel SSH já está ativo")
            return self.local_bind_port  # type: ignore[return-value]

        logger.info(
            "A estabelecer túnel SSH para %s@%s:%s",
            self.ssh_user, self.ssh_host, self.ssh_port,
        )

        self.tunnel = SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_pkey=str(self.ssh_key_path),
            remote_bind_address=(self.remote_bind_host, self.remote_bind_port),
            set_keepalive=30.0,
        )
        self.tunnel.start()
        self.local_bind_port = self.tunnel.local_bind_port

        logger.info(
            "Túnel SSH estabelecido: localhost:%s -> %s:%s",
            self.local_bind_port, self.remote_bind_host, self.remote_bind_port,
        )
        return self.local_bind_port

    def stop(self) -> None:
        """Encerra o túnel SSH."""
        if self.tunnel and self.tunnel.is_active:
            try:
                self.tunnel.stop()
                logger.info("Túnel SSH encerrado")
            except Exception as exc:
                logger.error("Erro ao encerrar túnel SSH: %s", exc)
        else:
            logger.debug("Túnel SSH já estava inativo")

    def is_active(self) -> bool:
        return self.tunnel is not None and self.tunnel.is_active

    def get_local_port(self) -> Optional[int]:
        return self.local_bind_port if self.is_active() else None

    # -- context manager -----------------------------------------------

    def __enter__(self) -> "SSHTunnelManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        self.stop()

    def __del__(self) -> None:
        try:
            self.stop()
        except Exception:
            pass
