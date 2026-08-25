from __future__ import annotations

import json
import os
import secrets
import socket
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import (
    Boolean,
    and_,
    Column,
    DateTime,
    delete,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    inspect,
    insert,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

from overseer_core.repo_paths import repo_root

metadata = MetaData()
_engine: Engine | None = None


pipelines_table = Table(
    "overseer_pipelines",
    metadata,
    Column("pipeline_id", String(128), primary_key=True),
    Column("host_id", String(128), primary_key=True, default=""),
    Column("name", String(255), nullable=False),
    Column("owner", String(128), nullable=False, default="unknown"),
    Column("criticality", String(32), nullable=False, default="medium"),
    Column("schedule", String(128), nullable=False, default="manual"),
    Column("entrypoint", Text, nullable=True),
    Column("runner_host", String(128), nullable=False, default="any"),
    Column("active", Boolean, nullable=False, default=True),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
)

pipeline_nodes_table = Table(
    "overseer_pipeline_nodes",
    metadata,
    Column("pipeline_id", String(128), primary_key=True),
    Column("module_id", String(255), primary_key=True),
    Column("label", String(255), nullable=False),
    Column("type", String(64), nullable=False, default="task"),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
)

pipeline_edges_table = Table(
    "overseer_pipeline_edges",
    metadata,
    Column("pipeline_id", String(128), primary_key=True),
    Column("from_module_id", String(255), primary_key=True),
    Column("to_module_id", String(255), primary_key=True),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

runs_table = Table(
    "overseer_runs",
    metadata,
    Column("run_id", String(128), primary_key=True),
    Column("pipeline_id", String(128), nullable=False, index=True),
    Column("host_id", String(128), nullable=False, default="", index=True),
    Column("pipeline_name", String(255), nullable=True),
    Column("status", String(32), nullable=False, default="running", index=True),
    Column("trigger_type", String(64), nullable=False, default="manual"),
    Column("requested_by", String(128), nullable=True),
    Column("runner_host", String(128), nullable=True),
    Column("hostname", String(255), nullable=True),
    Column("started_at", DateTime, nullable=False),
    Column("ended_at", DateTime, nullable=True),
    Column("duration_sec", Float, nullable=True),
    Column("exit_code", Integer, nullable=True),
    Column("error_message", Text, nullable=True),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("run_local_id", Integer, unique=True, nullable=True, index=True),
)

modules_table = Table(
    "overseer_modules",
    metadata,
    Column("event_id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(128), nullable=False, index=True),
    Column("pipeline_id", String(128), nullable=False, index=True),
    Column("host_id", String(128), nullable=False, default="", index=True),
    Column("module_id", String(255), nullable=False),
    Column("parent_module_id", String(255), nullable=True),
    Column("status", String(32), nullable=False, default="running"),
    Column("started_at", DateTime, nullable=True),
    Column("ended_at", DateTime, nullable=True),
    Column("duration_sec", Float, nullable=True),
    Column("error_message", Text, nullable=True),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

logs_table = Table(
    "overseer_logs",
    metadata,
    Column("log_id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(128), nullable=True, index=True),
    Column("pipeline_id", String(128), nullable=True, index=True),
    Column("host_id", String(128), nullable=True, default="", index=True),
    Column("module_id", String(255), nullable=True),
    Column("level", String(32), nullable=False, default="info"),
    Column("event_type", String(64), nullable=False, default="log"),
    Column("message", Text, nullable=False),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

heartbeats_table = Table(
    "overseer_heartbeats",
    metadata,
    Column("heartbeat_id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", String(255), nullable=False, index=True),
    Column("source_type", String(64), nullable=False, default="runner"),
    Column("pipeline_id", String(128), nullable=True),
    Column("host_id", String(128), nullable=True, default=""),
    Column("run_id", String(128), nullable=True),
    Column("hostname", String(255), nullable=True),
    Column("status", String(32), nullable=False, default="ok"),
    Column("payload_json", Text, nullable=True),
    Column("seen_at", DateTime, nullable=False),
)

triggers_table = Table(
    "overseer_triggers",
    metadata,
    Column("trigger_id", String(128), primary_key=True),
    Column("pipeline_id", String(128), nullable=False, index=True),
    Column("host_id", String(128), nullable=False, default="", index=True),
    Column("trigger_type", String(64), nullable=False, default="run_now"),
    Column("status", String(32), nullable=False, default="queued", index=True),
    Column("requested_by", String(128), nullable=True),
    Column("runner_host", String(128), nullable=False, default="any"),
    Column("payload_json", Text, nullable=True),
    Column("claimed_by", String(128), nullable=True),
    Column("claimed_at", DateTime, nullable=True),
    Column("completed_at", DateTime, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def json_dump(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=str)


def json_load(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(str(value))
    except Exception:
        return None


def _mysql_url_from_env() -> str | None:
    host = os.getenv("OVERSEER_DB_HOST") or os.getenv("P_MONITOR_DB_HOST")
    user = os.getenv("OVERSEER_DB_USER") or os.getenv("P_MONITOR_DB_USER")
    password = os.getenv("OVERSEER_DB_PASSWORD") or os.getenv("P_MONITOR_DB_PASSWORD")
    database = os.getenv("OVERSEER_DB_NAME") or os.getenv("P_MONITOR_DB_NAME")
    if not (host and user and password and database):
        return None
    port = int(os.getenv("OVERSEER_DB_PORT") or os.getenv("P_MONITOR_DB_PORT") or "3306")
    return (
        "mysql+pymysql://"
        f"{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/"
        f"{quote_plus(database)}?charset=utf8mb4"
    )


def get_db_url() -> str:
    return (
        os.getenv("OVERSEER_DB_URL")
        or os.getenv("DB_URL")
        or _mysql_url_from_env()
        or "sqlite:///./runtime/overseer.db"
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        db_url = get_db_url()
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, pool_pre_ping=True, future=True, connect_args=connect_args)
    return _engine


def database_status() -> dict[str, Any]:
    db_url = get_db_url()
    try:
        parsed = make_url(db_url)
        safe_url = parsed.render_as_string(hide_password=True)
        driver = parsed.drivername
        database = parsed.database
        host = parsed.host or "local-file"
        port = parsed.port
    except Exception:
        safe_url = "invalid-url"
        driver = "unknown"
        database = None
        host = None
        port = None

    host_label = str(host or "").lower()
    if host_label == "mysql":
        mode = "docker-local"
    elif host_label in {"127.0.0.1", "localhost", "local-file"}:
        mode = "host-local"
    else:
        mode = "external"

    result: dict[str, Any] = {
        "reachable": False,
        "mode": mode,
        "driver": driver,
        "database": database,
        "host": host,
        "port": port,
        "url": safe_url,
        "tables": {},
        "error": None,
    }
    try:
        with get_engine().connect() as conn:
            result["tables"] = {
                "pipelines": conn.execute(select(func.count()).select_from(pipelines_table)).scalar_one(),
                "pipeline_nodes": conn.execute(select(func.count()).select_from(pipeline_nodes_table)).scalar_one(),
                "pipeline_edges": conn.execute(select(func.count()).select_from(pipeline_edges_table)).scalar_one(),
                "runs": conn.execute(select(func.count()).select_from(runs_table)).scalar_one(),
                "modules": conn.execute(select(func.count()).select_from(modules_table)).scalar_one(),
                "logs": conn.execute(select(func.count()).select_from(logs_table)).scalar_one(),
                "heartbeats": conn.execute(select(func.count()).select_from(heartbeats_table)).scalar_one(),
                "triggers": conn.execute(select(func.count()).select_from(triggers_table)).scalar_one(),
            }
        result["reachable"] = True
    except Exception as exc:
        result["error"] = exc.__class__.__name__
    return result


EXCLUDED_PIPELINE_IDS = frozenset({
    "health_probe",
    "p_monitor_recent",
})

LEGACY_PIPELINE_IDS = EXCLUDED_PIPELINE_IDS | frozenset(
    item.strip()
    for item in os.getenv("OVERSEER_LEGACY_PIPELINE_IDS", "").split(",")
    if item.strip()
)


def is_excluded_pipeline(pipeline_id: str) -> bool:
    return logical_pipeline_id(str(pipeline_id or "").strip()) in EXCLUDED_PIPELINE_IDS


def init_schema() -> None:
    metadata.create_all(get_engine())
    ensure_schema_columns()
    backfill_run_local_ids()
    purge_stuck_running_runs()
    repair_deployment_data()
    deactivate_excluded_pipelines()


def retention_days() -> int:
    raw = os.getenv("OVERSEER_RETENTION_DAYS", "30")
    try:
        value = int(raw)
    except ValueError:
        return 30
    return max(1, value)


def retention_auto_enabled() -> bool:
    return os.getenv("OVERSEER_RETENTION_AUTO", "true").strip().lower() not in {"0", "false", "no", "off"}


def retention_interval_hours() -> float:
    raw = os.getenv("OVERSEER_RETENTION_INTERVAL_HOURS", "24")
    try:
        value = float(raw)
    except ValueError:
        return 24.0
    return max(1.0, value)


def _retention_marker_path() -> Path:
    return repo_root() / "runtime" / ".retention_last_purge"


def auto_purge_retention_if_due(*, force: bool = False) -> dict[str, Any] | None:
    """Purge telemetry older than the retention window (throttled, default daily)."""
    if not retention_auto_enabled() and not force:
        return None

    days = retention_days()
    marker = _retention_marker_path()
    now = utcnow()
    if not force and marker.is_file():
        try:
            last = datetime.fromisoformat(marker.read_text(encoding="utf-8").strip())
            if (now - last).total_seconds() < retention_interval_hours() * 3600:
                return None
        except Exception:
            pass

    result = purge_retention(days, dry_run=False)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(now.isoformat(), encoding="utf-8")
    result["auto"] = True
    return result


def deactivate_excluded_pipelines() -> None:
    """Marca pipelines de teste/sonda como inactivos na DB."""
    if not EXCLUDED_PIPELINE_IDS:
        return
    engine = get_engine()
    if not inspect(engine).has_table("overseer_pipelines"):
        return
    now = utcnow()
    with engine.begin() as conn:
        for pipeline_id in sorted(EXCLUDED_PIPELINE_IDS):
            conn.execute(
                update(pipelines_table)
                .where(
                    or_(
                        pipelines_table.c.pipeline_id == pipeline_id,
                        pipelines_table.c.pipeline_id.like(f"{pipeline_id}__%"),
                    )
                )
                .values(active=False, updated_at=now)
            )


def running_run_max_age_hours() -> float:
    raw = os.getenv("OVERSEER_RUNNING_RUN_MAX_AGE_HOURS", "6")
    try:
        value = float(raw)
    except ValueError:
        return 6.0
    return max(0.0, value)


def purge_stuck_running_runs(
    *,
    max_age_hours: float | None = None,
    pipeline_id: str | None = None,
    host_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, int | bool | float]:
    """Remove runs que ficaram em ``running`` após uma falha de fecho."""

    age_hours = running_run_max_age_hours() if max_age_hours is None else max(0.0, float(max_age_hours))
    cutoff = utcnow() - timedelta(hours=age_hours)
    filters = [
        func.lower(runs_table.c.status) == "running",
        runs_table.c.started_at <= cutoff,
    ]
    if pipeline_id:
        filters.append(runs_table.c.pipeline_id == logical_pipeline_id(str(pipeline_id).strip()))
    if host_id is not None:
        filters.append(runs_table.c.host_id == host_key(host_id))

    with get_engine().connect() as conn:
        run_ids = [
            str(row[0])
            for row in conn.execute(select(runs_table.c.run_id).where(and_(*filters))).all()
        ]
        counts: dict[str, int | bool | float] = {
            "dry_run": dry_run,
            "max_age_hours": age_hours,
            "runs": len(run_ids),
            "modules": 0,
            "logs": 0,
        }
        if not run_ids:
            return counts
        counts["modules"] = int(
            conn.execute(
                select(func.count()).select_from(modules_table).where(modules_table.c.run_id.in_(run_ids))
            ).scalar_one()
        )
        counts["logs"] = int(
            conn.execute(
                select(func.count()).select_from(logs_table).where(logs_table.c.run_id.in_(run_ids))
            ).scalar_one()
        )

    if dry_run:
        return counts

    with get_engine().begin() as conn:
        mod_result = conn.execute(delete(modules_table).where(modules_table.c.run_id.in_(run_ids)))
        log_result = conn.execute(delete(logs_table).where(logs_table.c.run_id.in_(run_ids)))
        run_result = conn.execute(delete(runs_table).where(runs_table.c.run_id.in_(run_ids)))
        counts["modules"] = int(mod_result.rowcount or 0)
        counts["logs"] = int(log_result.rowcount or 0)
        counts["runs"] = int(run_result.rowcount or 0)
    return counts

_HOST_ID_TABLES: dict[str, str] = {
    "overseer_pipelines": "VARCHAR(128) NOT NULL DEFAULT ''",
    "overseer_runs": "VARCHAR(128) NOT NULL DEFAULT ''",
    "overseer_modules": "VARCHAR(128) NOT NULL DEFAULT ''",
    "overseer_logs": "VARCHAR(128) NULL DEFAULT ''",
    "overseer_heartbeats": "VARCHAR(128) NULL DEFAULT ''",
    "overseer_triggers": "VARCHAR(128) NOT NULL DEFAULT ''",
}


def ensure_schema_columns() -> None:
    engine = get_engine()
    inspector = inspect(engine)
    with engine.begin() as conn:
        if inspector.has_table("overseer_pipelines"):
            existing = {column["name"] for column in inspector.get_columns("overseer_pipelines")}
            if "metadata_json" not in existing:
                conn.execute(text("ALTER TABLE overseer_pipelines ADD COLUMN metadata_json TEXT NULL"))
        for table, ddl in _HOST_ID_TABLES.items():
            if not inspector.has_table(table):
                continue
            cols = {column["name"] for column in inspector.get_columns(table)}
            if "host_id" not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN host_id {ddl}"))
        if inspector.has_table("overseer_runs"):
            run_cols = {column["name"] for column in inspector.get_columns("overseer_runs")}
            if "run_local_id" not in run_cols:
                conn.execute(text("ALTER TABLE overseer_runs ADD COLUMN run_local_id INTEGER NULL"))


def backfill_run_local_ids() -> int:
    engine = get_engine()
    if not inspect(engine).has_table("overseer_runs"):
        return 0
    inspector = inspect(engine)
    run_cols = {column["name"] for column in inspector.get_columns("overseer_runs")}
    if "run_local_id" not in run_cols:
        return 0
    updated = 0
    with engine.begin() as conn:
        pending = conn.execute(
            select(runs_table.c.run_id)
            .where(runs_table.c.run_local_id.is_(None))
            .order_by(runs_table.c.started_at.asc(), runs_table.c.created_at.asc())
        ).all()
        if not pending:
            return 0
        next_id = int(conn.execute(select(func.max(runs_table.c.run_local_id))).scalar() or 0) + 1
        for (run_id,) in pending:
            conn.execute(
                update(runs_table)
                .where(runs_table.c.run_id == run_id)
                .values(run_local_id=next_id, updated_at=utcnow())
            )
            next_id += 1
            updated += 1
    return updated


def normalize_host_id(value: Any) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "")).strip("-")


def host_key(value: Any) -> str:
    return normalize_host_id(value).upper()


def effective_host_id(row: dict[str, Any], *, from_run: bool = False) -> str:
    explicit = str(row.get("host_id") or "").strip()
    if explicit:
        return host_key(explicit)
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    if metadata.get("host_id"):
        return host_key(metadata["host_id"])
    _, legacy_host = split_legacy_pipeline_id(str(row.get("pipeline_id") or ""))
    if legacy_host:
        return host_key(legacy_host)
    if from_run:
        hostname = str(row.get("hostname") or "").strip()
        if hostname:
            return host_key(hostname)
    return ""


def resolve_host_id(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("host_id") or "").strip()
    if explicit:
        return host_key(explicit)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if metadata.get("host_id"):
        return host_key(metadata["host_id"])
    hostname = str(payload.get("hostname") or "").strip()
    if hostname:
        return host_key(hostname)
    return ""


def split_legacy_pipeline_id(pipeline_id: str) -> tuple[str, str]:
    if "__" not in pipeline_id:
        return pipeline_id, ""
    logical, _, host = pipeline_id.rpartition("__")
    if logical and host:
        return logical, normalize_host_id(host)
    return pipeline_id, ""


def logical_pipeline_id(pipeline_id: str) -> str:
    logical, _ = split_legacy_pipeline_id(str(pipeline_id or "").strip())
    return logical


def normalize_pipeline_row(row: dict[str, Any], *, from_run: bool = False) -> dict[str, Any] | None:
    """Normaliza pipeline_id lógico e host_id (legacy, metadata ou hostname)."""
    raw_id = str(row.get("pipeline_id") or "").strip()
    logical_id = logical_pipeline_id(raw_id)
    if not logical_id:
        return None
    candidate = dict(row)
    candidate["pipeline_id"] = logical_id
    resolved_host = effective_host_id(row, from_run=from_run)
    if resolved_host:
        candidate["host_id"] = resolved_host
    return candidate


def deployment_key(pipeline_id: str, host_id: str = "") -> str:
    logical_id = logical_pipeline_id(str(pipeline_id or "").strip())
    host = host_key(host_id) if str(host_id or "").strip() else ""
    if not host:
        _, legacy_host = split_legacy_pipeline_id(str(pipeline_id or "").strip())
        host = host_key(legacy_host) if legacy_host else ""
    return f"{logical_id}::{host}"


def deployment_key_from_row(row: dict[str, Any]) -> str:
    normalized = normalize_pipeline_row(row)
    if not normalized:
        return ""
    return deployment_key(
        str(normalized.get("pipeline_id") or ""),
        str(normalized.get("host_id") or ""),
    )


def _pipeline_recency_key(row: dict[str, Any]) -> tuple[datetime, int, int]:
    started = parse_dt(row.get("last_started_at")) or datetime.min
    prefers_clean_id = 0 if "__" in str(row.get("pipeline_id") or "") else 1
    has_host = 1 if str(row.get("host_id") or "").strip() else 0
    return (started, prefers_clean_id, has_host)


def dedupe_pipelines(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Uma linha por deployment (pipeline lógico + host); funde duplicados legacy."""
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = normalize_pipeline_row(row)
        if not candidate:
            continue
        if not str(candidate.get("host_id") or "").strip():
            continue
        key = deployment_key_from_row(candidate)
        current = best.get(key)
        if not current or _pipeline_recency_key(candidate) > _pipeline_recency_key(current):
            best[key] = candidate
    return sorted(
        best.values(),
        key=lambda item: (item.get("pipeline_id") or "", item.get("host_id") or ""),
    )


def repair_deployment_data() -> None:
    """Normaliza catálogo e runs legacy (``__HOST``, host vazio, metadata.host_id)."""
    engine = get_engine()
    if not inspect(engine).has_table("overseer_pipelines"):
        return

    with engine.begin() as conn:
        for row in conn.execute(select(runs_table)).mappings().all():
            data = row_to_dict(row)
            logical_id, legacy_host = split_legacy_pipeline_id(str(data.get("pipeline_id") or ""))
            host = effective_host_id(data, from_run=True) or host_key(legacy_host)
            updates: dict[str, Any] = {}
            if logical_id and logical_id != data.get("pipeline_id"):
                updates["pipeline_id"] = logical_id
            current_host = host_key(data.get("host_id") or "")
            if host and current_host != host:
                updates["host_id"] = host
            if updates:
                conn.execute(
                    update(runs_table)
                    .where(runs_table.c.run_id == data["run_id"])
                    .values(**updates)
                )

        pipe_rows = [row_to_dict(row) for row in conn.execute(select(pipelines_table)).mappings().all()]
        now = utcnow()
        for data in pipe_rows:
            raw_pid = str(data.get("pipeline_id") or "")
            raw_host = str(data.get("host_id") or "")
            logical_id, _ = split_legacy_pipeline_id(raw_pid)
            if raw_pid == logical_id:
                continue
            conn.execute(
                update(pipelines_table)
                .where(
                    (pipelines_table.c.pipeline_id == raw_pid)
                    & (pipelines_table.c.host_id == raw_host)
                )
                .values(active=False, updated_at=now)
            )
            conn.execute(delete(pipeline_nodes_table).where(pipeline_nodes_table.c.pipeline_id == raw_pid))
            conn.execute(delete(pipeline_edges_table).where(pipeline_edges_table.c.pipeline_id == raw_pid))

        for data in pipe_rows:
            raw_pid = str(data.get("pipeline_id") or "")
            raw_host = str(data.get("host_id") or "")
            logical_id, _ = split_legacy_pipeline_id(raw_pid)
            if raw_pid != logical_id:
                continue
            host = effective_host_id(data)
            if host and not raw_host:
                conn.execute(
                    update(pipelines_table)
                    .where(
                        (pipelines_table.c.pipeline_id == raw_pid)
                        & (pipelines_table.c.host_id == raw_host)
                    )
                    .values(host_id=host, updated_at=now)
                )


def new_id(prefix: str) -> str:
    return f"{prefix}-{int(time.time())}-{secrets.token_hex(4)}"


def normalize_status(value: str | None, *, running: bool = False) -> str:
    raw = str(value or ("running" if running else "ok")).strip().lower()
    if raw in {"ok", "success", "sucesso", "done", "completed"}:
        return "ok"
    if raw in {"warning", "warn", "parcial"}:
        return "warning"
    if raw in {"running", "started", "claimed"}:
        return "running"
    if raw in {"queued"}:
        return "queued"
    return "failed"


def row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key in ("metadata_json", "payload_json"):
        if key in data:
            data[key.removesuffix("_json")] = json_load(data.pop(key))
    for key, value in list(data.items()):
        if isinstance(value, datetime):
            data[key] = value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return data


def _resolve_pipeline_host(payload: dict[str, Any]) -> tuple[str, str]:
    pipeline_id = str(payload["pipeline_id"]).strip()
    host_id = resolve_host_id(payload)
    logical_id, legacy_host = split_legacy_pipeline_id(pipeline_id)
    if legacy_host:
        return logical_id, host_id or host_key(legacy_host)
    return pipeline_id, host_id


def register_pipeline_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    pipeline_id, host_id = _resolve_pipeline_host(payload)
    values = {
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "name": str(payload.get("name") or pipeline_id),
        "owner": str(payload.get("owner") or "unknown"),
        "criticality": str(payload.get("criticality") or "medium").lower(),
        "schedule": str(payload.get("schedule") or "manual"),
        "entrypoint": None,
        "runner_host": normalize_runner(payload.get("runner_host")),
        "active": True,
        "metadata_json": json_dump(payload.get("metadata") or {}),
        "created_at": now,
        "updated_at": now,
    }
    nodes = payload.get("nodes") or []
    edges = payload.get("edges") or []
    with get_engine().begin() as conn:
        existing = conn.execute(
            select(pipelines_table.c.pipeline_id, pipelines_table.c.host_id).where(
                (pipelines_table.c.pipeline_id == pipeline_id) & (pipelines_table.c.host_id == host_id)
            )
        ).first()
        if not existing:
            legacy = conn.execute(
                select(pipelines_table.c.pipeline_id, pipelines_table.c.host_id).where(
                    pipelines_table.c.pipeline_id == pipeline_id
                )
            ).first()
            if legacy:
                existing = legacy
        update_host_id = host_id
        if existing:
            legacy_host = str(getattr(existing, "host_id", None) or existing.get("host_id") if isinstance(existing, dict) else getattr(existing, "host_id", "") or "")
            if legacy_host:
                update_host_id = legacy_host
            current = get_pipeline(pipeline_id, update_host_id) or get_pipeline(pipeline_id, host_id)
            if current:
                for field in PATCHABLE_CATALOG_FIELDS:
                    db_val = current.get(field)
                    if db_val is not None and str(db_val).strip():
                        values[field] = db_val
                cur_meta = current.get("metadata")
                if not isinstance(cur_meta, dict):
                    cur_meta = json_load(current.get("metadata_json")) or {}
                yaml_meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
                merged_meta = dict(cur_meta)
                if yaml_meta.get("host_id"):
                    merged_meta["host_id"] = yaml_meta["host_id"]
                if yaml_meta.get("prev_schedule") and not merged_meta.get("prev_schedule"):
                    merged_meta["prev_schedule"] = yaml_meta["prev_schedule"]
                values["metadata_json"] = json_dump(merged_meta)
            conn.execute(
                update(pipelines_table)
                .where(
                    (pipelines_table.c.pipeline_id == pipeline_id)
                    & (pipelines_table.c.host_id == update_host_id)
                )
                .values(**{k: v for k, v in values.items() if k != "created_at"})
            )
        else:
            conn.execute(insert(pipelines_table).values(**values))

        conn.execute(delete(pipeline_nodes_table).where(pipeline_nodes_table.c.pipeline_id == pipeline_id))
        conn.execute(delete(pipeline_edges_table).where(pipeline_edges_table.c.pipeline_id == pipeline_id))

        for node in nodes:
            conn.execute(
                insert(pipeline_nodes_table).values(
                    pipeline_id=pipeline_id,
                    module_id=str(node["module_id"]).strip(),
                    label=str(node.get("label") or node["module_id"]),
                    type=str(node.get("type") or "task"),
                    metadata_json=json_dump(node.get("metadata") or {}),
                    created_at=now,
                    updated_at=now,
                )
            )
        for edge in edges:
            conn.execute(
                insert(pipeline_edges_table).values(
                    pipeline_id=pipeline_id,
                    from_module_id=str(edge["from_module_id"]).strip(),
                    to_module_id=str(edge["to_module_id"]).strip(),
                    metadata_json=json_dump(edge.get("metadata") or {}),
                    created_at=now,
                )
            )
    return get_pipeline_dag(pipeline_id, host_id)


PATCHABLE_CATALOG_FIELDS = ("name", "owner", "criticality", "schedule", "runner_host")


def patch_pipeline_catalog(pipeline_id: str, host_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    logical_id = logical_pipeline_id(pipeline_id)
    host_id = host_key(host_id)
    if not host_id:
        raise ValueError("host_id é obrigatório para PATCH de catálogo.")
    if not get_pipeline(logical_id, host_id):
        repair_deployment_data()
    if not get_pipeline(logical_id, host_id):
        ensure_pipeline_in_catalog(logical_id, host_id)
    if not get_pipeline(logical_id, host_id):
        raise ValueError(f"Pipeline não encontrado: {logical_id}@{host_id}")
    pipeline_id = logical_id

    current = get_pipeline(pipeline_id, host_id) or {}
    current_meta = current.get("metadata") if isinstance(current.get("metadata"), dict) else json_load(current.get("metadata_json"))
    if not isinstance(current_meta, dict):
        current_meta = {}

    updates: dict[str, Any] = {}
    meta_updates: dict[str, Any] = {}
    for key in PATCHABLE_CATALOG_FIELDS:
        if key not in fields or fields[key] is None:
            continue
        if key == "runner_host":
            updates[key] = normalize_runner(fields[key])
        elif key == "criticality":
            updates[key] = str(fields[key]).strip().lower()
        else:
            updates[key] = str(fields[key]).strip()

    if "schedule" in updates:
        from . import runner_catalog

        entry = {
            "schedule": current.get("schedule") or "manual",
            "prev_schedule": current_meta.get("prev_schedule") or current.get("prev_schedule"),
        }
        schedule_patch = runner_catalog.resolve_schedule_patch(entry, updates["schedule"])
        updates["schedule"] = schedule_patch["schedule"]
        if "prev_schedule" in schedule_patch:
            if schedule_patch["prev_schedule"] is None:
                meta_updates["prev_schedule"] = None
            else:
                meta_updates["prev_schedule"] = schedule_patch["prev_schedule"]

    if "suspended" in fields and fields["suspended"] is not None:
        if fields["suspended"]:
            meta_updates["suspended"] = True
        else:
            meta_updates["suspended"] = None

    if not updates and not meta_updates:
        return get_pipeline_dag(pipeline_id, host_id)

    if meta_updates:
        merged_meta = dict(current_meta)
        for meta_key, meta_val in meta_updates.items():
            if meta_val is None:
                merged_meta.pop(meta_key, None)
            else:
                merged_meta[meta_key] = meta_val
        updates["metadata_json"] = json_dump(merged_meta)

    updates["updated_at"] = utcnow()
    with get_engine().begin() as conn:
        conn.execute(
            update(pipelines_table)
            .where(
                (pipelines_table.c.pipeline_id == pipeline_id) & (pipelines_table.c.host_id == host_id)
            )
            .values(**updates)
        )
    return get_pipeline_dag(pipeline_id, host_id)


def normalize_runner(value: Any) -> str:
    raw = str(value or "any").strip().lower()
    if raw in {"", "auto", "local", "localhost", "this-host", "self", "*"}:
        return "any"
    return raw


def _latest_runs_by_deployment() -> dict[str, dict[str, Any]]:
    latest_runs: dict[str, dict[str, Any]] = {}
    for run in list_runs(limit=5000):
        normalized = normalize_pipeline_row(run, from_run=True)
        if not normalized:
            continue
        key = deployment_key_from_row(normalized)
        if not key:
            continue
        current = latest_runs.get(key)
        started = parse_dt(run.get("started_at")) or datetime.min
        if not current or started > (parse_dt(current.get("started_at")) or datetime.min):
            latest_runs[key] = run
    return latest_runs


def _catalog_payload_from_yaml_entry(entry: dict[str, Any], host_db: str, catalog_host: str) -> dict[str, Any]:
    pipeline_id = str(entry["pipeline_id"])
    steps = entry.get("steps") if isinstance(entry.get("steps"), list) else []
    nodes: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        module_id = str(step.get("module_id") or "").strip()
        if not module_id:
            continue
        meta: dict[str, Any] = {}
        if step.get("command"):
            meta["command"] = step["command"]
        if step.get("cwd"):
            meta["cwd"] = step["cwd"]
        if "critical" in step:
            meta["critical"] = bool(step["critical"])
        if step.get("description"):
            meta["description"] = str(step["description"])
        nodes.append(
            {
                "module_id": module_id,
                "label": str(step.get("label") or module_id),
                "metadata": meta,
            }
        )
    edges: list[dict[str, Any]] = []
    has_explicit_deps = False
    node_ids = {node["module_id"] for node in nodes}
    for step in steps:
        if not isinstance(step, dict):
            continue
        module_id = str(step.get("module_id") or "").strip()
        if not module_id:
            continue
        raw_deps = step.get("depends_on")
        if raw_deps is None:
            continue
        dep_list = [str(raw_deps)] if isinstance(raw_deps, str) else [str(d) for d in raw_deps if d]
        for dep in dep_list:
            if dep in node_ids and dep != module_id:
                edges.append({"from_module_id": dep, "to_module_id": module_id})
                has_explicit_deps = True
    if not has_explicit_deps:
        edges = [
            {
                "from_module_id": nodes[i]["module_id"],
                "to_module_id": nodes[i + 1]["module_id"],
            }
            for i in range(len(nodes) - 1)
        ]
    return {
        "pipeline_id": pipeline_id,
        "host_id": host_db,
        "name": str(entry.get("name") or pipeline_id),
        "owner": str(entry.get("owner") or "data"),
        "criticality": str(entry.get("criticality") or "medium").lower(),
        "schedule": str(entry.get("schedule") or "manual"),
        "metadata": {
            "host_id": catalog_host,
            **({"prev_schedule": str(entry["prev_schedule"])} if entry.get("prev_schedule") else {}),
            **(
                {"inventory_globs": [str(item) for item in entry["inventory_globs"] if item]}
                if isinstance(entry.get("inventory_globs"), list)
                else {}
            ),
        },
        "nodes": nodes,
        "edges": edges,
    }


def ensure_pipeline_in_catalog(pipeline_id: str, host_id: str) -> bool:
    """Regista na DB a partir do YAML se o deployment ainda não existir."""
    from . import runner_catalog

    logical_id = logical_pipeline_id(pipeline_id)
    host_db = host_key(host_id)
    if not host_db:
        return False
    if get_pipeline(logical_id, host_db):
        return True
    entry = runner_catalog.catalog_entry_for(host_id, logical_id)
    if not entry:
        return False
    catalog_host = str(entry.get("catalog_host") or host_id)
    register_pipeline_catalog(_catalog_payload_from_yaml_entry(entry, host_db, catalog_host))
    return True


def reconcile_catalog_from_yaml() -> dict[str, Any]:
    """Regista na DB os pipelines definidos no diretório de runners configurado."""
    from . import runner_catalog

    created: list[dict[str, str]] = []
    updated: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    hosts: list[str] = []

    for catalog_host, entries in runner_catalog.load_all_runner_catalogs().items():
        hosts.append(catalog_host)
        host_db = host_key(catalog_host)
        for entry in entries:
            pipeline_id = str(entry["pipeline_id"])
            payload = _catalog_payload_from_yaml_entry(entry, host_db, catalog_host)
            existing = find_pipeline_catalog(pipeline_id, host_db)
            if not existing:
                register_pipeline_catalog(payload)
                created.append({"pipeline_id": pipeline_id, "host_id": host_db})
                continue
            register_pipeline_catalog(payload)
            updated.append({"pipeline_id": pipeline_id, "host_id": host_db})

    exported = runner_catalog.export_catalog_from_db()
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "hosts": sorted(set(hosts)),
        "exported": exported,
    }


def list_deployments() -> list[dict[str, Any]]:
    """Vista unificada: YAML + DB + telemetria (runs)."""
    from . import runner_catalog

    latest_runs = _latest_runs_by_deployment()
    defaults = {"owner": "data", "criticality": "medium", "schedule": "manual"}
    merged: dict[str, dict[str, Any]] = {}

    for catalog_host, entries in runner_catalog.load_all_runner_catalogs().items():
        host_id = host_key(catalog_host)
        for entry in entries:
            pipeline_id = str(entry["pipeline_id"])
            key = deployment_key(pipeline_id, host_id)
            item = merged.setdefault(
                key,
                {
                    "pipeline_id": pipeline_id,
                    "host_id": host_id,
                    "catalog_source": "yaml",
                    "catalog_host": catalog_host,
                },
            )
            if entry.get("name"):
                item["name"] = str(entry["name"])
            if entry.get("owner"):
                item["owner"] = str(entry["owner"])
            if entry.get("schedule"):
                item["schedule"] = str(entry["schedule"])
            if entry.get("prev_schedule"):
                item["prev_schedule"] = str(entry["prev_schedule"])
            if entry.get("criticality"):
                item["criticality"] = str(entry["criticality"]).lower()

    with get_engine().connect() as conn:
        pipeline_rows = conn.execute(
            select(pipelines_table).where(pipelines_table.c.active.is_(True))
        ).mappings().all()

    for row in pipeline_rows:
        normalized = normalize_pipeline_row(row_to_dict(row))
        if not normalized or not str(normalized.get("host_id") or "").strip():
            continue
        key = deployment_key_from_row(normalized)
        item = merged.setdefault(
            key,
            {
                "pipeline_id": normalized["pipeline_id"],
                "host_id": normalized["host_id"],
                "catalog_source": "runs_only",
            },
        )
        had_yaml = str(item.get("catalog_source") or "") == "yaml"
        yaml_schedule = str(item.get("schedule") or "").strip() if had_yaml else ""
        item["catalog_source"] = "db"
        for field in ("name", "owner", "schedule", "criticality", "runner_host", "metadata", "active"):
            if field not in normalized or normalized[field] is None:
                continue
            if field == "schedule":
                db_schedule = str(normalized[field]).strip()
                if (
                    had_yaml
                    and yaml_schedule
                    and yaml_schedule.lower() not in {"", "manual"}
                    and db_schedule.lower() == "manual"
                ):
                    continue
            item[field] = normalized[field]

    for key, run in latest_runs.items():
        normalized = normalize_pipeline_row(run, from_run=True)
        if not normalized or not str(normalized.get("host_id") or "").strip():
            continue
        if key in merged:
            continue
        merged[key] = {
            "pipeline_id": normalized["pipeline_id"],
            "host_id": normalized["host_id"],
            "name": str(run.get("pipeline_name") or normalized["pipeline_id"]),
            "catalog_source": "runs_only",
        }

    from . import deployment_health, runner_ssh

    runs_by_deployment = deployment_health.group_runs_by_deployment(list_runs(limit=5000))
    hosts_cfg = runner_ssh.load_hosts_config()
    enriched: list[dict[str, Any]] = []
    for key, item in merged.items():
        if is_excluded_pipeline(str(item.get("pipeline_id") or "")):
            continue
        for field, value in defaults.items():
            item.setdefault(field, value)
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        if meta.get("suspended"):
            item["suspended"] = True
        elif "suspended" not in item:
            item["suspended"] = False
        if not item.get("name"):
            item["name"] = item["pipeline_id"]
        catalog_host = str(item.get("catalog_host") or item.get("host_id") or "")
        try:
            canonical = runner_ssh.resolve_catalog_host_id(catalog_host)
            host_cfg = hosts_cfg.get(canonical) if isinstance(hosts_cfg.get(canonical), dict) else {}
            item["runner_platform"] = str(host_cfg.get("platform") or "")
        except ValueError:
            item["runner_platform"] = ""
        latest = latest_runs.get(key)
        if latest:
            item["last_run_id"] = latest.get("run_id")
            item["last_status"] = latest.get("status")
            item["last_started_at"] = latest.get("started_at")
            item["last_ended_at"] = latest.get("ended_at")
            item["last_duration_sec"] = latest.get("duration_sec")
        enriched.append(
            deployment_health.enrich_deployment(item, runs_by_deployment.get(key, []))
        )
    from . import pipeline_names

    result = dedupe_pipelines(enriched)
    catalog_index = pipeline_names.build_catalog_name_index(result) or _build_catalog_name_index_light()
    return [pipeline_names.normalize_pipeline_item(item, catalog_index) for item in result]


def _build_catalog_name_index_light() -> dict[str, str]:
    """Índice de nomes a partir de YAML + DB (sem depender de list_deployments)."""
    from . import pipeline_names, runner_catalog

    candidates: list[dict[str, Any]] = []
    for catalog_host, entries in runner_catalog.load_all_runner_catalogs().items():
        host_id = host_key(catalog_host)
        for entry in entries:
            candidates.append(
                {
                    "pipeline_id": str(entry["pipeline_id"]),
                    "host_id": host_id,
                    "name": entry.get("name"),
                }
            )
    with get_engine().connect() as conn:
        pipeline_rows = conn.execute(
            select(pipelines_table).where(pipelines_table.c.active.is_(True))
        ).mappings().all()
    for row in pipeline_rows:
        normalized = normalize_pipeline_row(row_to_dict(row))
        if normalized:
            candidates.append(normalized)
    return pipeline_names.build_catalog_name_index(candidates)


def catalog_name_index() -> dict[str, str]:
    return _build_catalog_name_index_light()


def list_pipelines() -> list[dict[str, Any]]:
    return list_deployments()


def previous_completed_run(
    pipeline_id: str,
    host_id: str = "",
    *,
    exclude_run_id: str = "",
) -> dict[str, Any] | None:
    """Última run terminada antes da run actual (ignora running)."""
    for run in list_runs(limit=50, pipeline_id=pipeline_id, host_id=host_id or None):
        if exclude_run_id and str(run.get("run_id") or "") == exclude_run_id:
            continue
        if str(run.get("status") or "").lower() == "running":
            continue
        return run
    return None


def start_run(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    run_id = str(payload.get("run_id") or new_id("run"))
    pipeline_id, host_id = _resolve_pipeline_host(payload)
    purge_stuck_running_runs(pipeline_id=pipeline_id, host_id=host_id)
    pipeline = get_pipeline(pipeline_id, host_id) or get_pipeline(pipeline_id) or {}
    from . import pipeline_names

    catalog_index = _build_catalog_name_index_light()
    pipeline_name = pipeline_names.resolve_display_name(
        pipeline_id,
        host_id,
        str(pipeline.get("name") or payload.get("pipeline_name") or pipeline_id),
        catalog_index,
    )
    values = {
        "run_id": run_id,
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "pipeline_name": pipeline_name,
        "status": "running",
        "trigger_type": payload.get("trigger_type") or "manual",
        "requested_by": payload.get("requested_by"),
        "runner_host": payload.get("runner_host") or pipeline.get("runner_host") or "any",
        "hostname": payload.get("hostname") or socket.gethostname(),
        "started_at": parse_dt(payload.get("started_at")) or now,
        "metadata_json": json_dump(payload.get("metadata")),
        "created_at": now,
        "updated_at": now,
    }
    with get_engine().begin() as conn:
        next_local = int(conn.execute(select(func.max(runs_table.c.run_local_id))).scalar() or 0) + 1
        values["run_local_id"] = next_local
        conn.execute(insert(runs_table).values(**values))
    return get_run(run_id) or {"run_id": run_id}


def finish_run(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    run = get_run(run_id) or {}
    started = parse_dt(run.get("started_at"))
    ended = parse_dt(payload.get("ended_at")) or now
    duration = payload.get("duration_sec")
    if duration is None and started:
        duration = max(0.0, (ended - started).total_seconds())
    existing_meta = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    incoming_meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    merged_meta = {**existing_meta, **incoming_meta}
    final_status = normalize_status(payload.get("status"))
    with get_engine().begin() as conn:
        conn.execute(
            update(runs_table)
            .where(runs_table.c.run_id == run_id)
            .values(
                status=final_status,
                ended_at=ended,
                duration_sec=duration,
                exit_code=payload.get("exit_code"),
                error_message=payload.get("error_message"),
                metadata_json=json_dump(merged_meta),
                updated_at=now,
            )
        )
    finished = get_run(run_id) or {"run_id": run_id}
    pipeline_id = str(finished.get("pipeline_id") or "")
    host_id = str(finished.get("host_id") or "")
    try:
        from . import slack_alerts

        if final_status == "failed" and not existing_meta.get("slack_notified"):
            alert_number = slack_alerts.failure_alert_number(finished)
            if alert_number is not None and slack_alerts.notify_failed_run(
                finished,
                alert_number=alert_number,
            ):
                patch_meta = {
                    **merged_meta,
                    "slack_notified": True,
                    "slack_alert_number": alert_number,
                }
                with get_engine().begin() as conn:
                    conn.execute(
                        update(runs_table)
                        .where(runs_table.c.run_id == run_id)
                        .values(metadata_json=json_dump(patch_meta), updated_at=utcnow())
                    )
                finished = get_run(run_id) or finished

        if final_status == "ok" and not existing_meta.get("slack_resolved_notified"):
            prev_failed = previous_completed_run(
                pipeline_id,
                host_id,
                exclude_run_id=run_id,
            )
            if prev_failed and str(prev_failed.get("status") or "").lower() == "failed":
                if slack_alerts.notify_resolved_run(finished, prev_failed):
                    patch_meta = {**merged_meta, "slack_resolved_notified": True}
                    with get_engine().begin() as conn:
                        conn.execute(
                            update(runs_table)
                            .where(runs_table.c.run_id == run_id)
                            .values(metadata_json=json_dump(patch_meta), updated_at=utcnow())
                        )
                    finished = get_run(run_id) or finished
    except Exception:
        pass
    return finished


def purge_pipeline_data(
    pipeline_id: str,
    *,
    deactivate: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    logical_id = logical_pipeline_id(str(pipeline_id or "").strip())
    if not logical_id:
        raise ValueError("pipeline_id is required")

    pipeline_filter = or_(
        runs_table.c.pipeline_id == logical_id,
        runs_table.c.pipeline_id.like(f"{logical_id}__%"),
    )
    with get_engine().connect() as conn:
        run_ids = [
            str(row[0])
            for row in conn.execute(select(runs_table.c.run_id).where(pipeline_filter)).all()
        ]

    counts = {
        "pipeline_id": logical_id,
        "runs": len(run_ids),
        "modules": 0,
        "logs": 0,
        "deactivated": False,
        "dry_run": dry_run,
    }
    if not run_ids:
        if deactivate and not dry_run:
            with get_engine().begin() as conn:
                result = conn.execute(
                    update(pipelines_table)
                    .where(
                        or_(
                            pipelines_table.c.pipeline_id == logical_id,
                            pipelines_table.c.pipeline_id.like(f"{logical_id}__%"),
                        )
                    )
                    .values(active=False, updated_at=utcnow())
                )
                counts["deactivated"] = bool(result.rowcount)
        return counts

    if dry_run:
        with get_engine().connect() as conn:
            counts["modules"] = int(
                conn.execute(
                    select(func.count()).select_from(modules_table).where(modules_table.c.run_id.in_(run_ids))
                ).scalar_one()
            )
            counts["logs"] = int(
                conn.execute(
                    select(func.count()).select_from(logs_table).where(logs_table.c.run_id.in_(run_ids))
                ).scalar_one()
            )
        return counts

    with get_engine().begin() as conn:
        mod_result = conn.execute(delete(modules_table).where(modules_table.c.run_id.in_(run_ids)))
        log_result = conn.execute(delete(logs_table).where(logs_table.c.run_id.in_(run_ids)))
        run_result = conn.execute(delete(runs_table).where(runs_table.c.run_id.in_(run_ids)))
        counts["modules"] = int(mod_result.rowcount or 0)
        counts["logs"] = int(log_result.rowcount or 0)
        counts["runs"] = int(run_result.rowcount or 0)
        if deactivate:
            pipe_result = conn.execute(
                update(pipelines_table)
                .where(
                    or_(
                        pipelines_table.c.pipeline_id == logical_id,
                        pipelines_table.c.pipeline_id.like(f"{logical_id}__%"),
                    )
                )
                .values(active=False, updated_at=utcnow())
            )
            counts["deactivated"] = bool(pipe_result.rowcount)
    return counts


def purge_retention(
    days: int = 30,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove telemetry older than ``days``. Catalog rows are preserved."""
    if days < 1:
        raise ValueError("days must be >= 1")
    cutoff = utcnow() - timedelta(days=days)
    counts: dict[str, Any] = {
        "days": days,
        "cutoff": cutoff.isoformat(),
        "dry_run": dry_run,
        "runs": 0,
        "modules": 0,
        "logs": 0,
        "triggers": 0,
        "heartbeats": 0,
    }

    with get_engine().connect() as conn:
        run_ids = [
            str(row[0])
            for row in conn.execute(
                select(runs_table.c.run_id).where(runs_table.c.started_at < cutoff)
            ).all()
        ]
        counts["runs"] = len(run_ids)

        if run_ids:
            counts["modules"] = int(
                conn.execute(
                    select(func.count()).select_from(modules_table).where(modules_table.c.run_id.in_(run_ids))
                ).scalar_one()
            )
            counts["logs"] = int(
                conn.execute(
                    select(func.count()).select_from(logs_table).where(logs_table.c.run_id.in_(run_ids))
                ).scalar_one()
            )

        counts["triggers"] = int(
            conn.execute(
                select(func.count()).select_from(triggers_table).where(triggers_table.c.created_at < cutoff)
            ).scalar_one()
        )
        counts["heartbeats"] = int(
            conn.execute(
                select(func.count()).select_from(heartbeats_table).where(heartbeats_table.c.seen_at < cutoff)
            ).scalar_one()
        )

    if dry_run:
        return counts

    with get_engine().begin() as conn:
        if run_ids:
            mod_result = conn.execute(delete(modules_table).where(modules_table.c.run_id.in_(run_ids)))
            log_result = conn.execute(delete(logs_table).where(logs_table.c.run_id.in_(run_ids)))
            run_result = conn.execute(delete(runs_table).where(runs_table.c.run_id.in_(run_ids)))
            counts["modules"] = int(mod_result.rowcount or 0)
            counts["logs"] = int(log_result.rowcount or 0)
            counts["runs"] = int(run_result.rowcount or 0)

        trig_result = conn.execute(delete(triggers_table).where(triggers_table.c.created_at < cutoff))
        hb_result = conn.execute(delete(heartbeats_table).where(heartbeats_table.c.seen_at < cutoff))
        counts["triggers"] = int(trig_result.rowcount or 0)
        counts["heartbeats"] = int(hb_result.rowcount or 0)

    return counts


def purge_legacy_pipelines(*, dry_run: bool = False) -> dict[str, Any]:
    """Purge runs/modules/logs and deactivate known legacy pipeline catalog rows."""
    summary: dict[str, Any] = {"dry_run": dry_run, "pipelines": {}}
    for pipeline_id in sorted(LEGACY_PIPELINE_IDS):
        summary["pipelines"][pipeline_id] = purge_pipeline_data(
            pipeline_id,
            deactivate=True,
            dry_run=dry_run,
        )
    return summary


LEGACY_DROP_TABLES = frozenset(
    {
        "logs_archive",
        "medidata_indicator_records_raw",
        "medidata_scrape_runs",
        "orchestrator_events_local",
        "orchestrator_runs_local",
        "orchestrator_steps_local",
        "orchestrator_triggers_local",
        "overseer_alert_events",
        "overseer_alert_state",
        "overseer_runners",
        "pipeline_catalog",
        "pipeline_module_events",
        "pipeline_runs",
        "pipeline_script_logs",
    }
)

GOVERNANCE_TABLES = frozenset(
    {
        "overseer_identity_mappings",
        "overseer_identity_mapping_requests",
        "overseer_permission_requests",
        "overseer_pipeline_permissions",
    }
)

CANONICAL_TABLES = frozenset(
    {
        "overseer_pipelines",
        "overseer_pipeline_nodes",
        "overseer_pipeline_edges",
        "overseer_runs",
        "overseer_modules",
        "overseer_logs",
        "overseer_heartbeats",
        "overseer_triggers",
    }
)


def _quote_table(name: str) -> str:
    safe = str(name).replace("`", "")
    return f"`{safe}`"


def drop_legacy_tables(*, dry_run: bool = True) -> dict[str, Any]:
    """Drop pre-Overseer schema tables that are no longer read by the API."""
    engine = get_engine()
    existing = set(inspect(engine).get_table_names())
    to_drop = sorted(LEGACY_DROP_TABLES & existing)
    result: dict[str, Any] = {
        "dry_run": dry_run,
        "would_drop": to_drop,
        "dropped": [],
        "absent": sorted(LEGACY_DROP_TABLES - existing),
        "row_counts": {},
    }
    with engine.connect() as conn:
        for table in to_drop:
            result["row_counts"][table] = int(
                conn.execute(text(f"SELECT COUNT(*) FROM {_quote_table(table)}")).scalar_one()
            )
    if dry_run:
        return result
    with engine.begin() as conn:
        for table in to_drop:
            conn.execute(text(f"DROP TABLE {_quote_table(table)}"))
            result["dropped"].append(table)
    result["would_drop"] = []
    return result


def record_module(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    started = parse_dt(payload.get("started_at"))
    ended = parse_dt(payload.get("ended_at"))
    duration = payload.get("duration_sec")
    if duration is None and started and ended:
        duration = max(0.0, (ended - started).total_seconds())
    pipeline_id, host_id = _resolve_pipeline_host(payload)
    values = {
        "run_id": payload["run_id"],
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "module_id": payload["module_id"],
        "parent_module_id": payload.get("parent_module_id"),
        "status": normalize_status(payload.get("status"), running=ended is None),
        "started_at": started or now,
        "ended_at": ended,
        "duration_sec": duration,
        "error_message": payload.get("error_message"),
        "metadata_json": json_dump(payload.get("metadata")),
        "created_at": now,
    }
    with get_engine().begin() as conn:
        result = conn.execute(insert(modules_table).values(**values))
        event_id = result.inserted_primary_key[0]
    return get_module(int(event_id)) or {"event_id": event_id}


def record_log(payload: dict[str, Any]) -> dict[str, Any]:
    now = parse_dt(payload.get("created_at")) or utcnow()
    if payload.get("pipeline_id"):
        pipeline_id, host_id = _resolve_pipeline_host(payload)
    else:
        pipeline_id, host_id = None, resolve_host_id(payload)
    values = {
        "run_id": payload.get("run_id"),
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "module_id": payload.get("module_id"),
        "level": str(payload.get("level") or "info").lower(),
        "event_type": str(payload.get("event_type") or "log"),
        "message": str(payload.get("message") or ""),
        "metadata_json": json_dump(payload.get("metadata")),
        "created_at": now,
    }
    with get_engine().begin() as conn:
        result = conn.execute(insert(logs_table).values(**values))
        log_id = result.inserted_primary_key[0]
    return get_log(int(log_id)) or {"log_id": log_id}


def record_heartbeat(payload: dict[str, Any]) -> dict[str, Any]:
    now = parse_dt(payload.get("seen_at")) or utcnow()
    host_id = resolve_host_id(payload)
    if not host_id and payload.get("pipeline_id"):
        _, legacy_host = split_legacy_pipeline_id(str(payload["pipeline_id"]))
        host_id = legacy_host
    values = {
        "source_id": payload.get("source_id") or payload.get("hostname") or socket.gethostname(),
        "source_type": payload.get("source_type") or "runner",
        "pipeline_id": payload.get("pipeline_id"),
        "host_id": host_id,
        "run_id": payload.get("run_id"),
        "hostname": payload.get("hostname") or socket.gethostname(),
        "status": normalize_status(payload.get("status")),
        "payload_json": json_dump(payload.get("payload")),
        "seen_at": now,
    }
    with get_engine().begin() as conn:
        result = conn.execute(insert(heartbeats_table).values(**values))
        heartbeat_id = result.inserted_primary_key[0]
    return get_heartbeat(int(heartbeat_id)) or {"heartbeat_id": heartbeat_id}


def enqueue_trigger(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    trigger_id = str(payload.get("trigger_id") or new_id("trg"))
    pipeline_id, host_id = _resolve_pipeline_host(payload)
    values = {
        "trigger_id": trigger_id,
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "trigger_type": payload.get("trigger_type") or "run_now",
        "status": "queued",
        "requested_by": payload.get("requested_by"),
        "runner_host": normalize_runner(payload.get("runner_host")),
        "payload_json": json_dump(payload.get("payload")),
        "created_at": now,
        "updated_at": now,
    }
    with get_engine().begin() as conn:
        conn.execute(insert(triggers_table).values(**values))
    return get_trigger(trigger_id) or {"trigger_id": trigger_id}


def claim_trigger(trigger_id: str, claimed_by: str | None = None) -> dict[str, Any] | None:
    now = utcnow()
    with get_engine().begin() as conn:
        conn.execute(
            update(triggers_table)
            .where((triggers_table.c.trigger_id == trigger_id) & (triggers_table.c.status == "queued"))
            .values(status="claimed", claimed_by=claimed_by or socket.gethostname(), claimed_at=now, updated_at=now)
        )
    return get_trigger(trigger_id)


def complete_trigger(trigger_id: str, status: str = "done") -> dict[str, Any] | None:
    now = utcnow()
    with get_engine().begin() as conn:
        conn.execute(
            update(triggers_table)
            .where(triggers_table.c.trigger_id == trigger_id)
            .values(status=normalize_status(status), completed_at=now, updated_at=now)
        )
    return get_trigger(trigger_id)


def get_pipeline(pipeline_id: str, host_id: str = "") -> dict[str, Any] | None:
    stmt = select(pipelines_table).where(pipelines_table.c.pipeline_id == pipeline_id)
    if host_id:
        stmt = stmt.where(pipelines_table.c.host_id == host_id)
    with get_engine().connect() as conn:
        row = conn.execute(stmt).mappings().first()
    return row_to_dict(row) if row else None


def find_pipeline_catalog(pipeline_id: str, host_id: str = "") -> dict[str, Any] | None:
    """Resolve catálogo por deployment; em PK legacy só por ``pipeline_id``."""
    logical_id = logical_pipeline_id(pipeline_id)
    host_db = host_key(host_id) if host_id else ""
    row = get_pipeline(logical_id, host_db) if host_db else None
    if row:
        return row
    if host_db:
        row = get_pipeline(logical_id, "")
        if row:
            return row
    with get_engine().connect() as conn:
        legacy = conn.execute(
            select(pipelines_table).where(pipelines_table.c.pipeline_id == logical_id)
        ).mappings().first()
    return row_to_dict(legacy) if legacy else None


def get_pipeline_dag(
    pipeline_id: str,
    host_id: str = "",
    *,
    include_inventory: bool = False,
) -> dict[str, Any]:
    pipeline = get_pipeline(pipeline_id, host_id)
    with get_engine().connect() as conn:
        node_rows = conn.execute(
            select(pipeline_nodes_table)
            .where(pipeline_nodes_table.c.pipeline_id == pipeline_id)
            .order_by(pipeline_nodes_table.c.module_id)
        ).mappings().all()
        edge_rows = conn.execute(
            select(pipeline_edges_table)
            .where(pipeline_edges_table.c.pipeline_id == pipeline_id)
            .order_by(pipeline_edges_table.c.from_module_id, pipeline_edges_table.c.to_module_id)
        ).mappings().all()
    nodes = [row_to_dict(row) for row in node_rows]
    inventory_nodes: list[dict[str, Any]] = []
    if include_inventory:
        from . import pipeline_inventory

        inventory_nodes = pipeline_inventory.discover_inventory_nodes(pipeline, nodes)
    return {
        "pipeline": pipeline,
        "nodes": nodes + inventory_nodes,
        "edges": [row_to_dict(row) for row in edge_rows],
        "inventory_count": len(inventory_nodes),
    }


def get_run(run_id: str) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(runs_table).where(runs_table.c.run_id == run_id)).mappings().first()
    if not row:
        return None
    from . import pipeline_names

    return pipeline_names.normalize_run_item(row_to_dict(row), _build_catalog_name_index_light())


def get_module(event_id: int) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(modules_table).where(modules_table.c.event_id == event_id)).mappings().first()
    return row_to_dict(row) if row else None


def get_log(log_id: int) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(logs_table).where(logs_table.c.log_id == log_id)).mappings().first()
    return row_to_dict(row) if row else None


def get_heartbeat(heartbeat_id: int) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(
            select(heartbeats_table).where(heartbeats_table.c.heartbeat_id == heartbeat_id)
        ).mappings().first()
    return row_to_dict(row) if row else None


def get_trigger(trigger_id: str) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(triggers_table).where(triggers_table.c.trigger_id == trigger_id)).mappings().first()
    return row_to_dict(row) if row else None


def list_runs(
    limit: int = 200,
    pipeline_id: str | None = None,
    host_id: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(runs_table).order_by(runs_table.c.started_at.desc()).limit(max(1, min(limit, 1000)))
    if pipeline_id:
        stmt = stmt.where(runs_table.c.pipeline_id == pipeline_id)
    if host_id is not None:
        stmt = stmt.where(runs_table.c.host_id == host_key(host_id))
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    from . import pipeline_names

    catalog_index = _build_catalog_name_index_light()
    return [pipeline_names.normalize_run_item(row_to_dict(row), catalog_index) for row in rows]


def list_runs_since(days: float = 7, limit: int = 5000) -> list[dict[str, Any]]:
    cutoff = utcnow() - timedelta(days=max(0.0, days))
    stmt = (
        select(runs_table)
        .where(runs_table.c.started_at >= cutoff)
        .order_by(runs_table.c.started_at.desc())
        .limit(max(1, min(limit, 5000)))
    )
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    from . import pipeline_names

    catalog_index = _build_catalog_name_index_light()
    return [pipeline_names.normalize_run_item(row_to_dict(row), catalog_index) for row in rows]


def count_runs() -> int:
    with get_engine().connect() as conn:
        total = conn.execute(select(func.count()).select_from(runs_table)).scalar()
    return int(total or 0)


def oldest_run_started_at() -> datetime | None:
    with get_engine().connect() as conn:
        value = conn.execute(select(func.min(runs_table.c.started_at))).scalar()
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return parse_dt(value)


def telemetry_since_label() -> str | None:
    oldest = oldest_run_started_at()
    return oldest.strftime("%Y-%m-%d") if oldest else None


def count_runs_since(days: float = 7, *, failed_only: bool = False) -> int:
    cutoff = utcnow() - timedelta(days=max(0.0, days))
    stmt = select(func.count()).select_from(runs_table).where(runs_table.c.started_at >= cutoff)
    if failed_only:
        stmt = stmt.where(func.lower(runs_table.c.status).in_(("failed", "nok", "error")))
    with get_engine().connect() as conn:
        total = conn.execute(stmt).scalar()
    return int(total or 0)


def list_modules(run_id: str | None = None, pipeline_id: str | None = None) -> list[dict[str, Any]]:
    stmt = select(modules_table).order_by(modules_table.c.created_at.desc()).limit(1000)
    if run_id:
        stmt = stmt.where(modules_table.c.run_id == run_id)
    if pipeline_id:
        stmt = stmt.where(modules_table.c.pipeline_id == pipeline_id)
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


def list_logs(run_id: str | None = None, pipeline_id: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    stmt = select(logs_table).order_by(logs_table.c.created_at.desc()).limit(max(1, min(limit, 2000)))
    if run_id:
        stmt = stmt.where(logs_table.c.run_id == run_id)
    if pipeline_id:
        stmt = stmt.where(logs_table.c.pipeline_id == pipeline_id)
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


def list_heartbeats(limit: int = 200) -> list[dict[str, Any]]:
    stmt = select(heartbeats_table).order_by(heartbeats_table.c.seen_at.desc()).limit(max(1, min(limit, 1000)))
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


def list_triggers(limit: int = 200) -> list[dict[str, Any]]:
    stmt = select(triggers_table).order_by(triggers_table.c.created_at.desc()).limit(max(1, min(limit, 1000)))
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


def overview() -> dict[str, Any]:
    from . import deployment_health

    runs = list_runs(limit=1000)
    runs_7d = list_runs_since(days=7, limit=5000)
    pipelines = list_pipelines()
    summary = deployment_health.build_operational_summary(
        runs,
        pipelines,
        total_runs=count_runs(),
        runs_7d=runs_7d,
        failed_7d=count_runs_since(7, failed_only=True),
        since_label=telemetry_since_label(),
        retention_days=retention_days(),
    )
    return {
        "generated_at": utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": summary,
        "pipelines": pipelines,
        "recent_runs": runs[:200],
        "heartbeats": list_heartbeats(limit=50),
        "triggers": list_triggers(limit=50),
    }


def parse_dt(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def persist_lineage_markers(*, run_id: str, pipeline_id: str, output: str) -> None:
    starts: dict[str, float] = {}
    for line in str(output or "").splitlines():
        if not line.startswith("@@OVERSEER_MODULE@@"):
            continue
        raw = line.removeprefix("@@OVERSEER_MODULE@@")
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        module_id = str(payload.get("module_id") or "").strip()
        if not module_id:
            continue
        event = str(payload.get("event") or "").lower()
        if event == "start":
            starts[module_id] = time.monotonic()
            continue
        if event != "end":
            continue
        status = payload.get("status") or "ok"
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        duration = context.get("duration_sec") if isinstance(context, dict) else None
        if duration is None and module_id in starts:
            duration = max(0.0, time.monotonic() - starts[module_id])
        record_module(
            {
                "run_id": run_id,
                "pipeline_id": pipeline_id,
                "module_id": module_id,
                "parent_module_id": payload.get("parent_module_id"),
                "status": status,
                "duration_sec": duration,
                "error_message": payload.get("message") if normalize_status(status) == "failed" else None,
                "metadata": {
                    "message": payload.get("message"),
                    "critical": payload.get("critical", True),
                    "context": context,
                    "source": "stdout-marker",
                },
            }
        )
