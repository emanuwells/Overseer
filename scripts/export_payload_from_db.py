from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import shutil
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from socket import error as SocketError
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pm_runtime.db import get_engine
from src.pm_runtime.monitor_service import MonitorService
from src.pm_runtime.repository import MonitorRepository, to_run_summary

PAYLOAD_PATH = ROOT / "frontend" / "pm_payload.json"
DETAILS_PATH = ROOT / "frontend" / "pm_details.json"
STATUS_PATH = ROOT / "runtime" / "export_status.json"
PIPELINES_DIR = ROOT / "pipelines"
LOCAL_HOST = socket.gethostname().strip().lower() or "unknown-runner"
NGINX_PUBLISH_DIR = os.getenv("EXPORT_NGINX_DIR", "/usr/share/nginx/html/MAIATRON/apps/overseer")
SCRIPT_EXTENSIONS = (".py", ".ps1", ".sh", ".bat", ".cmd")
WARN_RE = re.compile(r"\bwarn(?:ing)?\b|⚠", re.IGNORECASE)
ERROR_RE = re.compile(r"\berror\b|\bexception\b|\btraceback\b|\bfalha\b|\bfailed\b", re.IGNORECASE)
ANOMALY_RE = re.compile(r"\bcom\s+erro:\s*[1-9]\d*\b|\bfailed:\s*[1-9]\d*\b", re.IGNORECASE)
NOISE_RE = re.compile(
    r"falha\s+ao\s+gravar\s+m[ée]tricas\s+na\s+tabela"
    r"|\bFailed[=:]\s*0\b"
    r"|\berror[s]?[=:]\s*0\b"
    r"|\b0\s+error"
    r"|\b0\s+failed\b",
    re.IGNORECASE,
)
SCRIPT_LOG_MAX_CHARS = int(os.getenv("SCRIPT_LOG_MAX_CHARS", "60000"))
SCRIPT_LOG_TABLE = os.getenv("SCRIPT_LOG_TABLE", "pipeline_script_logs")
LOGS_FALLBACK_DIR = ROOT / "logs"  # Fallback directory for logs when DB unavailable


def _ensure_logs_fallback() -> None:
    """Ensure fallback logs directory exists"""
    try:
        LOGS_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _log_fallback(message: str, pipeline_id: str | None = None) -> None:
    """Write log to file when DB is unavailable"""
    try:
        _ensure_logs_fallback()
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = f"export_{datetime.now().strftime('%Y%m%d')}.log"
        logpath = LOGS_FALLBACK_DIR / filename
        logpath.write_text(
            f"{timestamp} | {pipeline_id or 'export':<30} | {message}\n",
            encoding="utf-8",
            errors="replace"
        )
    except Exception:
        pass



def _sweep_stale_runs(*, threshold_minutes: int = 60) -> int:
    """Auto-expire runs stuck as 'running'/'Running' longer than *threshold_minutes*.

    Returns the total number of rows updated across both tables.
    """
    engine = get_engine()
    updated = 0
    stmts = [
        text(
            """
            UPDATE pipeline_runs
               SET status   = 'Failed',
                   endDate   = NOW(),
                   errorMessage = CONCAT(
                       COALESCE(errorMessage, ''),
                       '[auto-expired] stale running run cleaned up by export sweep')
             WHERE LOWER(status) = 'running'
               AND startDate < DATE_SUB(NOW(), INTERVAL :mins MINUTE)
            """
        ),
        text(
            """
            UPDATE orchestrator_runs_local
               SET status        = 'failed',
                   ended_at      = UTC_TIMESTAMP(),
                   error_message = CONCAT(
                       COALESCE(error_message, ''),
                       '[auto-expired] stuck running >60 min')
             WHERE LOWER(status) = 'running'
               AND COALESCE(started_at, created_at) < DATE_SUB(UTC_TIMESTAMP(), INTERVAL :mins MINUTE)
            """
        ),
    ]
    try:
        with engine.begin() as conn:
            for stmt in stmts:
                result = conn.execute(stmt, {"mins": threshold_minutes})
                updated += result.rowcount
        if updated:
            print(f"[sweep] auto-expired {updated} stale running run(s)")
    except Exception as exc:
        print(f"[sweep] WARNING — could not sweep stale runs: {exc}")
    return updated


