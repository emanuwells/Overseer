from __future__ import annotations

import argparse
import json
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from croniter import croniter
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pm_runtime.settings import settings
from src.pm_runtime.db import get_db_url, get_engine
from overseer_monitor import OverseerMonitor
from overseer_monitor.lineage_emitter import MARKER_PREFIX
from overseer_sdk.runtime_context import runtime_ctx as _runtime_ctx

PIPELINES_DIR = ROOT / "pipelines"
DEFAULT_RUN_NOW_DIR = ROOT / "runtime" / "run_now_channel"
SCHEDULE_TRIGGER_DIR = ROOT / "runtime" / "triggers" / "schedule"
SCHEDULER_STATE_FILE = ROOT / "runtime" / "scheduler_state.json"
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
IS_WINDOWS = platform.system() == "Windows"

_shutdown_event = threading.Event()

def safe_print(*args: Any, sep: str = " ", end: str = "\n") -> None:
    text = sep.join(str(a) for a in args) + end
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode(encoding, errors="replace"))


@dataclass
class PipelineCfg:
    definition_path: Path
    root_dir: Path
    pipeline_id: str
    name: str
    owner: str
    criticality: str
    runner_host: str | None
    schedule: str | None
    timeout_sec: int
    retries: int
    entrypoint: str | None
    entrypoint_windows: str | None
    steps: list[dict[str, Any]]


@dataclass
class ModuleMarker:
    """Parsed lineage marker from subprocess stdout."""
    module_id: str
    critical: bool = True
    parent_module_id: str | None = None
    status: str = "OK"
    message: str | None = None
    started_at: float = 0.0
    ended_at: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)



class StepExecutionError(RuntimeError):
    def __init__(self, message: str, log_message: str | None = None) -> None:
        super().__init__(message)
        self.log_message = log_message


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "list":
        return cmd_list()
    if args.command == "run":
        return cmd_run(args)
    if args.command == "trigger":
        return cmd_trigger(args)
    if args.command == "archive":
        return cmd_archive(args.days)
    if args.command == "export":
        return cmd_export()
    if args.command == "scheduler":
        return cmd_scheduler(args)
    if args.command == "user":
        return cmd_user(args)
    if args.command == "schedule":
        return cmd_schedule(args)
    if args.command == "deploy-frontend":
        return cmd_deploy_frontend()
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orquestrador simples para pipelines YAML.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="Lista pipelines disponiveis.")

    run = sub.add_parser("run", help="Executa um pipeline manualmente.")
    run.add_argument("pipeline_id", nargs="?", help="ID do pipeline.")
    run.add_argument("--file", dest="pipeline_file", help="Ficheiro YAML especifico.")
    run.add_argument("--by", default="cli", help="Utilizador/ator do trigger.")
    run.add_argument("--force", action="store_true", help="Ignora restricao runner_host no YAML.")

    trig = sub.add_parser("trigger", help="Gestao de triggers do frontend.")
    trig_sub = trig.add_subparsers(dest="trigger_cmd")
    t_enq = trig_sub.add_parser("enqueue", help="Enfileira trigger manual.")
    t_enq.add_argument("pipeline_id")
    t_enq.add_argument("--by", default="cli")
    t_enq.add_argument("--source", default="frontend")
    t_enq.add_argument("--runner-host", default=None, help="Hostname alvo para consumo do trigger.")
    t_enq.add_argument("--notes", default="")
    t_consume = trig_sub.add_parser("consume", help="Consome fila de triggers.")
    t_consume.add_argument("--runner", default=None, help="Hostname do runner atual (default: hostname local).")
    t_consume.add_argument("--max", type=int, default=10, help="Maximo de triggers a consumir por execucao.")
    t_file = trig_sub.add_parser("consume-file", help="Consome canal de triggers por ficheiros (run now sem API).")
    t_file.add_argument("--dir", dest="channel_dir", default=str(DEFAULT_RUN_NOW_DIR), help="Diretorio base do canal de triggers.")
    t_file.add_argument("--runner", default=None, help="Hostname do runner atual (default: hostname local).")
    t_file.add_argument("--max", type=int, default=20, help="Maximo de triggers por ciclo.")
    t_file.add_argument("--poll", type=float, default=2.0, help="Segundos entre ciclos quando em loop.")
    t_file.add_argument("--once", action="store_true", help="Executa apenas um ciclo de consumo e termina.")

    arch = sub.add_parser("archive", help="Arquiva logs antigos.")
    arch.add_argument("--days", type=int, default=30)

    sub.add_parser("export", help="Forca export DB -> JSON.")

    # ── schedule management ──
    sch = sub.add_parser("schedule", help="Gestao de schedules de pipelines.")
    sch_sub = sch.add_subparsers(dest="schedule_cmd")
    sch_set = sch_sub.add_parser("set", help="Altera schedule de um pipeline (reescreve YAML).")
    sch_set.add_argument("pipeline_id", help="ID do pipeline.")
    sch_set.add_argument("new_schedule", help="Nova expressao cron ou 'manual'.")
    sch_set.add_argument("--by", default="cli", help="Utilizador que fez a alteracao.")
    sch_show = sch_sub.add_parser("show", help="Mostra schedule atual de um pipeline.")
    sch_show.add_argument("pipeline_id", nargs="?", help="ID do pipeline (ou todos se omitido).")

    # ── scheduler daemon ──
    sched = sub.add_parser("scheduler", help="Daemon scheduler (substitui cron). Corre pipelines conforme schedule YAML + tarefas internas.")
    sched.add_argument("--once", action="store_true", help="Executa um unico tick e termina.")
    sched.add_argument("--tick", type=int, default=60, help="Intervalo entre ticks em segundos (default: 60).")
    sched.add_argument("--workers", type=int, default=4, help="Threads para execucao paralela de pipelines (default: 4).")

    # ── user management ──
    usr = sub.add_parser("user", help="Gestao de utilizadores e permissoes.")
    usr_sub = usr.add_subparsers(dest="user_cmd")
    usr_sub.add_parser("list", help="Lista utilizadores ativos de MAIATRON.auth_users.")
    usr_grant = usr_sub.add_parser("grant", help="Atribui permissao a um utilizador para um pipeline.")
    usr_grant.add_argument("username")
    usr_grant.add_argument("pipeline_id")
    usr_grant.add_argument("--role", default="executor", choices=["owner", "executor", "viewer"])
    usr_revoke = usr_sub.add_parser("revoke", help="Remove permissao de um utilizador para um pipeline.")
    usr_revoke.add_argument("username")
    usr_revoke.add_argument("pipeline_id")
    usr_show = usr_sub.add_parser("show", help="Mostra permissoes de um pipeline.")
    usr_show.add_argument("pipeline_id")

    # ── deploy frontend assets (blocked by policy) ──
    sub.add_parser(
        "deploy-frontend",
        help="BLOQUEADO por politica MAIATRON: Overseer publica apenas dados JSON.",
    )

    return parser


def cmd_list() -> int:
    configs = load_all_pipelines()
    if not configs:
        safe_print("Sem pipelines em pipelines/*.yaml")
        return 0
    for cfg in configs:
        safe_print(
            f"- {cfg.pipeline_id} | owner={cfg.owner} | criticality={cfg.criticality} | "
            f"schedule={cfg.schedule or 'manual'} | runner={cfg.runner_host or 'any'} | file={cfg.definition_path}"
        )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = None
    if args.pipeline_file:
        cfg = load_pipeline_file(Path(args.pipeline_file))
    elif args.pipeline_id:
        cfg = find_pipeline(args.pipeline_id)
    if cfg is None:
        safe_print("Pipeline nao encontrada. Usa 'python orchestrator.py list'.")
        return 1
    local_runner = normalize_runner_name(None)
    if cfg.runner_host and cfg.runner_host != "any" and normalize_runner_name(cfg.runner_host) != local_runner and not args.force:
        safe_print(
            f"Pipeline '{cfg.pipeline_id}' atribuida a runner '{cfg.runner_host}'. "
            f"Runner local='{local_runner}'. Usa --force para ignorar."
        )
        return 1
    return execute_pipeline(cfg, requested_by=args.by, trigger_source="manual")


