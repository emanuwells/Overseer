from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import yaml
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

ROOT = Path(__file__).resolve().parents[2]
PIPELINES_DIR = ROOT / "pipelines"
HOST_PIPELINES_DIR = ROOT / "host_pipelines"

metadata = MetaData()
_engine: Engine | None = None


pipelines_table = Table(
    "overseer_pipelines",
    metadata,
    Column("pipeline_id", String(128), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("owner", String(128), nullable=False, default="unknown"),
    Column("criticality", String(32), nullable=False, default="medium"),
    Column("schedule", String(128), nullable=False, default="manual"),
    Column("entrypoint", Text, nullable=True),
    Column("runner_host", String(128), nullable=False, default="any"),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow),
)

runs_table = Table(
    "overseer_runs",
    metadata,
    Column("run_id", String(128), primary_key=True),
    Column("pipeline_id", String(128), nullable=False, index=True),
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
    Column("event_id", BigInteger, primary_key=True, autoincrement=True),
    Column("run_id", String(128), nullable=False, index=True),
    Column("pipeline_id", String(128), nullable=False, index=True),
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
    Column("log_id", BigInteger, primary_key=True, autoincrement=True),
    Column("run_id", String(128), nullable=True, index=True),
    Column("pipeline_id", String(128), nullable=True, index=True),
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
    Column("heartbeat_id", BigInteger, primary_key=True, autoincrement=True),
    Column("source_id", String(255), nullable=False, index=True),
    Column("source_type", String(64), nullable=False, default="runner"),
    Column("pipeline_id", String(128), nullable=True),
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
    sync_pipeline_catalog()


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


def pipeline_dirs() -> list[Path]:
    raw_dirs = [PIPELINES_DIR, HOST_PIPELINES_DIR]
    extra = os.getenv("OVERSEER_PIPELINES_DIR")
    if extra:
        raw_dirs.extend(Path(item.strip()) for item in extra.split(os.pathsep) if item.strip())
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in raw_dirs:
        resolved = path.resolve() if path.exists() else path
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique


def iter_pipeline_yamls() -> list[tuple[Path, dict[str, Any]]]:
    items: list[tuple[Path, dict[str, Any]]] = []
    seen_pipeline_ids: set[str] = set()
    for directory in pipeline_dirs():
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*/pipeline.yaml")):
            if path.parent.name.startswith("_"):
                continue
            try:
                payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            pipeline_id = str(payload.get("pipeline_id") or "").strip()
            if pipeline_id and pipeline_id not in seen_pipeline_ids:
                items.append((path, payload))
                seen_pipeline_ids.add(pipeline_id)
    return items


def sync_pipeline_catalog() -> None:
    now = utcnow()
    with get_engine().begin() as conn:
        for path, payload in iter_pipeline_yamls():
            pipeline_id = str(payload.get("pipeline_id")).strip()
            values = {
                "pipeline_id": pipeline_id,
                "name": str(payload.get("name") or pipeline_id),
                "owner": str(payload.get("owner") or "unknown"),
                "criticality": str(payload.get("criticality") or "medium").lower(),
                "schedule": str(payload.get("schedule") or "manual"),
                "entrypoint": str(payload.get("entrypoint_windows") if os.name == "nt" else payload.get("entrypoint") or ""),
                "runner_host": normalize_runner(payload.get("runner_host")),
                "active": True,
                "created_at": now,
                "updated_at": now,
            }
            existing = conn.execute(
                select(pipelines_table.c.pipeline_id).where(pipelines_table.c.pipeline_id == pipeline_id)
            ).first()
            if existing:
                conn.execute(
                    update(pipelines_table)
                    .where(pipelines_table.c.pipeline_id == pipeline_id)
                    .values(**{k: v for k, v in values.items() if k != "created_at"})
                )
            else:
                conn.execute(insert(pipelines_table).values(**values))


def normalize_runner(value: Any) -> str:
    raw = str(value or "any").strip().lower()
    if raw in {"", "auto", "local", "localhost", "this-host", "self", "*"}:
        return "any"
    return raw


def list_pipelines() -> list[dict[str, Any]]:
    sync_pipeline_catalog()
    latest = (
        select(runs_table.c.pipeline_id, func.max(runs_table.c.started_at).label("latest_at"))
        .group_by(runs_table.c.pipeline_id)
        .subquery()
    )
    stmt = (
        select(
            pipelines_table,
            runs_table.c.run_id.label("last_run_id"),
            runs_table.c.status.label("last_status"),
            runs_table.c.started_at.label("last_started_at"),
            runs_table.c.ended_at.label("last_ended_at"),
        )
        .outerjoin(latest, latest.c.pipeline_id == pipelines_table.c.pipeline_id)
        .outerjoin(
            runs_table,
            (runs_table.c.pipeline_id == latest.c.pipeline_id)
            & (runs_table.c.started_at == latest.c.latest_at),
        )
        .order_by(pipelines_table.c.pipeline_id)
    )
    with get_engine().connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [row_to_dict(row) for row in rows]


def start_run(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    run_id = str(payload.get("run_id") or new_id("run"))
    pipeline_id = str(payload["pipeline_id"]).strip()
    pipeline = get_pipeline(pipeline_id) or {}
    values = {
        "run_id": run_id,
        "pipeline_id": pipeline_id,
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
    with get_engine().begin() as conn:
        conn.execute(
            update(runs_table)
            .where(runs_table.c.run_id == run_id)
            .values(
                status=normalize_status(payload.get("status")),
                ended_at=ended,
                duration_sec=duration,
                exit_code=payload.get("exit_code"),
                error_message=payload.get("error_message"),
                metadata_json=json_dump(payload.get("metadata")),
                updated_at=now,
            )
        )
    return get_run(run_id) or {"run_id": run_id}


def record_module(payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    started = parse_dt(payload.get("started_at"))
    ended = parse_dt(payload.get("ended_at"))
    duration = payload.get("duration_sec")
    if duration is None and started and ended:
        duration = max(0.0, (ended - started).total_seconds())
    values = {
        "run_id": payload["run_id"],
        "pipeline_id": payload["pipeline_id"],
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
    values = {
        "run_id": payload.get("run_id"),
        "pipeline_id": payload.get("pipeline_id"),
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
    values = {
        "source_id": payload.get("source_id") or payload.get("hostname") or socket.gethostname(),
        "source_type": payload.get("source_type") or "runner",
        "pipeline_id": payload.get("pipeline_id"),
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
    values = {
        "trigger_id": trigger_id,
        "pipeline_id": payload["pipeline_id"],
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


def get_pipeline(pipeline_id: str) -> dict[str, Any] | None:
    sync_pipeline_catalog()
    with get_engine().connect() as conn:
        row = conn.execute(
            select(pipelines_table).where(pipelines_table.c.pipeline_id == pipeline_id)
        ).mappings().first()
    return row_to_dict(row) if row else None


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


def list_runs(limit: int = 200, pipeline_id: str | None = None) -> list[dict[str, Any]]:
    stmt = select(runs_table).order_by(runs_table.c.started_at.desc()).limit(max(1, min(limit, 1000)))
    if pipeline_id:
        stmt = stmt.where(runs_table.c.pipeline_id == pipeline_id)
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


def run_pipeline_subprocess(pipeline_id: str, requested_by: str = "api") -> dict[str, Any]:
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        raise ValueError("pipeline_id inexistente.")
    entrypoint = str(pipeline.get("entrypoint") or "").strip()
    if not entrypoint:
        raise ValueError("Pipeline sem entrypoint.")

    run = start_run(
        {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.get("name"),
            "requested_by": requested_by,
            "trigger_type": "api",
            "runner_host": socket.gethostname(),
            "metadata": {"source": "orchestrate-api"},
        }
    )
    run_id = run["run_id"]
    record_log({"run_id": run_id, "pipeline_id": pipeline_id, "level": "info", "message": f"A executar: {entrypoint}"})

    env = os.environ.copy()
    env["OVERSEER_RUN_ID"] = run_id
    env["OVERSEER_PIPELINE_ID"] = pipeline_id
    env["OVERSEER_API_URL"] = env.get("OVERSEER_API_URL", "http://127.0.0.1:8090")
    workdir = PIPELINES_DIR / pipeline_id
    if not workdir.exists():
        for directory in pipeline_dirs():
            candidate = directory / pipeline_id
            if candidate.exists():
                workdir = candidate
                break
    started = time.monotonic()
    try:
        proc = subprocess.run(
            entrypoint,
            cwd=str(workdir),
            env=env,
            shell=True,
            text=True,
            capture_output=True,
            timeout=3600,
            check=False,
        )
        if proc.stdout:
            record_log({"run_id": run_id, "pipeline_id": pipeline_id, "level": "info", "message": proc.stdout[-60000:]})
            persist_lineage_markers(run_id=run_id, pipeline_id=pipeline_id, output=proc.stdout)
        if proc.stderr:
            record_log({"run_id": run_id, "pipeline_id": pipeline_id, "level": "error", "message": proc.stderr[-60000:]})
        return finish_run(
            run_id,
            {
                "status": "ok" if proc.returncode == 0 else "failed",
                "exit_code": proc.returncode,
                "duration_sec": round(time.monotonic() - started, 3),
                "error_message": proc.stderr[-4000:] if proc.returncode else None,
            },
        )
    except Exception as exc:
        record_log({"run_id": run_id, "pipeline_id": pipeline_id, "level": "error", "message": str(exc)})
        return finish_run(
            run_id,
            {
                "status": "failed",
                "duration_sec": round(time.monotonic() - started, 3),
                "error_message": str(exc),
            },
        )


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