def main() -> int:
    started_at = time.time()
    
    try:
        # --- housekeeping: expire any stuck "running" runs before building payload ---
        _sweep_stale_runs()

        repo = MonitorRepository()
        service = MonitorService(repo=repo)
        runs = repo.load_runs()
    except Exception as exc:
        # DB connection failed - log to fallback and exit gracefully
        error_msg = f"DB unavailable: {str(exc)[:100]}"
        print(f"[WARNING] {error_msg} — logs saved to {LOGS_FALLBACK_DIR}")
        _log_fallback(f"EXPORT_FAILED: {error_msg}", "export_process")
        return 1
    
    runs_sorted = sorted(runs, key=lambda r: r.start_date or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True)

    run_items: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    for run in runs_sorted:
        item = to_run_summary(run)
        item["owner"] = run.owner
        item["criticality"] = run.criticality
        item["run_id_pipeline"] = f"{run.pipeline_id}#{run.id}"
        run_items.append(item)
        details[str(run.id)] = {
            "errorMessage": getattr(run, "error_message", getattr(run, "error_preview", "")),
            "logMessage": getattr(run, "logMessage", getattr(run, "log_message", "")),
            "run_id_pipeline": item.get("run_id_pipeline"),
            "trigger_info": None,
        }

    fields = [
        "id",
        "run_id_pipeline",
        "pipelineId",
        "scriptName",
        "owner",
        "criticality",
        "status",
        "startDate",
        "endDate",
        "execTime",
        "usageCPU",
        "usageMemoria",
        "durationLabel",
        "cpuLabel",
        "memLabel",
        "hostname",
        "osName",
        "errorPreview",
        "triggerType",
    ]
    rows = [[item.get(field) for field in fields] for item in run_items]

    overview = service.overview("24h")
    pipelines = service.pipelines(limit=5000).get("items", [])
    orchestrator_runs = load_orchestrator_runs()
    orchestrator_triggers = load_orchestrator_triggers()
    module_lineage, run_trigger_info, runtime_scripts = load_module_lineage()
    pipeline_catalog = load_pipeline_catalog()
    pipeline_permissions = load_pipeline_permissions()
    pipeline_scripts = build_pipeline_scripts(runtime_scripts)
    enrich_pipeline_scripts_with_run_logs(pipeline_scripts, runs_sorted)
    persist_pipeline_script_logs(pipeline_scripts)
    summary = build_summary(overview, run_items)

    for run in run_items:
        rid = str(run.get("id"))
        if rid in details:
            details[rid]["trigger_info"] = run_trigger_info.get(rid)

    payload = {
        "schema_version": "3.1.0-noapi",
        "generated_at": overview.get("generatedAt"),
        "generated_at_label": fmt_pt(overview.get("generatedAt")),
        "first_run_label": first_run_label(run_items),
        "fields": fields,
        "rows": rows,
        "summary": summary,
        "overview": overview,
        "pipelines": pipelines,
        "pipeline_catalog": pipeline_catalog,
        "pipeline_permissions": pipeline_permissions,
        "orchestrator_runs": orchestrator_runs,
        "orchestrator_triggers": orchestrator_triggers,
        "module_lineage": module_lineage,
        "pipeline_scripts": pipeline_scripts,
        "lineage": {
            "nodes": [
                {"pipelineId": p.get("pipelineId"), "name": p.get("name"), "status": p.get("lastStatus", "UNKNOWN")}
                for p in pipelines
            ],
            "edges": [],
        },
    }

    write_json_atomic(PAYLOAD_PATH, payload)
    write_json_atomic(DETAILS_PATH, details)
    publish_frontend_payloads(PAYLOAD_PATH, DETAILS_PATH)

    elapsed_ms = int((time.time() - started_at) * 1000)
    status = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "duration_ms": elapsed_ms,
        "rows": len(rows),
    }
    write_json_atomic(STATUS_PATH, status)
    return 0


def _iter_pipeline_definitions() -> list[tuple[Path, dict[str, Any], str]]:
    import yaml

    items: list[tuple[Path, dict[str, Any], str]] = []
    if not PIPELINES_DIR.exists():
        return items

    for path in sorted(PIPELINES_DIR.rglob("*.y*ml")):
        if any(part.startswith("_") for part in path.parts):
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        pipeline_id = str(payload.get("pipeline_id") or "").strip()
        if not pipeline_id:
            continue
        items.append((path, payload, pipeline_id))
    return items


def load_pipeline_catalog() -> list[dict[str, Any]]:
    dedup: dict[str, dict[str, Any]] = {}
    for _, payload, pipeline_id in _iter_pipeline_definitions():
        raw_runner = str(payload.get("runner_host") or "").strip().lower()
        runner = raw_runner or LOCAL_HOST
        if runner in {"auto", "local", "localhost", "this-host", "self"}:
            runner = LOCAL_HOST
        if runner in {"*", "any"}:
            runner = "any"
        dedup[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "name": payload.get("name") or pipeline_id,
            "owner": payload.get("owner") or "unknown",
            "criticality": payload.get("criticality") or "medium",
            "schedule": payload.get("schedule") or "manual",
            "prev_schedule": payload.get("prev_schedule") or None,
            "runner_host": runner,
        }
    return [dedup[key] for key in sorted(dedup.keys())]


