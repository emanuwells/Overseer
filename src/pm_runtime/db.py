from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


_engine: Engine | None = None
_db_url: str | None = None
_ssh_tunnel: Any | None = None
ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_ssh_key_path(raw_value: str) -> Path:
    candidate = Path(raw_value)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    if candidate.exists():
        return candidate.resolve()

    static_candidates = [
        ROOT / "secrets" / raw_value,
        ROOT / raw_value,
    ]
    for item in static_candidates:
        if item.exists():
            return item.resolve()

    for pipeline_secret in (ROOT / "pipelines").glob(f"*/secrets/{raw_value}"):
        if pipeline_secret.exists():
            return pipeline_secret.resolve()

    raise FileNotFoundError(f"Chave SSH nao encontrada: {raw_value}")


def _build_mysql_url(host: str, port: int, user: str, password: str, database: str, charset: str) -> str:
    user_q = quote_plus(str(user))
    pass_q = quote_plus(str(password))
    db_q = quote_plus(str(database))
    return f"mysql+pymysql://{user_q}:{pass_q}@{host}:{port}/{db_q}?charset={charset}"


def _stop_ssh_tunnel() -> None:
    global _ssh_tunnel
    if _ssh_tunnel is not None and _ssh_tunnel.is_active:
        _ssh_tunnel.stop()
    _ssh_tunnel = None


def _build_db_url() -> str:
    global _ssh_tunnel
    env_url = os.getenv("DB_URL")
    if env_url:
        return env_url

    cfg = _load_json(ROOT / "secrets" / "database.json")
    db_cfg = cfg.get("database") or {}
    ssh_cfg = cfg.get("ssh") or {}

    host = str(db_cfg.get("host") or "localhost")
    port = int(db_cfg.get("port") or 3306)
    user = str(db_cfg.get("user") or "monitor_user")
    password = str(db_cfg.get("password") or "change-me")
    database = str(db_cfg.get("database") or "monitor_db")
    charset = str(db_cfg.get("charset") or "utf8mb4")

    if ssh_cfg:
        try:
            from sshtunnel import SSHTunnelForwarder
        except Exception as exc:
            raise RuntimeError("Pacote 'sshtunnel' em falta. Instala com: .\\.venv\\Scripts\\python.exe -m pip install sshtunnel") from exc

        ssh_host = str(ssh_cfg.get("host") or "").strip()
        ssh_user = str(ssh_cfg.get("user") or "").strip()
        ssh_key_name = str(ssh_cfg.get("key_filename") or "ssh_key").strip()
        if not ssh_host or not ssh_user:
            raise RuntimeError("Bloco ssh em secrets/database.json exige host e user.")

        key_path = _resolve_ssh_key_path(ssh_key_name)
        remote_bind_host = str(ssh_cfg.get("remote_bind_host") or "localhost")
        remote_bind_port = int(ssh_cfg.get("remote_bind_port") or 3306)
        ssh_port = int(ssh_cfg.get("port") or 22)

        _ssh_tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_pkey=str(key_path),
            remote_bind_address=(remote_bind_host, remote_bind_port),
            local_bind_address=("127.0.0.1", 0),
        )
        _ssh_tunnel.start()
        atexit.register(_stop_ssh_tunnel)

        host = "127.0.0.1"
        port = int(_ssh_tunnel.local_bind_port)

    return _build_mysql_url(host, port, user, password, database, charset)


def get_db_url() -> str:
    global _db_url
    if _db_url is None:
        _db_url = _build_db_url()
    return _db_url


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_db_url(), pool_pre_ping=True, future=True)
    return _engine