def cmd_trigger(args: argparse.Namespace) -> int:
    engine = get_engine()
    ensure_tables(engine)

    if args.trigger_cmd == "enqueue":
        cfg = find_pipeline(str(args.pipeline_id))
        runner_target = args.runner_host or (cfg.runner_host if cfg else None)
        trigger = {
            "trigger_id": uuid.uuid4().hex,
            "pipeline_id": args.pipeline_id,
            "requested_by": args.by,
            "requested_at": now_iso(),
            "source": args.source,
            "runner_host": runner_target,
            "status": "queued",
            "notes": args.notes,
        }
        insert_trigger(engine, trigger)
        safe_print(json.dumps(trigger, ensure_ascii=False))
        return 0

    if args.trigger_cmd == "consume":
        return consume_triggers(runner=args.runner, max_items=args.max)
    if args.trigger_cmd == "consume-file":
        return consume_file_triggers(
            channel_root=Path(args.channel_dir),
            runner=args.runner,
            max_items=args.max,
            poll_seconds=args.poll,
            once=args.once,
        )

    safe_print("Comando trigger invalido.")
    return 2


def cmd_archive(days: int) -> int:
    script = ROOT / "scripts" / "archive_logs.py"
    return subprocess.run([sys.executable, str(script), "--days", str(days)], check=False).returncode


def cmd_export() -> int:
    script = ROOT / "scripts" / "export_payload_from_db.py"
    return subprocess.run([sys.executable, str(script)], check=False).returncode


def cmd_deploy_frontend() -> int:
    """Frontend deploy is intentionally disabled; Overseer only publishes JSON payloads."""
    safe_print("deploy-frontend: BLOQUEADO por politica MAIATRON.")
    safe_print("Use apenas: python scripts/export_payload_from_db.py")
    safe_print("Frontend (HTML/JS/CSS) e gerido fora do Overseer em Frontends/MAIATRON.")
    return 2


def load_all_pipelines() -> list[PipelineCfg]:
    out: list[PipelineCfg] = []
    for path in sorted(PIPELINES_DIR.rglob("*.y*ml")):
        if any(part.startswith("_") for part in path.parts):
            continue
        try:
            out.append(load_pipeline_file(path))
        except Exception:
            continue
    return out


def find_pipeline(pipeline_id: str) -> PipelineCfg | None:
    for cfg in load_all_pipelines():
        if cfg.pipeline_id == pipeline_id:
            return cfg
    return None


def load_pipeline_file(path: Path) -> PipelineCfg:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pipeline_id = str(payload.get("pipeline_id") or "").strip()
    if not pipeline_id:
        raise ValueError(f"pipeline_id ausente em {path}")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", pipeline_id):
        raise ValueError(f"pipeline_id invalido: {pipeline_id}")

    entrypoint = payload.get("entrypoint")
    entrypoint_windows = payload.get("entrypoint_windows")
    steps = payload.get("steps") or []
    if not entrypoint and not steps:
        raise ValueError("YAML precisa de 'entrypoint' ou 'steps'.")

    return PipelineCfg(
        definition_path=path.resolve(),
        root_dir=path.parent.resolve(),
        pipeline_id=pipeline_id,
        name=payload.get("name") or pipeline_id,
        owner=payload.get("owner") or "unknown",
        criticality=payload.get("criticality") or "medium",
        runner_host=resolve_pipeline_runner_host(payload.get("runner_host")),
        schedule=payload.get("schedule"),
        timeout_sec=int(payload.get("timeout_sec") or 3600),
        retries=int(payload.get("retries") or 2),
        entrypoint=entrypoint,
        entrypoint_windows=entrypoint_windows,
        steps=steps,
    )


def execute_pipeline(cfg: PipelineCfg, requested_by: str, trigger_source: str) -> int:
    engine = get_engine()
    ensure_tables(engine)
    run_id = insert_run(engine, cfg, requested_by, trigger_source)

    db_params = db_params_from_url(get_db_url())
    monitor = OverseerMonitor(
        script_name=cfg.pipeline_id,
        table_name=settings.runs_table,
        db_params=db_params,
        frontend_base_url=None,
        slack_config=os.getenv("P_MONITOR_SLACK_CONFIG"),
        extra_tags={"mode": "no-api-cli"},
    )
    monitor.start()

    ok = False
    warning = False
    error_message = ""
    run_exit_code = 1
    run_logs: list[str] = []
    all_module_markers: list[ModuleMarker] = []
    try:
        plan = build_execution_plan(cfg)
        for attempt in range(1, cfg.retries + 2):
            set_run_status(engine, run_id, "running")
            insert_event(engine, run_id, "info", f"attempt {attempt} started", {"attempt": attempt})
            try:
                for step in plan:
                    step_log, step_markers = run_step(engine, cfg, run_id, step, attempt, monitor, trigger_source=trigger_source)
                    if step_log:
                        run_logs.append(step_log)
                    all_module_markers.extend(step_markers)
                ok = True
                break
            except Exception as exc:
                if isinstance(exc, StepExecutionError) and exc.log_message:
                    run_logs.append(exc.log_message)
                error_message = str(exc)
                insert_event(engine, run_id, "error", f"attempt {attempt} failed", {"error": error_message})
                if attempt > cfg.retries:
                    break
                time.sleep(60 * attempt)

        # --- Determine final status: OK / WARNING / NOK ---
        critical_nok = [m for m in all_module_markers if m.critical and m.status != "OK"]
        noncritical_nok = [m for m in all_module_markers if not m.critical and m.status != "OK"]

        if ok and critical_nok:
            # A critical module failed inside a step that didn't raise (shouldn't happen normally)
            ok = False
            error_message = f"Critical module(s) failed: {', '.join(m.module_id for m in critical_nok)}"
        elif ok and noncritical_nok:
            warning = True

        aggregated_log = "\n\n".join(chunk for chunk in run_logs if chunk).strip()
        if len(aggregated_log) > 60000:
            aggregated_log = aggregated_log[-60000:]

        # Determine status string
        if ok and not warning:
            final_status = "success"
            monitor_status = "success"
        elif ok and warning:
            final_status = "warning"
            monitor_status = "warning"
        else:
            final_status = "failed"
            monitor_status = "failed"

        set_run_status(engine, run_id, final_status, error_message=error_message if not ok else None)
        monitor.finish(
            status=monitor_status,
            error_message=error_message if not ok else None,
            context={
                "pipeline_id": cfg.pipeline_id,
                "run_id": run_id,
                "trigger_type": trigger_source,
                "owner": cfg.owner,
                "criticality": cfg.criticality,
                "log_message": aggregated_log or None,
                "warning_modules": [m.module_id for m in noncritical_nok] if warning else None,
            },
        )
        insert_event(engine, run_id, "info", f"run {final_status}", None)
        safe_print(f"run_id={run_id} status={final_status}")
        run_exit_code = 0 if ok else 1

    except Exception as exc:
        error_text = str(exc)
        set_run_status(engine, run_id, "failed", error_message=error_text)
        monitor.finish(
            status="failed",
            error_message=error_text,
            context={
                "pipeline_id": cfg.pipeline_id,
                "run_id": run_id,
                "trigger_type": trigger_source,
                "owner": cfg.owner,
                "criticality": cfg.criticality,
                "log_message": error_text,
            },
        )
        safe_print(f"run_id={run_id} status=failed error={exc}")
        run_exit_code = 1

    export_rc = cmd_export()
    if export_rc == 0:
        safe_print(f"run_id={run_id} export=ok")
    else:
        safe_print(f"run_id={run_id} export=failed code={export_rc}")

    if run_exit_code == 0 and export_rc != 0:
        return 1
    return run_exit_code


def _resolve_step_command(cfg: PipelineCfg, step: dict[str, Any]) -> str:
    """Pick the right command string considering OS and entrypoint_windows."""
    cmd = str(step.get("run") or "").strip()
    if not cmd:
        raise RuntimeError(f"Step '{step.get('id', 'step')}' sem comando.")
    # If this is the synthetic entrypoint step and there's a Windows override
    if IS_WINDOWS and step.get("id") == "entrypoint" and cfg.entrypoint_windows:
        return cfg.entrypoint_windows
    return cmd


def _parse_module_marker(line: str) -> dict[str, Any] | None:
    """Parse a @@OVERSEER_MODULE@@{...} line. Returns dict or None."""
    idx = line.find(MARKER_PREFIX)
    if idx < 0:
        return None
    json_str = line[idx + len(MARKER_PREFIX):]
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