def load_pipeline_permissions() -> dict[str, list[dict[str, Any]]]:
    """Load pipeline permission grants from overseer_pipeline_permissions table."""
    engine = get_engine()
    sql = text(
        """
        SELECT p.pipeline_id, p.username, p.role, p.granted_at, p.granted_by,
               u.display_name
        FROM overseer_pipeline_permissions p
        LEFT JOIN MAIATRON.auth_users u ON u.username = p.username AND u.is_active = 1
        ORDER BY p.pipeline_id, p.username
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
    except Exception:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        pid = str(row.get("pipeline_id") or "").strip()
        if not pid:
            continue
        out.setdefault(pid, []).append({
            "username": row.get("username"),
            "displayName": row.get("display_name"),
            "role": row.get("role"),
            "grantedAt": to_iso(row.get("granted_at")),
            "grantedBy": row.get("granted_by"),
        })
    return out


def build_pipeline_scripts(runtime_scripts: dict[str, dict[str, dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    defs: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, payload, pipeline_id in _iter_pipeline_definitions():
        if pipeline_id not in defs:
            defs[pipeline_id] = (path, payload)

    pipeline_ids = sorted(set(defs.keys()) | set(runtime_scripts.keys()))
    out: dict[str, list[dict[str, Any]]] = {}

    for pipeline_id in pipeline_ids:
        path, payload = defs.get(pipeline_id, (None, {}))
        script_rows: dict[str, dict[str, Any]] = {}

        def upsert(
            script_path: str,
            source: str,
            executed: bool = False,
            last_status: str | None = None,
            last_run_id: Any = None,
            last_seen_at: Any = None,
            last_event_level: str | None = None,
            warning_count: int | None = None,
            error_count: int | None = None,
            last_warning_at: Any = None,
            last_error_at: Any = None,
            last_message: str | None = None,
            script_log_message: str | None = None,
            script_log_updated_at: Any = None,
            script_log_source: str | None = None,
        ) -> None:
            key = _normalize_script_path(script_path)
            if not key:
                return
            row = script_rows.setdefault(
                key,
                {
                    "path": key,
                    "_sources": set(),
                    "executed": False,
                    "lastStatus": None,
                    "lastRunId": None,
                    "lastSeenAt": None,
                    "lastEventLevel": None,
                    "warningCount": 0,
                    "errorCount": 0,
                    "lastWarningAt": None,
                    "lastErrorAt": None,
                    "lastMessage": None,
                    "scriptLogMessage": None,
                    "scriptLogUpdatedAt": None,
                    "scriptLogSource": None,
                },
            )
            row["_sources"].add(source)
            row["executed"] = bool(row["executed"] or executed)
            if last_status is not None:
                row["lastStatus"] = str(last_status).upper()
            if last_run_id is not None:
                row["lastRunId"] = last_run_id
            if last_seen_at is not None:
                row["lastSeenAt"] = to_iso(last_seen_at)
            if last_event_level is not None:
                row["lastEventLevel"] = str(last_event_level).lower()
            if warning_count is not None:
                row["warningCount"] = max(int(row.get("warningCount") or 0), int(warning_count or 0))
            if error_count is not None:
                row["errorCount"] = max(int(row.get("errorCount") or 0), int(error_count or 0))
            if last_warning_at is not None:
                row["lastWarningAt"] = to_iso(last_warning_at)
            if last_error_at is not None:
                row["lastErrorAt"] = to_iso(last_error_at)
            if last_message:
                row["lastMessage"] = str(last_message)[:1000]
            if script_log_message:
                row["scriptLogMessage"] = str(script_log_message)[-SCRIPT_LOG_MAX_CHARS:]
            if script_log_updated_at is not None:
                row["scriptLogUpdatedAt"] = to_iso(script_log_updated_at)
            if script_log_source:
                row["scriptLogSource"] = str(script_log_source)[:255]

        if path is not None:
            root_dir = path.parent
            src_dir = root_dir / "src"
            if src_dir.exists():
                for file_path in src_dir.rglob("*"):
                    if not file_path.is_file() or file_path.suffix.lower() not in SCRIPT_EXTENSIONS:
                        continue
                    if file_path.stem == "__init__":
                        continue
                    rel = file_path.relative_to(root_dir).as_posix()
                    upsert(rel, "src")

            commands: list[str] = []
            entrypoint = payload.get("entrypoint")
            if isinstance(entrypoint, str) and entrypoint.strip():
                commands.append(entrypoint.strip())

            for step in payload.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                command = step.get("run")
                if isinstance(command, str) and command.strip():
                    commands.append(command.strip())

            for command in commands:
                script_ref = _extract_script_reference(command)
                if script_ref:
                    upsert(script_ref, "yaml")

        for script_path, runtime_meta in (runtime_scripts.get(pipeline_id) or {}).items():
            upsert(
                script_path,
                source="runtime",
                executed=True,
                last_status=runtime_meta.get("lastStatus"),
                last_run_id=runtime_meta.get("lastRunId"),
                last_seen_at=runtime_meta.get("lastSeenAt"),
                last_event_level=runtime_meta.get("lastEventLevel"),
                warning_count=runtime_meta.get("warningCount"),
                error_count=runtime_meta.get("errorCount"),
                last_warning_at=runtime_meta.get("lastWarningAt"),
                last_error_at=runtime_meta.get("lastErrorAt"),
                last_message=runtime_meta.get("lastMessage"),
                script_log_message=runtime_meta.get("scriptLogMessage"),
                script_log_updated_at=runtime_meta.get("scriptLogUpdatedAt"),
                script_log_source=runtime_meta.get("scriptLogSource"),
            )

        if path is not None:
            for script_path, meta in load_pipeline_script_logs(path.parent, list(script_rows.keys())).items():
                upsert(
                    script_path,
                    source="filelog",
                    executed=bool(meta.get("hasContent")),
                    last_seen_at=meta.get("updatedAt"),
                    last_event_level=meta.get("eventLevel"),
                    warning_count=meta.get("warningCount"),
                    error_count=meta.get("errorCount"),
                    last_warning_at=meta.get("lastWarningAt"),
                    last_error_at=meta.get("lastErrorAt"),
                    last_message=meta.get("lastMessage"),
                    script_log_message=meta.get("logMessage"),
                    script_log_updated_at=meta.get("updatedAt"),
                    script_log_source=meta.get("sourceFile"),
                )

        normalized_items: list[dict[str, Any]] = []
        for script_path in sorted(script_rows.keys()):
            row = script_rows[script_path]
            normalized_items.append(
                {
                    "path": row["path"],
                    "source": ",".join(sorted(row["_sources"])),
                    "executed": bool(row.get("executed")),
                    "lastStatus": row.get("lastStatus"),
                    "lastRunId": row.get("lastRunId"),
                    "lastSeenAt": row.get("lastSeenAt"),
                    "lastEventLevel": row.get("lastEventLevel"),
                    "warningCount": int(row.get("warningCount") or 0),
                    "errorCount": int(row.get("errorCount") or 0),
                    "lastWarningAt": row.get("lastWarningAt"),
                    "lastErrorAt": row.get("lastErrorAt"),
                    "lastMessage": row.get("lastMessage"),
                    "scriptLogMessage": row.get("scriptLogMessage"),
                    "scriptLogUpdatedAt": row.get("scriptLogUpdatedAt"),
                    "scriptLogSource": row.get("scriptLogSource"),
                }
            )

        out[pipeline_id] = normalized_items

    return out


def load_pipeline_script_logs(root_dir: Path, known_scripts: list[str]) -> dict[str, dict[str, Any]]:
    logs_dir = root_dir / "logs"
    if not logs_dir.exists() or not logs_dir.is_dir():
        return {}

    known = [k for k in (known_scripts or []) if k]
    by_stem: dict[str, str] = {}
    for script_path in known:
        stem = Path(script_path).stem.lower()
        if stem and stem not in by_stem:
            by_stem[stem] = script_path

    main_script = next((k for k in known if k.lower().endswith("/main.py") or k.lower() == "main.py"), "src/main.py")
    out: dict[str, dict[str, Any]] = {}

    for file_path in sorted(logs_dir.glob("*.log"), key=lambda fp: fp.stat().st_mtime, reverse=True):
        mapped = map_log_file_to_script(file_path.name, by_stem, main_script)
        if not mapped or mapped in out:
            continue

        text_tail = read_tail_text(file_path, SCRIPT_LOG_MAX_CHARS)
        if not text_tail.strip():
            continue

        warning_count, error_count = count_log_levels(text_tail)
        event_level = "error" if error_count > 0 else ("warning" if warning_count > 0 else "ok")
        event_message = pick_last_event_line(text_tail)
        updated_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        out[mapped] = {
            "sourceFile": file_path.name,
            "logMessage": text_tail,
            "updatedAt": updated_at,
            "warningCount": warning_count,
            "errorCount": error_count,
            "eventLevel": event_level,
            "lastWarningAt": updated_at if warning_count > 0 else None,
            "lastErrorAt": updated_at if error_count > 0 else None,
            "lastMessage": event_message,
            "hasContent": True,
        }

    return out


def map_log_file_to_script(file_name: str, by_stem: dict[str, str], main_script: str) -> str | None:
    stem = Path(file_name).stem.lower()
    if stem in by_stem:
        return by_stem[stem]
    if stem.startswith("sync_") and stem != "sync_system":
        return main_script
    if stem == "main":
        return main_script
    return None


def read_tail_text(path: Path, max_chars: int) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if len(content) > max_chars:
        return content[-max_chars:]
    return content


def pick_last_event_line(content: str) -> str:
    lines = [line.strip() for line in str(content or "").splitlines() if line.strip()]
    if not lines:
        return ""
    for line in reversed(lines):
        if _is_noise_message(line):
            continue
        if WARN_RE.search(line) or ERROR_RE.search(line) or ANOMALY_RE.search(line):
            return line[:1000]
    return lines[-1][:1000]


def persist_pipeline_script_logs(pipeline_scripts: dict[str, list[dict[str, Any]]]) -> None:
    if not pipeline_scripts:
        return

    try:
        engine = get_engine()
        create_sql = text(
            f"""
            CREATE TABLE IF NOT EXISTS {SCRIPT_LOG_TABLE} (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              pipelineId VARCHAR(255) NOT NULL,
              scriptPath VARCHAR(512) NOT NULL,
              logSource VARCHAR(255) NULL,
              logMessage MEDIUMTEXT NULL,
              warningCount INT NOT NULL DEFAULT 0,
              errorCount INT NOT NULL DEFAULT 0,
              lastEventLevel VARCHAR(32) NULL,
              lastMessage VARCHAR(1024) NULL,
              logUpdatedAt VARCHAR(64) NULL,
              regDate DATETIME NOT NULL,
              modDate DATETIME NOT NULL,
              UNIQUE KEY uq_pipeline_script (pipelineId, scriptPath)
            )
            """
        )

        upsert_sql = text(
            f"""
            INSERT INTO {SCRIPT_LOG_TABLE}
                (pipelineId, scriptPath, logSource, logMessage, warningCount, errorCount, lastEventLevel, lastMessage, logUpdatedAt, regDate, modDate)
            VALUES
                (:pipelineId, :scriptPath, :logSource, :logMessage, :warningCount, :errorCount, :lastEventLevel, :lastMessage, :logUpdatedAt, :regDate, :modDate)
            ON DUPLICATE KEY UPDATE
                logSource = VALUES(logSource),
                logMessage = VALUES(logMessage),
                warningCount = VALUES(warningCount),
                errorCount = VALUES(errorCount),
                lastEventLevel = VALUES(lastEventLevel),
                lastMessage = VALUES(lastMessage),
                logUpdatedAt = VALUES(logUpdatedAt),
                modDate = VALUES(modDate)
            """
        )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        with engine.begin() as conn:
            conn.execute(create_sql)
            for pipeline_id, scripts in pipeline_scripts.items():
                for item in scripts:
                    log_message = str(item.get("scriptLogMessage") or "").strip()
                    if not log_message:
                        continue
                    conn.execute(
                        upsert_sql,
                        {
                            "pipelineId": pipeline_id,
                            "scriptPath": item.get("path"),
                            "logSource": item.get("scriptLogSource"),
                            "logMessage": log_message[-SCRIPT_LOG_MAX_CHARS:],
                            "warningCount": int(item.get("warningCount") or 0),
                            "errorCount": int(item.get("errorCount") or 0),
                            "lastEventLevel": item.get("lastEventLevel"),
                            "lastMessage": str(item.get("lastMessage") or "")[:1000],
                            "logUpdatedAt": item.get("scriptLogUpdatedAt"),
                            "regDate": now,
                            "modDate": now,
                        },
                    )
    except Exception as exc:
        # DB unavailable - fall back to file logging
        for pipeline_id, scripts in pipeline_scripts.items():
            for script in scripts:
                path = script.get("path") or "unknown"
                msg = str(script.get("scriptLogMessage") or "")[:100]
                _log_fallback(f"script_log {path}: {msg}", pipeline_id)


def enrich_pipeline_scripts_with_run_logs(
    pipeline_scripts: dict[str, list[dict[str, Any]]],
    runs_sorted: list[Any],
) -> None:
    if not pipeline_scripts or not runs_sorted:
        return

    latest_by_pipeline: dict[str, Any] = {}
    for run in runs_sorted:
        pid = str(getattr(run, "pipeline_id", "") or "").strip()
        if not pid or pid in latest_by_pipeline:
            continue
        latest_by_pipeline[pid] = run

    for pipeline_id, scripts in (pipeline_scripts or {}).items():
        run = latest_by_pipeline.get(str(pipeline_id))
        if run is None:
            continue

        run_log = str(getattr(run, "log_message", "") or "").strip()
        if not run_log:
            continue

        warning_count, error_count = count_log_levels(run_log)
        run_status = str(getattr(run, "status", "") or "").upper()
        # Trust explicit pipeline status first: OK means OK even if ERROR lines exist
        if run_status in {"OK", "SUCCESS", "SUCESSO"}:
            # If status is OK, downgrade ERROR lines to warnings—only report actual warnings
            event_level = "warning" if warning_count > 0 else "ok"
        elif run_status in {"NOK", "FAILED", "FAIL", "ERROR"}:
            event_level = "error"
        elif error_count > 0:
            event_level = "error"
        elif warning_count > 0:
            event_level = "warning"
        else:
            event_level = "unknown"

        target = next(
            (
                s
                for s in scripts
                if str(s.get("path", "")).lower().endswith("/main.py")
                or str(s.get("path", "")).lower() == "main.py"
            ),
            None,
        )
        if target is None:
            continue

        seen_at = to_iso(getattr(run, "end_date", None) or getattr(run, "start_date", None))
        target["lastRunId"] = int(getattr(run, "id", 0) or 0)
        target["lastSeenAt"] = seen_at
        target["scriptLogMessage"] = run_log[-SCRIPT_LOG_MAX_CHARS:]
        target["scriptLogUpdatedAt"] = seen_at
        target["scriptLogSource"] = f"run:{getattr(run, 'id', '-') }"
        # When pipeline status is OK, ignore ERROR lines—don't count them as serious errors
        if run_status in {"OK", "SUCCESS", "SUCESSO"}:
            target["errorCount"] = 0  # Clear error count when status=OK
            target["warningCount"] = max(int(target.get("warningCount") or 0), warning_count)
        else:
            target["warningCount"] = max(int(target.get("warningCount") or 0), warning_count)
            target["errorCount"] = max(int(target.get("errorCount") or 0), error_count)
        if warning_count > 0:
            target["lastWarningAt"] = seen_at
        if error_count > 0 and run_status not in {"OK", "SUCCESS", "SUCESSO"}:
            target["lastErrorAt"] = seen_at
        target["lastEventLevel"] = event_level
        msg = pick_last_event_line(run_log)
        if msg:
            target["lastMessage"] = msg


def load_orchestrator_runs() -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(
        """
        SELECT run_local_id, pipeline_id, status, trigger_source, requested_by, created_at, runner_host
        FROM orchestrator_runs_local
        ORDER BY run_local_id DESC
        LIMIT 200
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "runId": int(row["run_local_id"]),
                "pipelineId": row["pipeline_id"],
                "status": row["status"],
                "source": row["trigger_source"],
                "triggeredBy": row["requested_by"],
                "runnerHost": row.get("runner_host"),
                "createdAt": to_iso(row["created_at"]),
            }
        )
    return out


