"""Sincronização de runners remotos após alterações ao catálogo (SSH ou subprocess local)."""

from __future__ import annotations

import logging
import os
import shlex
import socket
import subprocess
from pathlib import Path
from typing import Any

import paramiko
import yaml

from .repo_paths import repo_root

logger = logging.getLogger("overseer.runner_ssh")


def ssh_sync_enabled() -> bool:
    return os.getenv("OVERSEER_SSH_SYNC_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def hosts_file(root: Path | None = None) -> Path:
    return runners_hosts_dir(root) / "hosts.yaml"


def runners_hosts_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "deploy" / "runners"


def load_hosts_config(root: Path | None = None) -> dict[str, Any]:
    path = hosts_file(root)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    hosts = data.get("hosts")
    return hosts if isinstance(hosts, dict) else {}


def list_known_hosts(root: Path | None = None) -> list[str]:
    return sorted(load_hosts_config(root).keys())


def get_host_config(host_id: str, root: Path | None = None) -> dict[str, Any]:
    hosts = load_hosts_config(root)
    if host_id not in hosts:
        available = ", ".join(sorted(hosts)) or "(nenhum)"
        raise ValueError(f"host_id desconhecido: {host_id}. Hosts disponíveis: {available}")
    cfg = hosts[host_id]
    if not isinstance(cfg, dict):
        raise ValueError(f"Configuração inválida para host {host_id}")
    return cfg


def is_local_ssh_target(ssh_target: str) -> bool:
    target = (ssh_target or "").strip().lower()
    if target in {"", "localhost", "127.0.0.1", "::1"}:
        return True
    host_part = target.split("@", 1)[-1].lower()
    if host_part in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        local_names = {socket.gethostname().lower(), socket.getfqdn().lower()}
        if host_part in local_names:
            return True
    except Exception:
        pass
    return False


def _run_local(command: str, *, cwd: Path | None = None, timeout: int = 900) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": exc.stdout or "",
            "stderr": f"{exc.stderr or ''}\n(timeout)".strip(),
        }


def _run_ssh(ssh_target: str, command: str, *, timeout: int = 900) -> dict[str, Any]:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    username: str | None = None
    hostname = ssh_target
    if "@" in ssh_target:
        username, hostname = ssh_target.split("@", 1)
    try:
        client.connect(hostname, username=username, timeout=30)
        _, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout.read().decode("utf-8", errors="replace"),
            "stderr": stderr.read().decode("utf-8", errors="replace"),
        }
    finally:
        client.close()


def build_sync_command(
    host_id: str,
    cfg: dict[str, Any],
    *,
    schedule_changed: bool,
) -> str:
    platform = str(cfg.get("platform") or "linux").strip().lower()
    repo_path = str(cfg.get("repo_path") or "").strip()
    catalog_rel = f"deploy/runners/{host_id}.yaml"

    if platform == "windows":
        repo_win = repo_path.rstrip("\\")
        catalog_win = f"{repo_win}\\{catalog_rel.replace('/', chr(92))}"
        commands = [
            f'cd /d "{repo_win}" && git pull',
            (
                f'powershell -NoProfile -ExecutionPolicy Bypass '
                f'-File "{repo_win}\\scripts\\provision-runners.ps1" '
                f'-Register -Catalog "{catalog_win}"'
            ),
        ]
        if schedule_changed:
            commands.append(
                f'powershell -NoProfile -ExecutionPolicy Bypass '
                f'-File "{repo_win}\\scripts\\migrate-taskscheduler.ps1"'
            )
        return " && ".join(commands)

    repo_q = shlex.quote(repo_path)
    prov = f"bash scripts/provision-runners.sh --register --catalog={catalog_rel}"
    if schedule_changed:
        prov += " --crontab"
    return f"cd {repo_q} && git pull && {prov}"


def sync_remote_runner(
    host_id: str,
    *,
    schedule_changed: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    if not ssh_sync_enabled():
        return {
            "enabled": False,
            "host": host_id,
            "skipped": True,
            "reason": "OVERSEER_SSH_SYNC_ENABLED não está activo",
        }

    cfg = get_host_config(host_id, root)
    ssh_target = str(cfg.get("ssh") or "").strip()
    platform = str(cfg.get("platform") or "linux").strip().lower()
    command = build_sync_command(host_id, cfg, schedule_changed=schedule_changed)

    result: dict[str, Any] = {
        "enabled": True,
        "host": host_id,
        "ssh": ssh_target,
        "platform": platform,
        "skipped": False,
    }

    if is_local_ssh_target(ssh_target):
        result["mode"] = "local"
        run = _run_local(command)
    else:
        result["mode"] = "ssh"
        run = _run_ssh(ssh_target, command)

    result["commands"] = [run]
    result["exit_code"] = run.get("exit_code", 1)
    stdout = str(run.get("stdout") or "")
    result["stdout_tail"] = stdout[-2000:] if len(stdout) > 2000 else stdout
    stderr = str(run.get("stderr") or "")
    if stderr:
        result["stderr_tail"] = stderr[-1000:] if len(stderr) > 1000 else stderr
    result["ok"] = result["exit_code"] == 0

    if platform == "windows" and schedule_changed:
        result["schedule_note"] = (
            "Windows: o Task Scheduler pode exigir migrate-taskscheduler.ps1 "
            "para reflectir triggers actualizados."
        )

    if not result["ok"]:
        logger.warning("Sync remoto falhou para %s (exit %s)", host_id, result["exit_code"])
    return result