def run_step(
    engine,
    cfg: PipelineCfg,
    run_id: int,
    step: dict[str, Any],
    attempt: int,
    monitor: OverseerMonitor,
    trigger_source: str = "manual",
) -> tuple[str | None, list[ModuleMarker]]:
    """Execute a single step, streaming stdout and capturing lineage markers.

    Returns (log_text, list_of_module_markers).
    """
    step_id = str(step.get("id") or "step")
    step_critical = step.get("critical", True)
    cmd = _resolve_step_command(cfg, step)

    step_row = insert_step(engine, run_id, step_id, attempt, "running")
    started = time.time()
    parent = None
    if isinstance(step.get("needs"), list) and step.get("needs"):
        parent = str(step["needs"][0])
    step_ctx = {
        "pipeline_id": cfg.pipeline_id,
        "run_id": run_id,
        "attempt_id": step_row,
        "trigger_type": trigger_source,
        "owner": cfg.owner,
        "criticality": cfg.criticality,
        "script_command": cmd,
    }

    # Track module markers discovered in stdout
    active_modules: dict[str, ModuleMarker] = {}
    finished_modules: list[ModuleMarker] = []

    step_log: str | None = None
    step_finalized = False
    stdout_lines: list[str] = []
    stderr_text = ""
    try:
        with monitor.step(step_id, parent_module_id=parent, context=step_ctx):
            child_env = os.environ.copy()
            child_env["OVERSEER_ORCHESTRATOR_MANAGED"] = "1"
            child_env.update(_runtime_ctx.env_export())
            # Ensure overseer_sdk is importable in all child pipelines
            _existing_pypath = child_env.get("PYTHONPATH", "")
            child_env["PYTHONPATH"] = (
                f"{ROOT}{os.pathsep}{_existing_pypath}" if _existing_pypath else str(ROOT)
            )
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(cfg.root_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
            )
            # Stream stdout line-by-line for real-time marker parsing
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.rstrip("\n\r")
                marker = _parse_module_marker(line)
                if marker:
                    _process_marker(marker, active_modules, finished_modules)
                else:
                    stdout_lines.append(line)

            stderr_text = sanitize_log_text(proc.stderr.read() if proc.stderr else "")
            proc.wait(timeout=cfg.timeout_sec)
            returncode = proc.returncode

            duration = time.time() - started
            stdout_text = sanitize_log_text("\n".join(stdout_lines))
            parts = [f"[{step_id}] exit_code={returncode}"]
            if stdout_text:
                parts.append(f"STDOUT:\n{stdout_text}")
            if stderr_text:
                parts.append(f"STDERR:\n{stderr_text}")
            joined = "\n\n".join(parts).strip()
            if len(joined) > 20000:
                joined = joined[-20000:]
            step_log = joined or None
            if step_log:
                step_ctx["log_message"] = step_log

            # Write module markers to DB
            _persist_module_markers(
                monitor, finished_modules, cfg, run_id, step_id, step_ctx
            )

            if returncode != 0:
                msg = (stderr_text or stdout_text or f"exit code {returncode}")[:1200]
                finalize_step(engine, step_row, "failed", duration, returncode, msg)
                step_finalized = True
                raise StepExecutionError(f"Step {step_id} falhou: {msg}", log_message=step_log)

            finalize_step(engine, step_row, "success", duration, returncode, None)
            step_finalized = True
            insert_event(engine, run_id, "info", f"step {step_id} success", {"duration_sec": round(duration, 3)})
            return step_log, finished_modules
    except Exception as exc:
        duration = time.time() - started
        if not step_finalized:
            finalize_step(engine, step_row, "failed", duration, -1, str(exc))
        if not step_ctx.get("log_message"):
            step_ctx["log_message"] = sanitize_log_text(str(exc))[:20000]
        raise


def _process_marker(
    marker: dict[str, Any],
    active: dict[str, ModuleMarker],
    finished: list[ModuleMarker],
) -> None:
    """Process a parsed @@OVERSEER_MODULE@@ JSON payload."""
    event = marker.get("event", "")
    module_id = marker.get("module_id", "")
    if not module_id:
        return

    if event == "start":
        m = ModuleMarker(
            module_id=module_id,
            critical=marker.get("critical", True),
            parent_module_id=marker.get("parent_module_id"),
            started_at=time.time(),
            context=marker.get("context") or {},
        )
        active[module_id] = m
    elif event == "end":
        m = active.pop(module_id, None)
        if m is None:
            # End without start — create a synthetic marker
            m = ModuleMarker(
                module_id=module_id,
                critical=marker.get("critical", True),
                started_at=time.time(),
            )
        m.ended_at = time.time()
        m.status = marker.get("status", "OK")
        m.message = marker.get("message")
        if marker.get("context"):
            m.context.update(marker["context"])
        finished.append(m)


def _persist_module_markers(
    monitor: OverseerMonitor,
    markers: list[ModuleMarker],
    cfg: PipelineCfg,
    run_id: int,
    step_id: str,
    step_ctx: dict[str, Any],
) -> None:
    """Write accumulated module markers to the pipeline_module_events table."""
    from overseer_monitor.db.writer import write_module_event_record

    for m in markers:
        started_dt = datetime.fromtimestamp(m.started_at) if m.started_at else datetime.now()
        ended_dt = datetime.fromtimestamp(m.ended_at) if m.ended_at else datetime.now()
        duration = max(0.0, (ended_dt - started_dt).total_seconds())
        ctx_json = {
            **step_ctx,
            "critical": m.critical,
            **(m.context or {}),
        }
        record = {
            "pipelineId": cfg.pipeline_id,
            "runId": run_id,
            "moduleId": m.module_id,
            "parentModuleId": m.parent_module_id,
            "status": "OK" if m.status.upper() in ("OK", "SUCCESS") else "NOK",
            "startedAt": started_dt,
            "endedAt": ended_dt,
            "durationSec": round(duration, 3),
            "errorMessage": m.message if m.status.upper() not in ("OK", "SUCCESS") else None,
            "logMessage": m.message,
            "owner": cfg.owner,
            "criticality": "non-critical" if not m.critical else cfg.criticality,
            "hostname": monitor.hostname,
            "triggerType": step_ctx.get("trigger_type"),
            "contextJson": json.dumps(ctx_json, ensure_ascii=False, default=str),
            "regDate": datetime.now(),
        }
        try:
            write_module_event_record(
                monitor.module_events_table,
                monitor.db_params,
                record,
            )
        except Exception as exc:
            safe_print(f"[WARN] Failed to persist module marker {m.module_id}: {exc}")


