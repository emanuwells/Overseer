from __future__ import annotations

import json
import os
import secrets
import socket
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import (
    Boolean,
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


def init_schema() -> None:
    metadata.create_all(get_engine())
    ensure_schema_columns()


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


def normalize_host_id(value: Any) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "")).strip("-")


def resolve_host_id(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("host_id") or "").strip()
    if explicit:
        return normalize_host_id(explicit)
    metadata = payload.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("host_id"):
        return normalize_host_id(metadata["host_id"])
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


def _pipeline_recency_key(row: dict[str, Any]) -> tuple[datetime, int, int]:
    started = parse_dt(row.get("last_started_at")) or datetime.min
    prefers_clean_id = 0 if "__" in str(row.get("pipeline_id") or "") else 1
    has_host = 1 if str(row.get("host_id") or "").strip() else 0
    return (started, prefers_clean_id, has_host)


def dedupe_pipelines(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Uma linha por pipeline lógico (ignora host e sufixos legacy duplicados)."""
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        logical_id = logical_pipeline_id(str(row.get("pipeline_id") or ""))
        if not logical_id:
            continue
        candidate = dict(row)
        candidate["pipeline_id"] = logical_id
        legacy_host = split_legacy_pipeline_id(str(row.get("pipeline_id") or ""))[1]
        if legacy_host and not str(candidate.get("host_id") or "").strip():
            candidate["host_id"] = legacy_host
        current = best.get(logical_id)
        if not current or _pipeline_recency_key(candidate) > _pipeline_recency_key(current):
            best[logical_id] = candidate
    return sorted(best.values(), key=lambda item: item.get("pipeline_id") or "")


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
    if legacy_host and not host_id:
        return logical_id, legacy_host
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
            select(pipelines_table.c.pipeline_id).where(
                (pipelines_table.c.pipeline_id == pipeline_id) & (pipelines_table.c.host_id == host_id)
            )
        ).first()
        if existing:
            conn.execute(
                update(pipelines_table)
                .where(
                    (pipelines_table.c.pipeline_id == pipeline_id) & (pipelines_table.c.host_id == host_id)
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
    return get_pipeline_dag(pipeline_id)


def normalize_runner(value: Any) -> str:
    raw = str(value or "any").strip().lower()
    if raw in {"", "auto", "local", "localhost", "this-host", "self", "*"}:
        return "any"
    return raw


def list_pipelines() -> list[dict[str, Any]]:
    ranked_runs = (
        select(
            runs_table.c.run_id,
            runs_table.c.pipeline_id,
            runs_table.c.host_id,
            runs_table.c.status,
            runs_table.c.started_at,
            runs_table.c.ended_at,
            runs_table.c.duration_sec,
            func.row_number()
            .over(
                partition_by=(runs_table.c.pipeline_id, runs_table.c.host_id),
                order_by=(runs_table.c.started_at.desc(), runs_table.c.run_id.desc()),
            )
            .label("rn"),
        )
    ).subquery()
    stmt = (
        select(
            pipelines_table,
            ranked_runs.c.run_id.label("last_run_id"),
            ranked_runs.c.status.label("last_status"),
            ranked_runs.c.started_at.label("last_started_at"),
            ranked_runs.c.ended_at.label("last_ended_at"),
            ranked_runs.c.duration_sec.label("last_duration_sec"),
        )
        .outerjoin(
            ranked_runs,
            (ranked_runs.c.pipeline_id == pipelines_table.c.pipeline_id)
            & (ranked_runs.c.host_id == pipelines_table.c.host_id)
            & (ranked_runs.c.rn == 1),
        )
        .order_by(pipelines_table.c.pipeline_id, pipelines_table.c.host_id)
    )
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return dedupe_pipelines([row_to_dict(row) for row in rows])


def start_run(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    run_id = str(payload.get("run_id") or new_id("run"))
    pipeline_id, host_id = _resolve_pipeline_host(payload)
    pipeline = get_pipeline(pipeline_id, host_id) or get_pipeline(pipeline_id) or {}
    values = {
        "run_id": run_id,
        "pipeline_id": pipeline_id,
        "host_id": host_id,
        "pipeline_name": payload.get("pipeline_name") or pipeline.get("name") or pipeline_id,
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
    if final_status == "failed" and not existing_meta.get("slack_notified"):
        try:
            from . import slack_alerts

            if slack_alerts.notify_failed_run(finished):
                patch_meta = {**merged_meta, "slack_notified": True}
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


def get_pipeline_dag(pipeline_id: str) -> dict[str, Any]:
    pipeline = get_pipeline(pipeline_id)
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
    return {
        "pipeline": pipeline,
        "nodes": [row_to_dict(row) for row in node_rows],
        "edges": [row_to_dict(row) for row in edge_rows],
    }


def get_run(run_id: str) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(runs_table).where(runs_table.c.run_id == run_id)).mappings().first()
    return row_to_dict(row) if row else None


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
        stmt = stmt.where(runs_table.c.host_id == host_id)
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


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
    runs = list_runs(limit=1000)
    pipelines = list_pipelines()
    total = len(runs)
    running = sum(1 for row in runs if row.get("status") == "running")
    ok = sum(1 for row in runs if row.get("status") == "ok")
    failed = sum(1 for row in runs if row.get("status") == "failed")
    warning = sum(1 for row in runs if row.get("status") == "warning")
    return {
        "generated_at": utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "pipelines": len(pipelines),
            "runs": total,
            "running": running,
            "ok": ok,
            "failed": failed,
            "warning": warning,
            "success_rate": round((ok / total) * 100, 2) if total else 100.0,
        },
        "pipelines": pipelines,
        "recent_runs": runs[:50],
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