def load_orchestrator_triggers() -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(
        """
        SELECT trigger_local_id, trigger_id, pipeline_id, requested_by, requested_at, source,
               runner_host, status, claimed_by, claimed_at, consumed_at, error_message
        FROM orchestrator_triggers_local
        ORDER BY trigger_local_id DESC
        LIMIT 200
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "triggerLocalId": int(row["trigger_local_id"]),
                "triggerId": row["trigger_id"],
                "pipelineId": row["pipeline_id"],
                "requestedBy": row["requested_by"],
                "requestedAt": to_iso(row["requested_at"]),
                "source": row["source"],
                "runnerHost": row["runner_host"],
                "status": row["status"],
                "claimedBy": row["claimed_by"],
                "claimedAt": to_iso(row["claimed_at"]),
                "consumedAt": to_iso(row["consumed_at"]),
                "errorMessage": row["error_message"],
            }
        )
    return out


def load_module_lineage() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, dict[str, Any]]]]:
    engine = get_engine()
    sql = text(
        """
        SELECT pipelineId, runId, moduleId, parentModuleId, status, errorMessage, logMessage, contextJson, endedAt
        FROM pipeline_module_events
        ORDER BY endedAt DESC
        LIMIT 5000
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
    except Exception:
        return {}, {}, {}

    parsed_events: list[dict[str, Any]] = []
    latest_run_by_pipeline: dict[str, str] = {}
    latest_run_ended_at: dict[str, int] = {}
    run_info: dict[str, Any] = {}

    # Pass 1: parse all rows and keep run-level info for pm_details.trigger_info.
    for row in rows:
        pipeline_id = str(row.get("pipelineId") or "").strip()
        module_id = str(row.get("moduleId") or "").strip()
        if not pipeline_id or not module_id:
            continue

        run_id = row.get("runId")
        run_key = str(run_id) if run_id is not None else ""
        context = _safe_json(row.get("contextJson"))
        status = str(row.get("status") or "UNKNOWN").upper()
        ended_at = row.get("endedAt")
        ended_iso = to_iso(ended_at)
        ended_value = _date_value(ended_iso)
        error_message = str(row.get("errorMessage") or "").strip()
        log_message = str(row.get("logMessage") or context.get("log_message") or "").strip()
        event_level = _detect_event_level(status=status, error_message=error_message, log_message=log_message)
        event_message = _pick_event_message(error_message=error_message, log_message=log_message)
        is_critical = bool(context.get("critical", True))  # default critical if not specified
        script_ref = _extract_script_reference(context.get("script_command"))

        parsed_events.append(
            {
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "run_key": run_key,
                "module_id": module_id,
                "parent_module_id": str(row.get("parentModuleId") or "").strip(),
                "status": status,
                "error_message": error_message,
                "log_message": log_message,
                "ended_iso": ended_iso,
                "ended_value": ended_value,
                "event_level": event_level,
                "event_message": event_message,
                "critical": is_critical,
                "script_ref": script_ref,
            }
        )

        if run_key:
            if run_key not in run_info:
                run_info[run_key] = {
                    "lastModule": module_id,
                    "failedModule": module_id if status == "NOK" else None,
                    "moduleStatus": status,
                }
            elif run_info[run_key].get("failedModule") is None and status == "NOK":
                run_info[run_key]["failedModule"] = module_id
                run_info[run_key]["moduleStatus"] = "NOK"

            current_ended = latest_run_ended_at.get(pipeline_id, -1)
            if ended_value > current_ended:
                latest_run_ended_at[pipeline_id] = ended_value
                latest_run_by_pipeline[pipeline_id] = run_key

    # Pass 2: build module_lineage/pipeline_scripts only for the latest run per pipeline.
    lineage: dict[str, Any] = {}
    runtime_scripts: dict[str, dict[str, dict[str, Any]]] = {}
    for event in parsed_events:
        pipeline_id = event["pipeline_id"]
        run_key = event["run_key"]
        selected_run = latest_run_by_pipeline.get(pipeline_id)
        if selected_run:
            if run_key != selected_run:
                continue
        elif run_key:
            continue

        module_id = event["module_id"]
        status = event["status"]
        error_message = event["error_message"]
        log_message = event["log_message"]
        ended_iso = event["ended_iso"]
        event_level = event["event_level"]
        event_message = event["event_message"]
        script_ref = event["script_ref"]
        is_critical = bool(event["critical"])
        run_id = event["run_id"]

        bucket = lineage.setdefault(pipeline_id, {"nodes": {}, "edges": set()})
        if module_id not in bucket["nodes"]:
            bucket["nodes"][module_id] = {
                "id": module_id,
                "label": module_id,
                "script": script_ref,
                "status": status,
                "critical": is_critical,
                "lastRunId": run_id,
                "lastSeenAt": ended_iso,
                "lastError": error_message[:300],
                "lastEventLevel": event_level,
                "lastMessage": event_message[:300] if event_message else "",
            }

        if script_ref:
            scripts_bucket = runtime_scripts.setdefault(pipeline_id, {})
            script_row = scripts_bucket.setdefault(
                script_ref,
                {
                    "path": script_ref,
                    "lastStatus": status,
                    "lastRunId": run_id,
                    "lastSeenAt": ended_iso,
                    "lastEventLevel": event_level,
                    "warningCount": 0,
                    "errorCount": 0,
                    "lastWarningAt": None,
                    "lastErrorAt": None,
                    "lastMessage": "",
                    "scriptLogMessage": "",
                    "scriptLogUpdatedAt": None,
                    "scriptLogSource": None,
                },
            )
            if _iso_is_newer(ended_iso, script_row.get("lastSeenAt")):
                script_row["lastStatus"] = status
                script_row["lastRunId"] = run_id
                script_row["lastSeenAt"] = ended_iso
                script_row["lastEventLevel"] = event_level
                script_row["lastMessage"] = event_message[:1000] if event_message else ""
            if log_message:
                event_line = f"[{ended_iso or '-'}] [{module_id}] [{status}] {log_message}".strip()
                prev_log = str(script_row.get("scriptLogMessage") or "").strip()
                merged = event_line if not prev_log else f"{prev_log}\n{event_line}"
                script_row["scriptLogMessage"] = merged[:SCRIPT_LOG_MAX_CHARS]
                if _iso_is_newer(ended_iso, script_row.get("scriptLogUpdatedAt")):
                    script_row["scriptLogUpdatedAt"] = ended_iso
                if not script_row.get("scriptLogSource"):
                    script_row["scriptLogSource"] = "module-events"
            if event_level == "warning":
                script_row["warningCount"] = int(script_row.get("warningCount") or 0) + 1
                if _iso_is_newer(ended_iso, script_row.get("lastWarningAt")):
                    script_row["lastWarningAt"] = ended_iso
            if event_level == "error":
                script_row["errorCount"] = int(script_row.get("errorCount") or 0) + 1
                if _iso_is_newer(ended_iso, script_row.get("lastErrorAt")):
                    script_row["lastErrorAt"] = ended_iso

        parent = str(event.get("parent_module_id") or "").strip()
        if parent:
            bucket["edges"].add((parent, module_id))

    normalized: dict[str, Any] = {}
    for pipeline_id, bucket in lineage.items():
        nodes = list(bucket["nodes"].values())
        edges = [{"source": source, "target": target} for source, target in sorted(bucket["edges"])]
        normalized[pipeline_id] = {"nodes": nodes, "edges": edges}

    return normalized, run_info, runtime_scripts


def _detect_event_level(*, status: str, error_message: str, log_message: str) -> str:
    status_norm = str(status or "").upper()
    merged = f"{error_message}\n{log_message}".strip()
    if _is_noise_message(merged):
        return "ok" if status_norm in {"OK", "SUCCESS", "SUCESSO"} else "warning"
    if status_norm in {"NOK", "FAILED", "FAIL", "ERROR"}:
        return "error"
    # If status is explicitly OK, trust it — only downgrade to warning for log noise
    if status_norm in {"OK", "SUCCESS", "SUCESSO"}:
        if error_message and not _is_noise_message(str(error_message)):
            return "warning"
        log_text = str(log_message or "")
        if WARN_RE.search(log_text):
            return "warning"
        return "ok"
    if error_message:
        return "error"
    log_text = str(log_message or "")
    if WARN_RE.search(log_text):
        return "warning"
    if ERROR_RE.search(log_text):
        return "error"
    return "unknown"


def count_log_levels(content: str) -> tuple[int, int]:
    warning_count = 0
    error_count = 0
    for raw in str(content or "").splitlines():
        line = raw.strip()
        if not line or _is_noise_message(line):
            continue
        if ERROR_RE.search(line):
            error_count += 1
        elif WARN_RE.search(line):
            warning_count += 1
        elif ANOMALY_RE.search(line):
            warning_count += 1
    return warning_count, error_count


def _is_noise_message(message: str) -> bool:
    txt = str(message or "").strip()
    if not txt:
        return False
    return bool(NOISE_RE.search(txt))


def _pick_event_message(*, error_message: str, log_message: str) -> str:
    if error_message:
        return error_message
    text_value = str(log_message or "").strip()
    if not text_value:
        return ""
    lines = [line.strip() for line in text_value.splitlines() if line.strip()]
    if not lines:
        return ""
    for line in lines:
        if WARN_RE.search(line) or ERROR_RE.search(line):
            return line
    return lines[-1]


def _iso_is_newer(candidate: Any, current: Any) -> bool:
    return _date_value(candidate) >= _date_value(current)


def _date_value(value: Any) -> int:
    if not value:
        return 0
    try:
        txt = str(value).replace("Z", "+00:00")
        return int(datetime.fromisoformat(txt).timestamp())
    except Exception:
        return 0


def _safe_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_script_path(value: Any) -> str:
    text = str(value or "").strip().strip("\"'")
    if not text:
        return ""
    text = text.replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")
    if text.startswith("./"):
        text = text[2:]
    return text


def _extract_script_reference(command: Any) -> str | None:
    if command is None:
        return None
    text = str(command).strip()
    if not text:
        return None
    try:
        parts = shlex.split(text, posix=False)
    except Exception:
        parts = text.split()
    for token in parts:
        candidate = _normalize_script_path(token)
        if candidate.lower().endswith(SCRIPT_EXTENSIONS):
            return candidate
    return None


def build_summary(overview: dict[str, Any], runs: list[dict[str, Any]]) -> dict[str, Any]:
    global_kpis = overview.get("globalKpis", {})
    signals = overview.get("operationalSignals", {})
    return {
        "generated_at": overview.get("generatedAt"),
        "total_runs": global_kpis.get("totalRuns", 0),
        "ok_runs": global_kpis.get("okRuns", 0),
        "nok_runs": global_kpis.get("nokRuns", 0),
        "success_rate": global_kpis.get("successRate", 0),
        "avg_exec_time": global_kpis.get("avgExecTime", 0),
        "avg_cpu": global_kpis.get("avgCpu", 0),
        "avg_mem": global_kpis.get("avgMem", 0),
        "p95_exec_time": global_kpis.get("p95ExecTime", 0),
        "pipeline_count": signals.get("pipelineCount", 0),
        "at_risk": signals.get("atRisk", 0),
        "stale": signals.get("stale", 0),
        "regressions": signals.get("regressions", 0),
        "archive_last_run_at": read_archive_status(),
        "export_window_minutes": 15,
        "first_run_label": first_run_label(runs),
    }


def read_archive_status() -> str | None:
    path = ROOT / "runtime" / "archive_status.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload.get("last_archive_at")


def first_run_label(runs: list[dict[str, Any]]) -> str:
    values = [r.get("startDate") for r in runs if r.get("startDate")]
    if not values:
        return "-"
    return fmt_pt(min(values))


def fmt_pt(value: Any) -> str:
    if not value:
        return "-"
    txt = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except Exception:
        return str(value)
    return dt.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")


def to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    return str(value)


def publish_frontend_payloads(payload_path: Path, details_path: Path) -> None:
    targets: list[tuple[Path, str]] = [
        (payload_path, "overseer_payload.json"),
        (details_path, "overseer_details.json"),
    ]

    publish_dir = Path(NGINX_PUBLISH_DIR)
    if publish_dir.exists():
        _publish_local(publish_dir, targets)
        _cleanup_local_legacy_files(publish_dir)
        return

    _publish_via_ssh(NGINX_PUBLISH_DIR, targets)
    _cleanup_ssh_legacy_files(NGINX_PUBLISH_DIR)


def _publish_local(target_dir: Path, files: list[tuple[Path, str]]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for src, name in files:
        dst = target_dir / name
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        shutil.copy2(src, tmp)
        # Retry loop: OneDrive may lock the target file during sync
        for attempt in range(5):
            try:
                tmp.replace(dst)
                break
            except PermissionError:
                if attempt < 4:
                    import time
                    time.sleep(1)
                else:
                    print(f"[export] WARN: Could not replace {dst} after 5 retries, keeping .tmp")
                    raise


def _publish_via_ssh(target_dir: str, files: list[tuple[Path, str]]) -> None:
    cfg = _load_json(ROOT / "secrets" / "database.json")
    ssh_cfg = cfg.get("ssh") or {}

    host = str(os.getenv("EXPORT_SSH_HOST") or ssh_cfg.get("host") or "").strip()
    user = str(os.getenv("EXPORT_SSH_USER") or ssh_cfg.get("user") or "").strip()
    port = int(os.getenv("EXPORT_SSH_PORT") or ssh_cfg.get("port") or 22)
    key_file = str(os.getenv("EXPORT_SSH_KEY") or ssh_cfg.get("key_filename") or "ssh_key").strip()

    if not host or not user:
        raise RuntimeError("Sem destino SSH para publicar JSON (EXPORT_SSH_HOST/USER ou secrets/database.json->ssh).")

    key_path = _resolve_ssh_key_path(key_file)

    try:
        import paramiko
    except Exception as exc:
        raise RuntimeError("Pacote 'paramiko' em falta para publicar JSON via SSH.") from exc

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=host, port=port, username=user, key_filename=str(key_path), timeout=20)
            with client.open_sftp() as sftp:
                _sftp_mkdir_p(sftp, target_dir)
                for src, name in files:
                    remote = posixpath.join(target_dir, name)
                    _sftp_put_atomic(sftp, src, remote)
            return
        except (SocketError, paramiko.SSHException, EOFError) as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(2 * attempt)
        finally:
            client.close()

    raise RuntimeError(f"Falha ao publicar via SSH em {host}:{port}: {last_exc}")


def _cleanup_local_legacy_files(target_dir: Path) -> None:
    for legacy in ("pm_payload.json", "pm_details.json"):
        legacy_path = target_dir / legacy
        try:
            if legacy_path.exists() or legacy_path.is_symlink():
                legacy_path.unlink()
        except Exception:
            pass


def _cleanup_ssh_legacy_files(target_dir: str) -> None:
    cfg = _load_json(ROOT / "secrets" / "database.json")
    ssh_cfg = cfg.get("ssh") or {}

    host = str(os.getenv("EXPORT_SSH_HOST") or ssh_cfg.get("host") or "").strip()
    user = str(os.getenv("EXPORT_SSH_USER") or ssh_cfg.get("user") or "").strip()
    port = int(os.getenv("EXPORT_SSH_PORT") or ssh_cfg.get("port") or 22)
    key_file = str(os.getenv("EXPORT_SSH_KEY") or ssh_cfg.get("key_filename") or "ssh_key").strip()

    if not host or not user:
        return

    key_path = _resolve_ssh_key_path(key_file)

    try:
        import paramiko
    except Exception:
        return

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, port=port, username=user, key_filename=str(key_path), timeout=20)
        with client.open_sftp() as sftp:
            for legacy in ("pm_payload.json", "pm_details.json"):
                remote = posixpath.join(target_dir, legacy)
                try:
                    sftp.remove(remote)
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        client.close()


def _sftp_mkdir_p(sftp: Any, remote_dir: str) -> None:
    parts = [part for part in remote_dir.strip("/").split("/") if part]
    current = ""
    for part in parts:
        current = f"{current}/{part}" if current else f"/{part}"
        try:
            sftp.stat(current)
        except Exception:
            sftp.mkdir(current)


def _sftp_put_atomic(sftp: Any, local_file: Path, remote_file: str) -> None:
    tmp = f"{remote_file}.tmp"
    sftp.put(str(local_file), tmp)
    try:
        sftp.remove(remote_file)
    except Exception:
        pass
    sftp.rename(tmp, remote_file)


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


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