def sanitize_log_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = ANSI_ESCAPE_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def build_execution_plan(cfg: PipelineCfg) -> list[dict[str, Any]]:
    if cfg.entrypoint:
        return [{"id": "entrypoint", "run": cfg.entrypoint, "needs": [], "critical": True}]
    steps = cfg.steps
    by_id = {str(s.get("id")): s for s in steps}
    # Ensure each step has a 'critical' flag (default True)
    for s in steps:
        if "critical" not in s:
            s["critical"] = True
    indegree = {k: 0 for k in by_id}
    graph: dict[str, list[str]] = {k: [] for k in by_id}
    for sid, step in by_id.items():
        needs = step.get("needs") or []
        for dep in needs:
            dep = str(dep)
            if dep not in by_id:
                raise ValueError(f"Step '{sid}' depende de '{dep}' inexistente.")
            graph[dep].append(sid)
            indegree[sid] += 1
    queue = [k for k, deg in indegree.items() if deg == 0]
    order: list[str] = []
    while queue:
        sid = queue.pop(0)
        order.append(sid)
        for nxt in graph[sid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(by_id):
        raise ValueError("DAG invalido: ciclo detectado nos steps.")
    return [by_id[sid] for sid in order]


def ensure_tables(engine) -> None:
    stmts = [
        """
        CREATE TABLE IF NOT EXISTS orchestrator_runs_local (
          run_local_id BIGINT AUTO_INCREMENT PRIMARY KEY,
          pipeline_id VARCHAR(255) NOT NULL,
          pipeline_name VARCHAR(255) NOT NULL,
          status VARCHAR(32) NOT NULL,
          requested_by VARCHAR(255) NULL,
          trigger_source VARCHAR(64) NULL,
          runner_host VARCHAR(255) NULL,
          retries INT NOT NULL DEFAULT 2,
          timeout_sec INT NOT NULL DEFAULT 3600,
          error_message MEDIUMTEXT NULL,
          started_at DATETIME NOT NULL,
          ended_at DATETIME NULL,
          created_at DATETIME NOT NULL,
          updated_at DATETIME NOT NULL,
          INDEX idx_orch_local_pipeline_status (pipeline_id, status),
          INDEX idx_orch_local_created (created_at)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orchestrator_triggers_local (
          trigger_local_id BIGINT AUTO_INCREMENT PRIMARY KEY,
          trigger_id VARCHAR(64) NOT NULL,
          pipeline_id VARCHAR(255) NOT NULL,
          requested_by VARCHAR(255) NULL,
          requested_at DATETIME NOT NULL,
          source VARCHAR(64) NULL,
          runner_host VARCHAR(255) NULL,
          status VARCHAR(32) NOT NULL,
          notes VARCHAR(1024) NULL,
          claimed_by VARCHAR(255) NULL,
          claimed_at DATETIME NULL,
          consumed_at DATETIME NULL,
          error_message MEDIUMTEXT NULL,
          created_at DATETIME NOT NULL,
          updated_at DATETIME NOT NULL,
          UNIQUE KEY uq_orch_trigger_id (trigger_id),
          INDEX idx_orch_trigger_status_req (status, requested_at),
          INDEX idx_orch_trigger_pipeline (pipeline_id),
          INDEX idx_orch_trigger_runner (runner_host, status)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orchestrator_steps_local (
          step_local_id BIGINT AUTO_INCREMENT PRIMARY KEY,
          run_local_id BIGINT NOT NULL,
          step_id VARCHAR(255) NOT NULL,
          attempt_no INT NOT NULL,
          status VARCHAR(32) NOT NULL,
          exit_code INT NULL,
          error_message MEDIUMTEXT NULL,
          duration_sec DECIMAL(18,3) NULL,
          started_at DATETIME NOT NULL,
          ended_at DATETIME NULL,
          created_at DATETIME NOT NULL,
          INDEX idx_orch_local_steps_run (run_local_id, step_id, attempt_no)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orchestrator_events_local (
          event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
          run_local_id BIGINT NOT NULL,
          level VARCHAR(16) NOT NULL,
          message VARCHAR(1024) NOT NULL,
          payload_json JSON NULL,
          created_at DATETIME NOT NULL,
          INDEX idx_orch_local_events_run (run_local_id, event_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pipeline_module_events (
          event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
          pipelineId VARCHAR(255) NOT NULL,
          runId BIGINT NULL,
          moduleId VARCHAR(255) NOT NULL,
          parentModuleId VARCHAR(255) NULL,
          status VARCHAR(20) NOT NULL,
          startedAt DATETIME NOT NULL,
          endedAt DATETIME NOT NULL,
          durationSec DECIMAL(18,3) NULL,
          errorMessage MEDIUMTEXT NULL,
          logMessage MEDIUMTEXT NULL,
          owner VARCHAR(255) NULL,
          criticality VARCHAR(32) NULL,
          hostname VARCHAR(255) NULL,
          triggerType VARCHAR(32) NULL,
          contextJson JSON NULL,
          regDate DATETIME NULL,
          INDEX idx_module_pipeline_run (pipelineId, runId),
          INDEX idx_module_pipeline_module (pipelineId, moduleId),
          INDEX idx_module_started (startedAt),
          INDEX idx_module_status (status)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS overseer_pipeline_permissions (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(255) NOT NULL,
          pipeline_id VARCHAR(255) NOT NULL,
          role VARCHAR(32) NOT NULL DEFAULT 'executor',
          granted_at DATETIME NOT NULL,
          granted_by VARCHAR(255) NULL,
          UNIQUE KEY uq_user_pipeline (username, pipeline_id),
          INDEX idx_perm_pipeline (pipeline_id)
        )
        """,
    ]
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))
        _ensure_optional_column(conn, "orchestrator_runs_local", "pipeline_name", "VARCHAR(255) NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "requested_by", "VARCHAR(255) NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "trigger_source", "VARCHAR(64) NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "retries", "INT NOT NULL DEFAULT 2")
        _ensure_optional_column(conn, "orchestrator_runs_local", "timeout_sec", "INT NOT NULL DEFAULT 3600")
        _ensure_optional_column(conn, "orchestrator_runs_local", "error_message", "MEDIUMTEXT NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "started_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "ended_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "created_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "updated_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_runs_local", "runner_host", "VARCHAR(255) NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "updated_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "claimed_by", "VARCHAR(255) NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "claimed_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "consumed_at", "DATETIME NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "error_message", "MEDIUMTEXT NULL")
        _ensure_optional_column(conn, "orchestrator_triggers_local", "notes", "VARCHAR(1024) NULL")
        try:
            _ensure_optional_column(conn, settings.runs_table, "osName", "VARCHAR(128) NULL")
            _ensure_optional_column(conn, settings.runs_table, "osRelease", "VARCHAR(128) NULL")
            _ensure_optional_column(conn, settings.runs_table, "osPlatform", "VARCHAR(255) NULL")
            _ensure_optional_column(conn, settings.runs_table, "triggerType", "VARCHAR(64) NULL")
        except Exception:
            pass
        _ensure_optional_column(conn, "pipeline_module_events", "logMessage", "MEDIUMTEXT NULL")
        _ensure_optional_column(conn, "pipeline_module_events", "owner", "VARCHAR(255) NULL")
        _ensure_optional_column(conn, "pipeline_module_events", "criticality", "VARCHAR(32) NULL")


def _ensure_optional_column(conn, table_name: str, column_name: str, column_type_sql: str) -> None:
    exists_sql = text(
        """
        SELECT COUNT(*) AS c
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
          AND COLUMN_NAME = :column_name
        """
    )
    row = conn.execute(exists_sql, {"table_name": table_name, "column_name": column_name}).mappings().first()
    present = int(row["c"]) > 0 if row and row.get("c") is not None else 0
    if present:
        return
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_sql}"))


def insert_run(engine, cfg: PipelineCfg, requested_by: str, trigger_source: str) -> int:
    sql = text(
        """
        INSERT INTO orchestrator_runs_local (
          pipeline_id, pipeline_name, status, requested_by, trigger_source, runner_host, retries, timeout_sec,
          error_message, started_at, ended_at, created_at, updated_at
        ) VALUES (
          :pipeline_id, :pipeline_name, 'queued', :requested_by, :trigger_source, :runner_host, :retries, :timeout_sec,
          NULL, UTC_TIMESTAMP(), NULL, UTC_TIMESTAMP(), UTC_TIMESTAMP()
        )
        """
    )
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "pipeline_id": cfg.pipeline_id,
                "pipeline_name": cfg.name,
                "requested_by": requested_by,
                "trigger_source": trigger_source,
                "runner_host": normalize_runner_name(None),
                "retries": cfg.retries,
                "timeout_sec": cfg.timeout_sec,
            },
        )
        run_id = int(result.lastrowid)
    insert_event(engine, run_id, "info", "run queued", {"pipeline_id": cfg.pipeline_id})
    return run_id


def set_run_status(engine, run_id: int, status: str, error_message: str | None = None) -> None:
    sql = text(
        """
        UPDATE orchestrator_runs_local
        SET status = :status,
            error_message = :error_message,
            ended_at = CASE WHEN :status IN ('success','failed') THEN UTC_TIMESTAMP() ELSE ended_at END,
            updated_at = UTC_TIMESTAMP()
        WHERE run_local_id = :run_id
        """
    )
    with engine.begin() as conn:
        conn.execute(sql, {"run_id": run_id, "status": status, "error_message": error_message})


def insert_step(engine, run_id: int, step_id: str, attempt: int, status: str) -> int:
    sql = text(
        """
        INSERT INTO orchestrator_steps_local (
          run_local_id, step_id, attempt_no, status, exit_code, error_message,
          duration_sec, started_at, ended_at, created_at
        ) VALUES (
          :run_id, :step_id, :attempt_no, :status, NULL, NULL,
          NULL, UTC_TIMESTAMP(), NULL, UTC_TIMESTAMP()
        )
        """
    )
    with engine.begin() as conn:
        result = conn.execute(sql, {"run_id": run_id, "step_id": step_id, "attempt_no": attempt, "status": status})
        return int(result.lastrowid)


def finalize_step(engine, step_row: int, status: str, duration: float, exit_code: int, error_message: str | None) -> None:
    sql = text(
        """
        UPDATE orchestrator_steps_local
        SET status = :status,
            exit_code = :exit_code,
            error_message = :error_message,
            duration_sec = :duration_sec,
            ended_at = UTC_TIMESTAMP()
        WHERE step_local_id = :step_id
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "step_id": step_row,
                "status": status,
                "exit_code": exit_code,
                "error_message": error_message,
                "duration_sec": round(duration, 3),
            },
        )


def insert_event(engine, run_id: int, level: str, message: str, payload: dict[str, Any] | None) -> None:
    sql = text(
        """
        INSERT INTO orchestrator_events_local (run_local_id, level, message, payload_json, created_at)
        VALUES (:run_id, :level, :message, :payload, UTC_TIMESTAMP())
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "run_id": run_id,
                "level": level,
                "message": message,
                "payload": json.dumps(payload, ensure_ascii=False) if payload else None,
            },
        )


