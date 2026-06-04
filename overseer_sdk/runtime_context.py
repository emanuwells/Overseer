"""
RuntimeContext — detecção automática de ambiente de execução.

Singleton que determina hostname, SO, e se o acesso à DB deve ser
via localhost (quando o pipeline corre na própria máquina da DB)
ou via túnel SSH (quando corre remotamente).

Utilização::

    from overseer_sdk.runtime_context import runtime_ctx

    if runtime_ctx.db_is_local:
        db_host, db_port = "localhost", 3306
    else:
        tunnel = SSHTunnelManager(...)
        tunnel.start()
        db_host, db_port = "127.0.0.1", tunnel.local_bind_port

Override via variável de ambiente ``OVERSEER_DB_SSH_MODE``:
    - ``auto``     (default) — detecta pelo hostname/IP
    - ``force``    — força túnel SSH mesmo que esteja no servidor
    - ``disabled`` — nunca usa SSH, acesso directo
"""

from __future__ import annotations

import os
import platform
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, Optional


# IPs / hostnames das máquinas que têm acesso directo à DB.
# Configurar via OVERSEER_DB_LOCAL_HOSTS quando esta detecção for necessária.
_DEFAULT_DB_LOCAL_HOSTS: FrozenSet[str] = frozenset()


def _resolve_local_ips() -> frozenset[str]:
    """Devolve todos os IPs locais da máquina (IPv4)."""
    ips: set[str] = {"127.0.0.1", "::1"}
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ips.add(info[4][0])
    except OSError:
        pass
    return frozenset(ips)


def _check_db_is_local(
    local_ips: frozenset[str],
    db_local_hosts: FrozenSet[str],
    ssh_mode: str,
) -> bool:
    """Determina se a DB é acessível por localhost."""
    mode = ssh_mode.strip().lower()
    if mode == "disabled":
        return True  # nunca usar SSH → acesso directo
    if mode == "force":
        return False  # forçar SSH sempre
    # auto — verificar se algum IP local coincide com os hosts da DB
    return bool(local_ips & db_local_hosts)


@dataclass(frozen=True)
class RuntimeContext:
    """
    Contexto de execução imutável, detectado automaticamente.

    Atributos
    ---------
    hostname : str
        Nome da máquina (``socket.gethostname()``).
    os_name : str
        Sistema operativo (``platform.system()``): ``Windows``, ``Linux``, …
    os_release : str
        Versão do SO (``platform.release()``).
    os_platform : str
        Plataforma completa (``platform.platform()``).
    is_windows : bool
        Atalho para ``os_name == "Windows"``.
    overseer_root : Path
        Raiz do projecto Overseer.
    db_is_local : bool
        Se ``True``, a DB está acessível em ``localhost:3306`` sem túnel SSH.
    db_ssh_mode : str
        Modo SSH configurado: ``auto``, ``force`` ou ``disabled``.
    local_ips : frozenset[str]
        IPs locais detectados na máquina.
    orchestrator_managed : bool
        ``True`` quando o pipeline foi lançado pelo orchestrator.
    """

    hostname: str
    os_name: str
    os_release: str
    os_platform: str
    is_windows: bool
    overseer_root: Path
    db_is_local: bool
    db_ssh_mode: str
    local_ips: frozenset[str] = field(repr=False)
    orchestrator_managed: bool = False

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        overseer_root: Optional[Path] = None,
        db_local_hosts: Optional[FrozenSet[str]] = None,
    ) -> "RuntimeContext":
        """
        Cria um ``RuntimeContext`` com detecção automática de ambiente.

        Parameters
        ----------
        overseer_root :
            Raiz do projecto. Se ``None``, usa a env var ``OVERSEER_ROOT``
            ou calcula 1 nível acima de ``overseer_sdk/``.
        db_local_hosts :
            Conjunto de IPs/hostnames onde a DB corre localmente.
            Default: conjunto vazio, configurável por ``OVERSEER_DB_LOCAL_HOSTS``.
        """
        # Overseer root
        if overseer_root is None:
            env_root = os.getenv("OVERSEER_ROOT")
            if env_root:
                overseer_root = Path(env_root)
            else:
                overseer_root = Path(__file__).resolve().parents[1]

        # DB local hosts
        if db_local_hosts is None:
            env_hosts = os.getenv("OVERSEER_DB_LOCAL_HOSTS")
            if env_hosts:
                db_local_hosts = frozenset(h.strip() for h in env_hosts.split(",") if h.strip())
            else:
                db_local_hosts = _DEFAULT_DB_LOCAL_HOSTS

        # SSH mode
        ssh_mode = os.getenv("OVERSEER_DB_SSH_MODE", "auto").strip().lower()
        if ssh_mode not in {"auto", "force", "disabled"}:
            ssh_mode = "auto"

        # Detectar IPs locais
        local_ips = _resolve_local_ips()

        # Determinar se DB é local
        db_is_local = _check_db_is_local(local_ips, db_local_hosts, ssh_mode)

        # Orchestrator managed
        orchestrator_managed = bool(os.getenv("OVERSEER_ORCHESTRATOR_MANAGED"))

        hn = socket.gethostname()
        os_name = platform.system()

        return RuntimeContext(
            hostname=hn,
            os_name=os_name,
            os_release=platform.release(),
            os_platform=platform.platform(),
            is_windows=(os_name == "Windows"),
            overseer_root=overseer_root,
            db_is_local=db_is_local,
            db_ssh_mode=ssh_mode,
            local_ips=local_ips,
            orchestrator_managed=orchestrator_managed,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def env_export(self) -> dict[str, str]:
        """Devolve dict de variáveis de ambiente para injectar em sub-processos."""
        return {
            "OVERSEER_ROOT": str(self.overseer_root),
            "OVERSEER_HOSTNAME": self.hostname,
            "OVERSEER_OS": self.os_name,
            "OVERSEER_IS_WINDOWS": "1" if self.is_windows else "0",
            "OVERSEER_DB_LOCAL": "1" if self.db_is_local else "0",
            "OVERSEER_DB_SSH_MODE": self.db_ssh_mode,
        }

    def summary(self) -> str:
        """Resumo legível para logs."""
        mode = "localhost (directo)" if self.db_is_local else "SSH tunnel"
        return (
            f"host={self.hostname} os={self.os_name}/{self.os_release} "
            f"db_mode={mode} ssh_override={self.db_ssh_mode} "
            f"overseer_root={self.overseer_root}"
        )


# -----------------------------------------------------------------------
# Singleton — importável directamente
# -----------------------------------------------------------------------

runtime_ctx: RuntimeContext = RuntimeContext.detect()
