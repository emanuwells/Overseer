from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _default_db_url() -> str:
    env_url = os.getenv("DB_URL")
    if env_url:
        return env_url

    # 1) Projeto global
    db_cfg = _load_json(ROOT / "secrets" / "database.json")
    # 2) Fallback por variaveis
    host = os.getenv("PM_DB_HOST", "localhost")
    port = int(os.getenv("PM_DB_PORT", "3306"))
    user = os.getenv("PM_DB_USER", "monitor_user")
    password = os.getenv("PM_DB_PASSWORD", "change-me")
    database = os.getenv("PM_DB_NAME", "monitor_db")
    charset = os.getenv("PM_DB_CHARSET", "utf8mb4")

    if db_cfg:
        db_node = db_cfg.get("database") or {}
        host = db_node.get("host") or host
        port = int(db_node.get("port") or port)
        user = db_node.get("user") or user
        password = db_node.get("password") or password
        database = db_node.get("database") or database
        charset = db_node.get("charset") or charset

    user_q = quote_plus(str(user))
    pass_q = quote_plus(str(password))
    db_q = quote_plus(str(database))
    return f"mysql+pymysql://{user_q}:{pass_q}@{host}:{port}/{db_q}?charset={charset}"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "production")
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost")

    db_url: str = _default_db_url()
    runs_table: str = os.getenv("RUNS_TABLE", "pipeline_runs")

    watermark_sla_minutes: int = int(os.getenv("WATERMARK_SLA_MINUTES", "30"))

    orchestrator_enabled: bool = _as_bool("ORCHESTRATOR_ENABLED", True)
    orchestrator_default_timeout_sec: int = int(os.getenv("ORCHESTRATOR_DEFAULT_TIMEOUT_SEC", "3600"))
    orchestrator_default_retry_max: int = int(os.getenv("ORCHESTRATOR_DEFAULT_RETRY_MAX", "2"))
    orchestrator_default_concurrency: int = int(os.getenv("ORCHESTRATOR_DEFAULT_CONCURRENCY", "1"))


settings = Settings()