def insert_trigger(engine, trigger: dict[str, Any]) -> None:
    sql = text(
        """
        INSERT INTO orchestrator_triggers_local (
          trigger_id, pipeline_id, requested_by, requested_at, source, runner_host, status, notes,
          claimed_by, claimed_at, consumed_at, error_message, created_at, updated_at
        ) VALUES (
          :trigger_id, :pipeline_id, :requested_by, UTC_TIMESTAMP(), :source, :runner_host, 'queued', :notes,
          NULL, NULL, NULL, NULL, UTC_TIMESTAMP(), UTC_TIMESTAMP()
        )
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "trigger_id": trigger["trigger_id"],
                "pipeline_id": trigger["pipeline_id"],
                "requested_by": trigger.get("requested_by"),
                "source": trigger.get("source"),
                "runner_host": normalize_runner_name(trigger.get("runner_host")),
                "notes": trigger.get("notes"),
            },
        )


def consume_triggers(runner: str | None, max_items: int = 10) -> int:
    engine = get_engine()
    ensure_tables(engine)
    runner_name = normalize_runner_name(runner)
    max_items = max(1, min(max_items, 200))
    processed = 0
    _release_stale_claims(engine, stale_minutes=15)

    for _ in range(max_items):
        trigger = _claim_next_trigger(engine, runner_name)
        if not trigger:
            break

        trigger_id = int(trigger["trigger_local_id"])
        pipeline_id = str(trigger.get("pipeline_id") or "")
        cfg = find_pipeline(pipeline_id)
        if not cfg:
            _finalize_trigger(engine, trigger_id, "failed", error_message="pipeline nao encontrada")
            processed += 1
            continue

        if cfg.runner_host and cfg.runner_host != "any" and normalize_runner_name(cfg.runner_host) != runner_name:
            _finalize_trigger(engine, trigger_id, "queued", error_message=None, release_claim=True)
            continue

        rc = execute_pipeline(
            cfg,
            requested_by=str(trigger.get("requested_by") or "trigger"),
            trigger_source="trigger_db",
        )
        _finalize_trigger(engine, trigger_id, "consumed" if rc == 0 else "failed", error_message=None if rc == 0 else "execucao falhou")
        processed += 1

    safe_print(f"Runner={runner_name} | Triggers processados: {processed}")
    return 0


def consume_file_triggers(
    channel_root: Path,
    runner: str | None,
    max_items: int = 20,
    poll_seconds: float = 2.0,
    once: bool = False,
) -> int:
    runner_name = normalize_runner_name(runner)
    max_items = max(1, min(max_items, 500))
    poll_seconds = max(0.5, min(poll_seconds, 60.0))
    channel = _ensure_file_channel(channel_root)

    total = 0
    while True:
        processed = _consume_file_cycle(channel, runner_name, max_items)
        total += processed
        if once:
            safe_print(f"Runner={runner_name} | Triggers processados (ciclo unico): {processed}")
            return 0
        time.sleep(poll_seconds)


def _ensure_file_channel(channel_root: Path) -> dict[str, Path]:
    pending = channel_root / "pending"
    processing = channel_root / "processing"
    done = channel_root / "done"
    failed = channel_root / "failed"
    for p in (pending, processing, done, failed):
        p.mkdir(parents=True, exist_ok=True)
    return {"root": channel_root, "pending": pending, "processing": processing, "done": done, "failed": failed}


def _consume_file_cycle(channel: dict[str, Path], runner_name: str, max_items: int) -> int:
    pending_files = sorted(channel["pending"].glob("*.json"), key=lambda p: p.stat().st_mtime)
    processed = 0
    for src in pending_files:
        if processed >= max_items:
            break
        dst = channel["processing"] / src.name
        try:
            src.replace(dst)
        except OSError:
            continue

        payload: dict[str, Any] = {}
        try:
            payload = json.loads(dst.read_text(encoding="utf-8"))
        except Exception as exc:
            _write_trigger_result(dst, channel["failed"], "failed", f"json invalido: {exc}", payload)
            _persist_file_trigger(payload, "failed", f"json invalido: {exc}", runner_name)
            processed += 1
            continue

        pipeline_id = str(payload.get("pipeline_id") or payload.get("pipelineId") or "").strip()
        if not pipeline_id:
            _write_trigger_result(dst, channel["failed"], "failed", "pipeline_id ausente", payload)
            _persist_file_trigger(payload, "failed", "pipeline_id ausente", runner_name)
            processed += 1
            continue

        cfg = find_pipeline(pipeline_id)
        if not cfg:
            payload["pipeline_id"] = pipeline_id
            _write_trigger_result(dst, channel["failed"], "failed", "pipeline nao encontrada", payload)
            _persist_file_trigger(payload, "failed", "pipeline nao encontrada", runner_name)
            processed += 1
            continue

        target_runner = resolve_pipeline_runner_host(payload.get("runner_host") or cfg.runner_host)
        if target_runner not in {"any", runner_name}:
            # devolve ao pending para outro runner
            back = channel["pending"] / dst.name
            try:
                dst.replace(back)
            except OSError:
                _write_trigger_result(dst, channel["failed"], "failed", "nao foi possivel devolver trigger ao pending", payload)
                _persist_file_trigger(payload, "failed", "nao foi possivel devolver trigger ao pending", runner_name)
                processed += 1
            continue

        requested_by = str(payload.get("requested_by") or "run-now")
        rc = execute_pipeline(cfg, requested_by=requested_by, trigger_source="trigger_file")
        final_status = "consumed" if rc == 0 else "failed"
        final_error = None if rc == 0 else "execucao falhou"
        _write_trigger_result(
            dst,
            channel["done"] if rc == 0 else channel["failed"],
            final_status,
            final_error,
            payload,
        )
        _persist_file_trigger(payload, final_status, final_error, runner_name)
        processed += 1
    return processed


def _persist_file_trigger(payload: dict[str, Any], status: str, error_message: str | None, runner_name: str) -> None:
    """Write file-trigger result into orchestrator_triggers_local so the frontend sees it."""
    trigger_id = str(payload.get("trigger_id") or payload.get("triggerId") or "").strip()
    pipeline_id = str(payload.get("pipeline_id") or payload.get("pipelineId") or "").strip()
    if not trigger_id and not pipeline_id:
        return

    # Normalize requested_at to MySQL-compatible format
    raw_at = payload.get("requested_at") or payload.get("requestedAt")
    requested_at_str: str | None = None
    if raw_at:
        try:
            dt = datetime.fromisoformat(str(raw_at).replace("Z", "+00:00"))
            requested_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            requested_at_str = None

    try:
        engine = get_engine()
        sql = text(
            """
            INSERT INTO orchestrator_triggers_local (
              trigger_id, pipeline_id, requested_by, requested_at, source, runner_host,
              status, notes, claimed_by, claimed_at, consumed_at, error_message, updated_at
            ) VALUES (
              :trigger_id, :pipeline_id, :requested_by,
              COALESCE(:requested_at, UTC_TIMESTAMP()),
              :source, :runner_host, :status, :notes, :runner_name,
              UTC_TIMESTAMP(),
              CASE WHEN :status IN ('consumed','failed') THEN UTC_TIMESTAMP() ELSE NULL END,
              :error_message, UTC_TIMESTAMP()
            )
            ON DUPLICATE KEY UPDATE
              status = VALUES(status),
              error_message = VALUES(error_message),
              consumed_at = VALUES(consumed_at),
              updated_at = UTC_TIMESTAMP()
            """
        )
        with engine.begin() as conn:
            conn.execute(sql, {
                "trigger_id": trigger_id or f"file-{uuid.uuid4().hex[:12]}",
                "pipeline_id": pipeline_id or "unknown",
                "requested_by": payload.get("requested_by"),
                "requested_at": requested_at_str,
                "source": payload.get("source") or "trigger_file",
                "runner_host": runner_name,
                "status": status,
                "notes": payload.get("notes"),
                "runner_name": runner_name,
                "error_message": error_message,
            })
    except Exception as exc:
        safe_print(f"[warn] _persist_file_trigger: {exc}")


def _write_trigger_result(src_path: Path, target_dir: Path, status: str, error_message: str | None, payload: dict[str, Any]) -> None:
    payload["status"] = status
    payload["updated_at"] = now_iso()
    if error_message:
        payload["error_message"] = error_message
    result_path = target_dir / src_path.name
    tmp = result_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(result_path)
    src_path.unlink(missing_ok=True)


def _release_stale_claims(engine, stale_minutes: int) -> None:
    stale_minutes = max(1, min(stale_minutes, 240))
    sql = text(
        f"""
        UPDATE orchestrator_triggers_local
        SET status = 'queued',
            claimed_by = NULL,
            claimed_at = NULL,
            updated_at = UTC_TIMESTAMP()
        WHERE status = 'claimed'
          AND claimed_at < (UTC_TIMESTAMP() - INTERVAL {stale_minutes} MINUTE)
        """
    )
    with engine.begin() as conn:
        conn.execute(sql)


def _claim_next_trigger(engine, runner_name: str) -> dict[str, Any] | None:
    claim_sql = text(
        """
        UPDATE orchestrator_triggers_local
        SET status = 'claimed',
            claimed_by = :runner_name,
            claimed_at = UTC_TIMESTAMP(),
            updated_at = UTC_TIMESTAMP()
        WHERE trigger_local_id = (
          SELECT x.trigger_local_id FROM (
            SELECT trigger_local_id
            FROM orchestrator_triggers_local
            WHERE status = 'queued'
              AND (
                runner_host IS NULL
                OR runner_host = ''
                OR LOWER(runner_host) = 'any'
                OR LOWER(runner_host) = LOWER(:runner_name)
              )
            ORDER BY requested_at ASC, trigger_local_id ASC
            LIMIT 1
          ) x
        )
          AND status = 'queued'
        """
    )
    pick_sql = text(
        """
        SELECT trigger_local_id, trigger_id, pipeline_id, requested_by, source, runner_host, notes
        FROM orchestrator_triggers_local
        WHERE status = 'claimed'
          AND LOWER(claimed_by) = LOWER(:runner_name)
        ORDER BY claimed_at DESC, trigger_local_id DESC
        LIMIT 1
        """
    )
    with engine.begin() as conn:
        updated = conn.execute(claim_sql, {"runner_name": runner_name}).rowcount or 0
        if updated == 0:
            return None
        row = conn.execute(pick_sql, {"runner_name": runner_name}).mappings().first()
        return dict(row) if row else None


def _finalize_trigger(engine, trigger_local_id: int, status: str, error_message: str | None, release_claim: bool = False) -> None:
    if release_claim:
        sql = text(
            """
            UPDATE orchestrator_triggers_local
            SET status = :status,
                claimed_by = NULL,
                claimed_at = NULL,
                error_message = :error_message,
                updated_at = UTC_TIMESTAMP()
            WHERE trigger_local_id = :trigger_local_id
            """
        )
    else:
        sql = text(
            """
            UPDATE orchestrator_triggers_local
            SET status = :status,
                error_message = :error_message,
                consumed_at = CASE WHEN :status IN ('consumed','failed') THEN UTC_TIMESTAMP() ELSE consumed_at END,
                updated_at = UTC_TIMESTAMP()
            WHERE trigger_local_id = :trigger_local_id
            """
        )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "trigger_local_id": trigger_local_id,
                "status": status,
                "error_message": error_message,
            },
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_runner_name(name: str | None) -> str:
    value = (name or socket.gethostname()).strip().lower()
    return value or "unknown-runner"


def resolve_pipeline_runner_host(value: Any) -> str | None:
    if value is None:
        return normalize_runner_name(None)
    text = str(value).strip()
    if not text:
        return normalize_runner_name(None)
    normalized = normalize_runner_name(text)
    if normalized in {"auto", "local", "localhost", "this-host", "self"}:
        return normalize_runner_name(None)
    if normalized in {"any", "*"}:
        return "any"
    return normalized


def db_params_from_url(db_url: str) -> dict[str, Any]:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(db_url)
    query = parse_qs(parsed.query)
    return {
        "host": parsed.hostname or "localhost",
        "port": int(parsed.port or 3306),
        "user": parsed.username,
        "password": parsed.password,
        "database": (parsed.path or "/").lstrip("/"),
        "charset": query.get("charset", ["utf8mb4"])[0],
    }


# ══════════════════════════════════════════════════════════════════════
# SCHEDULE MANAGEMENT — view & modify pipeline schedules via YAML
# ══════════════════════════════════════════════════════════════════════

def cmd_schedule(args: argparse.Namespace) -> int:
    """Route schedule sub-commands."""
    if args.schedule_cmd == "set":
        return cmd_schedule_set(args)
    if args.schedule_cmd == "show":
        return cmd_schedule_show(args)
    safe_print("Uso: orchestrator.py schedule {set|show}")
    return 2


def cmd_schedule_set(args: argparse.Namespace) -> int:
    """Change the schedule or config of a pipeline by rewriting its YAML file."""
    pipeline_id = str(args.pipeline_id).strip()
    new_schedule = str(getattr(args, "new_schedule", "")).strip()
    new_criticality = str(getattr(args, "criticality", "")).strip()
    new_owner = str(getattr(args, "owner", "")).strip()
    requested_by = str(getattr(args, "by", "cli")).strip()

    if new_schedule and new_schedule.lower() not in {"manual", "paused"} and not croniter.is_valid(new_schedule):
        safe_print(f"[schedule] Expressao cron invalida: {new_schedule}")
        return 1

    cfg = find_pipeline(pipeline_id)
    if not cfg:
        safe_print(f"[schedule] Pipeline nao encontrada: {pipeline_id}")
        return 1

    yaml_path = cfg.definition_path
    try:
        raw_text = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text) or {}
    except Exception as exc:
        safe_print(f"[schedule] Erro ao ler YAML {yaml_path}: {exc}")
        return 1

    if new_schedule:
        old_schedule = data.get("schedule", "manual")
        data["schedule"] = new_schedule

        # Preserve/restore prev_schedule when pausing/resuming
        if new_schedule.lower() == "paused" and old_schedule.lower() not in {"manual", "paused"}:
            data["prev_schedule"] = old_schedule
        elif old_schedule.lower() == "paused" and new_schedule.lower() != "paused":
            data.pop("prev_schedule", None)
            
    if new_criticality:
        data["criticality"] = new_criticality
    if new_owner:
        data["owner"] = new_owner

    # Atomic write
    tmp_path = yaml_path.with_suffix(".yaml.tmp")
    try:
        tmp_path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        tmp_path.replace(yaml_path)
    except Exception as exc:
        safe_print(f"[schedule] Erro ao escrever YAML: {exc}")
        tmp_path.unlink(missing_ok=True)
        return 1

    safe_print(f"[schedule] {pipeline_id}: schedule alterado de '{old_schedule}' para '{new_schedule}' por {requested_by}")
    return 0


def cmd_schedule_show(args: argparse.Namespace) -> int:
    """Show current schedule for one or all pipelines."""
    pipeline_id = getattr(args, "pipeline_id", None)
    pipelines = load_all_pipelines()
    if pipeline_id:
        pipelines = [p for p in pipelines if p.pipeline_id == pipeline_id]
        if not pipelines:
            safe_print(f"[schedule] Pipeline nao encontrada: {pipeline_id}")
            return 1
    safe_print(f"{'Pipeline':<35} {'Schedule':<25} {'Runner Host':<20}")
    safe_print("-" * 80)
    for p in pipelines:
        safe_print(f"{p.pipeline_id:<35} {p.schedule or 'manual':<25} {p.runner_host or 'auto':<20}")
    return 0


def consume_schedule_triggers() -> int:
    """Consume schedule change trigger files from the frontend."""
    if not SCHEDULE_TRIGGER_DIR.exists():
        return 0
    pending = SCHEDULE_TRIGGER_DIR / "pending"
    done = SCHEDULE_TRIGGER_DIR / "done"
    failed = SCHEDULE_TRIGGER_DIR / "failed"
    for d in (pending, done, failed):
        d.mkdir(parents=True, exist_ok=True)

    processed = 0
    for src in sorted(pending.glob("schedule-*.json"), key=lambda p: p.stat().st_mtime):
        try:
            payload = json.loads(src.read_text(encoding="utf-8"))
        except Exception as exc:
            safe_print(f"[schedule-trigger] JSON invalido em {src.name}: {exc}")
            src.replace(failed / src.name)
            processed += 1
            continue

        pipeline_id = str(payload.get("pipeline_id", "")).strip()
        new_schedule = str(payload.get("new_schedule", payload.get("schedule", ""))).strip()
        new_criticality = str(payload.get("criticality", "")).strip()
        new_owner = str(payload.get("owner", "")).strip()
        requested_by = str(payload.get("requested_by", "frontend")).strip()

        if not pipeline_id:
            safe_print(f"[schedule-trigger] Campos ausentes em {src.name}")
            src.replace(failed / src.name)
            processed += 1
            continue

        if new_schedule and new_schedule.lower() not in {"manual", "paused"} and not croniter.is_valid(new_schedule):
            safe_print(f"[schedule-trigger] Cron invalido em {src.name}: {new_schedule}")
            payload["error_message"] = f"cron invalido: {new_schedule}"
            (failed / src.name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            src.unlink(missing_ok=True)
            processed += 1
            continue

        # Build a minimal args namespace for cmd_schedule_set
        ns = argparse.Namespace(
            pipeline_id=pipeline_id, 
            new_schedule=new_schedule,
            criticality=new_criticality,
            owner=new_owner,
            by=requested_by
        )
        rc = cmd_schedule_set(ns)
        if rc == 0:
            payload["status"] = "consumed"
            payload["updated_at"] = now_iso()
            (done / src.name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            src.unlink(missing_ok=True)
        else:
            payload["status"] = "failed"
            payload["error_message"] = "cmd_schedule_set falhou"
            payload["updated_at"] = now_iso()
            (failed / src.name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            src.unlink(missing_ok=True)
        processed += 1

    if processed:
        safe_print(f"[schedule-trigger] Processados {processed} triggers de schedule")
    return processed


# ══════════════════════════════════════════════════════════════════════
# REMOTE TRIGGER PULL — fetches triggers from nginx server via SFTP
# ══════════════════════════════════════════════════════════════════════

REMOTE_TRIGGER_DIR = "/usr/share/nginx/html/MAIATRON/apps/overseer/triggers"


def _load_ssh_config() -> dict[str, Any]:
    """Load SSH config from secrets/database.json → ssh block."""
    db_json = ROOT / "secrets" / "database.json"
    if not db_json.exists():
        return {}
    try:
        cfg = json.loads(db_json.read_text(encoding="utf-8"))
        return cfg.get("ssh") or {}
    except Exception:
        return {}


def _resolve_ssh_key(key_filename: str) -> Path:
    """Resolve SSH key file path (same logic as export script)."""
    candidates = [
        ROOT / "secrets" / key_filename,
        ROOT / "pipelines" / "microsoft_forms_2_datalake" / "secrets" / key_filename,
        Path(key_filename),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def consume_remote_triggers() -> int:
    """Pull trigger files from the nginx server via SFTP.

    The frontend POSTs trigger JSON to /MAIATRON/apps/overseer/trigger.php,
    which writes files to the triggers/ directory on the server.
    This function downloads those files to the local run_now / schedule
    channel directories and deletes them from the remote server.
    """
    ssh_cfg = _load_ssh_config()
    host = str(ssh_cfg.get("host") or "").strip()
    user = str(ssh_cfg.get("user") or "").strip()
    port = int(ssh_cfg.get("port") or 22)
    key_file = str(ssh_cfg.get("key_filename") or "ssh_key").strip()

    if not host or not user:
        return 0

    key_path = _resolve_ssh_key(key_file)
    if not key_path.exists():
        return 0

    try:
        import paramiko
    except ImportError:
        return 0

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    processed = 0

    try:
        client.connect(hostname=host, port=port, username=user,
                        key_filename=str(key_path), timeout=15)
        with client.open_sftp() as sftp:
            try:
                remote_files = sftp.listdir(REMOTE_TRIGGER_DIR)
            except FileNotFoundError:
                return 0

            json_files = sorted(f for f in remote_files if f.endswith(".json"))
            if not json_files:
                return 0

            safe_print(f"[remote-triggers] {len(json_files)} trigger(s) pendente(s) no servidor")

            for fname in json_files:
                remote_path = f"{REMOTE_TRIGGER_DIR}/{fname}"
                try:
                    with sftp.open(remote_path, "r") as rf:
                        raw = rf.read().decode("utf-8")
                    payload = json.loads(raw)
                except Exception as exc:
                    safe_print(f"[remote-triggers] Erro ao ler {fname}: {exc}")
                    # Move to a failed directory remotely or just skip
                    continue

                # Determine target channel based on trigger type
                trigger_type = str(payload.get("type", "")).strip().lower()
                if trigger_type == "schedule_change":
                    # Schedule change trigger → schedule channel
                    local_dir = SCHEDULE_TRIGGER_DIR / "pending"
                    local_dir.mkdir(parents=True, exist_ok=True)
                    local_file = local_dir / fname.replace("trigger-", "schedule-")
                else:
                    # Run now trigger → run_now channel
                    local_dir = DEFAULT_RUN_NOW_DIR / "pending"
                    local_dir.mkdir(parents=True, exist_ok=True)
                    local_file = local_dir / fname

                # Write locally
                local_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                safe_print(f"[remote-triggers] {fname} → {local_file}")

                # Remove from remote
                try:
                    sftp.remove(remote_path)
                except Exception as exc:
                    safe_print(f"[remote-triggers] Aviso: nao foi possivel remover {fname} do servidor: {exc}")

                processed += 1

    except Exception as exc:
        safe_print(f"[remote-triggers] Erro SFTP: {exc}")
    finally:
        client.close()

    if processed:
        safe_print(f"[remote-triggers] {processed} trigger(s) descarregado(s) do servidor")
    return processed


# ══════════════════════════════════════════════════════════════════════
# SCHEDULER DAEMON — replaces cron entirely (cross-platform)
# ══════════════════════════════════════════════════════════════════════

def cmd_scheduler(args: argparse.Namespace) -> int:
    """Built-in scheduler daemon.  Replaces cron/Task Scheduler entirely.

    Every ``tick`` seconds it checks:
    1. Pipeline schedules from YAML (via croniter)
    2. Export payload (every 15 min)
    3. Archive logs (daily at 02:10)
    4. Slack daily digest (daily at 23:59)
    5. Trigger consume from DB (every tick)
    6. Trigger consume from file channel (every tick)
    7. Schedule change triggers (every tick)
    8. Remote triggers from nginx server via SFTP (every tick)
    """
    tick_sec = max(10, args.tick)
    max_workers = max(1, args.workers)
    once = args.once
    runner_name = normalize_runner_name(None)

    safe_print(f"[scheduler] Starting — runner={runner_name} tick={tick_sec}s workers={max_workers} once={once}")
    safe_print(f"[scheduler] PID={os.getpid()} OS={platform.system()}")

    # Graceful shutdown
    def _signal_handler(signum, frame):
        safe_print(f"[scheduler] Received signal {signum}, shutting down...")
        _shutdown_event.set()

    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Load state
    sched_state = _load_scheduler_state()
    last_export = sched_state.get("last_export", 0)
    last_archive = sched_state.get("last_archive", "")
    last_digest = sched_state.get("last_digest", "")
    last_fired: dict[str, float] = sched_state.get("last_fired", {})
    last_yaml_reload: float = 0.0

    pipelines: list[PipelineCfg] = []
    pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sched")

    try:
        while not _shutdown_event.is_set():
            tick_start = time.time()
            now = datetime.now(timezone.utc)
            now_ts = now.timestamp()

            # --- Reload YAML configs every 5 minutes ---
            if now_ts - last_yaml_reload > 300 or not pipelines:
                pipelines = load_all_pipelines()
                last_yaml_reload = now_ts
                safe_print(f"[scheduler] Loaded {len(pipelines)} pipelines")

            # --- 1) Pipeline schedules ---
            for cfg in pipelines:
                if not cfg.schedule or cfg.schedule.lower() in {"manual", "paused"}:
                    continue
                # Respect runner_host
                if cfg.runner_host and cfg.runner_host != "any" and normalize_runner_name(cfg.runner_host) != runner_name:
                    continue
                try:
                    if not croniter.is_valid(cfg.schedule):
                        continue
                    base_time = datetime.fromtimestamp(last_fired.get(cfg.pipeline_id, now_ts - 86400), tz=timezone.utc)
                    cron = croniter(cfg.schedule, base_time)
                    next_fire = cron.get_next(datetime)
                    if next_fire.timestamp() <= now_ts:
                        safe_print(f"[scheduler] Firing {cfg.pipeline_id} (schedule={cfg.schedule})")
                        last_fired[cfg.pipeline_id] = now_ts
                        pool.submit(_safe_execute, cfg, "scheduler", "schedule")
                except Exception as exc:
                    safe_print(f"[scheduler] Error checking schedule for {cfg.pipeline_id}: {exc}")

            # --- 2) Export payload every 15 min ---
            if now_ts - last_export >= 900:
                safe_print("[scheduler] Running export...")
                pool.submit(_safe_run_script, "export_payload_from_db.py")
                last_export = now_ts

            # --- 3) Archive logs daily at 02:10 ---
            today_str = now.strftime("%Y-%m-%d")
            if today_str != last_archive and now.hour >= 2 and now.minute >= 10:
                safe_print("[scheduler] Running archive...")
                pool.submit(_safe_run_script, "archive_logs.py", "--days", "30")
                last_archive = today_str

            # --- 4) Slack daily digest at 23:59 ---
            if today_str != last_digest and now.hour == 23 and now.minute >= 59:
                safe_print("[scheduler] Running daily digest...")
                pool.submit(_safe_run_script, "slack_daily_digest.py")
                last_digest = today_str

            # --- 5) Consume DB triggers ---
            try:
                consume_triggers(runner=runner_name, max_items=10)
            except Exception as exc:
                safe_print(f"[scheduler] Trigger consume error: {exc}")

            # --- 6) Pull remote triggers from nginx server ---
            try:
                consume_remote_triggers()
            except Exception as exc:
                safe_print(f"[scheduler] Remote trigger pull error: {exc}")

            # --- 7) Consume file triggers ---
            try:
                if DEFAULT_RUN_NOW_DIR.exists():
                    consume_file_triggers(
                        channel_root=DEFAULT_RUN_NOW_DIR,
                        runner=runner_name,
                        max_items=20,
                        poll_seconds=0,
                        once=True,
                    )
            except Exception as exc:
                safe_print(f"[scheduler] File trigger consume error: {exc}")

            # --- 8) Consume schedule change triggers ---
            try:
                sched_processed = consume_schedule_triggers()
                if sched_processed > 0:
                    safe_print("[scheduler] Schedule changed — forcing immediate export")
                    pool.submit(_safe_run_script, "export_payload_from_db.py")
                    last_export = time.time()
            except Exception as exc:
                safe_print(f"[scheduler] Schedule trigger consume error: {exc}")

            # --- Save state ---
            _save_scheduler_state({
                "last_export": last_export,
                "last_archive": last_archive,
                "last_digest": last_digest,
                "last_fired": last_fired,
            })

            if once:
                safe_print("[scheduler] --once mode, exiting.")
                break

            # Sleep until next tick
            elapsed = time.time() - tick_start
            sleep_time = max(0, tick_sec - elapsed)
            _shutdown_event.wait(timeout=sleep_time)

    finally:
        pool.shutdown(wait=True, cancel_futures=False)
        safe_print("[scheduler] Shutdown complete.")

    return 0


def _safe_execute(cfg: PipelineCfg, requested_by: str, trigger_source: str) -> None:
    """Wrapper for execute_pipeline that catches all exceptions."""
    try:
        execute_pipeline(cfg, requested_by=requested_by, trigger_source=trigger_source)
    except Exception as exc:
        safe_print(f"[scheduler] Pipeline {cfg.pipeline_id} failed: {exc}")


def _safe_run_script(script_name: str, *extra_args: str) -> None:
    """Run a script from scripts/ directory safely."""
    script = ROOT / "scripts" / script_name
    if not script.exists():
        safe_print(f"[scheduler] Script not found: {script}")
        return
    try:
        subprocess.run(
            [sys.executable, str(script), *extra_args],
            check=False,
            timeout=600,
        )
    except Exception as exc:
        safe_print(f"[scheduler] Script {script_name} error: {exc}")


def _load_scheduler_state() -> dict[str, Any]:
    try:
        if SCHEDULER_STATE_FILE.exists():
            return json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_scheduler_state(state: dict[str, Any]) -> None:
    try:
        SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = SCHEDULER_STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        tmp.replace(SCHEDULER_STATE_FILE)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
# USER MANAGEMENT — integrates with MAIATRON.auth_users
# ══════════════════════════════════════════════════════════════════════

def cmd_user(args: argparse.Namespace) -> int:
    engine = get_engine()
    ensure_tables(engine)

    if args.user_cmd == "list":
        return _user_list(engine)
    if args.user_cmd == "grant":
        return _user_grant(engine, args.username, args.pipeline_id, args.role)
    if args.user_cmd == "revoke":
        return _user_revoke(engine, args.username, args.pipeline_id)
    if args.user_cmd == "show":
        return _user_show(engine, args.pipeline_id)

    safe_print("Comando user invalido. Usa: list | grant | revoke | show")
    return 2


def _user_list(engine) -> int:
    """List active users from MAIATRON.auth_users."""
    sql = text("""
        SELECT id, username, display_name, role, is_active, last_login_at
        FROM MAIATRON.auth_users
        WHERE is_active = 1
        ORDER BY username
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
        if not rows:
            safe_print("Sem utilizadores ativos em MAIATRON.auth_users.")
            return 0
        for r in rows:
            safe_print(
                f"  {r['username']:<20} | {r.get('display_name') or '-':<25} | "
                f"role={r.get('role') or '-':<10} | last_login={r.get('last_login_at') or 'never'}"
            )
        safe_print(f"\nTotal: {len(rows)} utilizadores ativos.")
        return 0
    except Exception as exc:
        safe_print(f"Erro ao ler MAIATRON.auth_users: {exc}")
        safe_print("Verifica se a tabela MAIATRON.auth_users existe e o user de DB tem permissao SELECT.")
        return 1


def _user_grant(engine, username: str, pipeline_id: str, role: str) -> int:
    """Grant permission for a user to a pipeline."""
    # Validate user exists
    check_sql = text("SELECT id FROM MAIATRON.auth_users WHERE username = :u AND is_active = 1")
    try:
        with engine.connect() as conn:
            user_row = conn.execute(check_sql, {"u": username}).mappings().first()
    except Exception as exc:
        safe_print(f"Erro ao verificar utilizador: {exc}")
        return 1

    if not user_row:
        safe_print(f"Utilizador '{username}' nao encontrado ou inativo em MAIATRON.auth_users.")
        return 1

    # Validate pipeline exists
    cfg = find_pipeline(pipeline_id)
    if not cfg:
        safe_print(f"Pipeline '{pipeline_id}' nao encontrado.")
        return 1

    sql = text("""
        INSERT INTO overseer_pipeline_permissions (username, pipeline_id, role, granted_at, granted_by)
        VALUES (:username, :pipeline_id, :role, UTC_TIMESTAMP(), :granted_by)
        ON DUPLICATE KEY UPDATE role = :role, granted_at = UTC_TIMESTAMP(), granted_by = :granted_by
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "username": username,
            "pipeline_id": pipeline_id,
            "role": role,
            "granted_by": "cli",
        })
    safe_print(f"Permissao concedida: {username} -> {pipeline_id} (role={role})")
    return 0


def _user_revoke(engine, username: str, pipeline_id: str) -> int:
    """Revoke permission for a user from a pipeline."""
    sql = text("""
        DELETE FROM overseer_pipeline_permissions
        WHERE username = :username AND pipeline_id = :pipeline_id
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {"username": username, "pipeline_id": pipeline_id})
        if result.rowcount == 0:
            safe_print(f"Sem permissao para remover: {username} -> {pipeline_id}")
            return 1
    safe_print(f"Permissao removida: {username} -> {pipeline_id}")
    return 0


def _user_show(engine, pipeline_id: str) -> int:
    """Show users with permissions for a pipeline."""
    sql = text("""
        SELECT p.username, p.role, p.granted_at, p.granted_by,
               u.display_name, u.is_active
        FROM overseer_pipeline_permissions p
        LEFT JOIN MAIATRON.auth_users u ON u.username = p.username
        WHERE p.pipeline_id = :pipeline_id
        ORDER BY p.role, p.username
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, {"pipeline_id": pipeline_id}).mappings().all()
    except Exception as exc:
        safe_print(f"Erro ao ler permissoes: {exc}")
        return 1

    if not rows:
        # Check if pipeline owner should be auto-seeded
        cfg = find_pipeline(pipeline_id)
        if cfg:
            safe_print(f"Sem permissoes explicitas para '{pipeline_id}'. Owner do YAML: {cfg.owner}")
        else:
            safe_print(f"Pipeline '{pipeline_id}' nao encontrado.")
        return 0

    safe_print(f"Permissoes para '{pipeline_id}':")
    for r in rows:
        active = "ativo" if r.get("is_active") else "inativo"
        safe_print(
            f"  {r['username']:<20} | role={r['role']:<10} | "
            f"{r.get('display_name') or '-':<25} | {active} | granted={r.get('granted_at') or '-'}"
        )
    return 0


def check_user_permission(engine, username: str, pipeline_id: str) -> bool:
    """Check if a user has executor or owner permission for a pipeline.

    Returns True if:
    - User has an explicit grant with role 'owner' or 'executor'
    - Or if no permissions exist for the pipeline (open access)
    """
    count_sql = text("""
        SELECT COUNT(*) AS c
        FROM overseer_pipeline_permissions
        WHERE pipeline_id = :pipeline_id
    """)
    check_sql = text("""
        SELECT role
        FROM overseer_pipeline_permissions
        WHERE pipeline_id = :pipeline_id
          AND username = :username
          AND role IN ('owner', 'executor')
    """)
    with engine.connect() as conn:
        total = conn.execute(count_sql, {"pipeline_id": pipeline_id}).scalar() or 0
        if total == 0:
            return True  # No permissions configured = open access
        row = conn.execute(check_sql, {"pipeline_id": pipeline_id, "username": username}).first()
        return row is not None


if __name__ == "__main__":
    raise SystemExit(main())













