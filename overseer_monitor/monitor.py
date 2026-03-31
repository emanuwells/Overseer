from __future__ import annotations

import json
import logging
import os
import platform
import socket
from contextlib import ContextDecorator
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from .db.writer import write_log_record, write_module_event_record
from .notifiers.slack import SlackNotifier

MAX_ERROR_LENGTH = int(os.getenv("PERF_ERROR_MAX_LEN", "65000"))
ROOT = Path(__file__).resolve().parents[1]


class OverseerMonitor:
    """Modulo universal de monitorizacao de pipelines (DB + Slack), tolerante a falhas."""

    def __init__(
        self,
        script_name: str,
        table_name: str = "logs",
        db_params: Optional[Dict[str, Any]] = None,
        frontend_base_url: Optional[str] = None,
        slack_config: Optional[Dict[str, Any] | str] = None,
        extra_tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.logger = logging.getLogger("overseer_monitor")
        self.script_name = script_name
        self.table_name = table_name
        self.module_events_table = os.getenv("P_MONITOR_MODULE_TABLE", "pipeline_module_events")
        self.db_params = db_params or {}
        self.frontend_base_url = frontend_base_url
        self.extra_tags = extra_tags or {}
        self.hostname = socket.gethostname()
        self.os_name = platform.system()
        self.os_release = platform.release()
        self.os_platform = platform.platform()

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.process: Optional[psutil.Process] = None
        self._start_cpu_times: Optional[psutil._common.pcputimes] = None  # type: ignore[attr-defined]
        self.peak_rss: int = 0
        self.log_id: Optional[int] = None

        self.slack = self._build_slack_notifier(slack_config)

    def _build_slack_notifier(self, slack_config: Optional[Dict[str, Any] | str]) -> Optional[SlackNotifier]:
        if slack_config is None:
            env_path = os.getenv("P_MONITOR_SLACK_CONFIG")
            if env_path:
                return SlackNotifier(config_path=env_path)
            return None
        if isinstance(slack_config, dict):
            return SlackNotifier(config=slack_config)
        return SlackNotifier(config_path=slack_config)

    @staticmethod
    def from_json_config(script_name: str, config_path: str | Path) -> "OverseerMonitor":
        payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return OverseerMonitor(
            script_name=script_name,
            table_name=payload.get("table_name", "logs"),
            db_params=payload.get("database") or payload.get("db_params") or {},
            frontend_base_url=payload.get("frontend_base_url"),
            slack_config=payload.get("slack"),
            extra_tags=payload.get("extra_tags") or {},
        )

    @staticmethod
    def from_env(script_name: str) -> "OverseerMonitor":
        db_params = OverseerMonitor._db_params_from_env_or_file()
        frontend_base_url = os.getenv("P_MONITOR_FRONTEND_URL")
        table_name = os.getenv("P_MONITOR_TABLE", "logs")
        slack_config = os.getenv("P_MONITOR_SLACK_CONFIG") or OverseerMonitor._discover_slack_config_path()
        return OverseerMonitor(
            script_name=script_name,
            table_name=table_name,
            db_params=db_params,
            frontend_base_url=frontend_base_url,
            slack_config=slack_config,
        )

    @staticmethod
    def _discover_slack_config_path() -> Optional[str]:
        candidates = [
            ROOT / "secrets" / "slack.json",
            Path.cwd() / "secrets" / "slack.json",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        return None

    @staticmethod
    def _db_params_from_env_or_file() -> Dict[str, Any]:
        env_params = {
            "host": os.getenv("P_MONITOR_DB_HOST"),
            "port": int(os.getenv("P_MONITOR_DB_PORT", "3306")),
            "user": os.getenv("P_MONITOR_DB_USER"),
            "password": os.getenv("P_MONITOR_DB_PASSWORD"),
            "database": os.getenv("P_MONITOR_DB_NAME"),
            "charset": os.getenv("P_MONITOR_DB_CHARSET", "utf8mb4"),
        }
        if env_params["user"] and env_params["password"] and env_params["database"]:
            env_params["host"] = env_params["host"] or "localhost"
            return env_params

        candidates = [
            ROOT / "secrets" / "database.json",
            Path.cwd() / "secrets" / "database.json",
        ]
        for path in candidates:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            node = payload.get("database") or {}
            if node.get("user") and node.get("password") and node.get("database"):
                return {
                    "host": node.get("host", "localhost"),
                    "port": int(node.get("port", 3306)),
                    "user": node.get("user"),
                    "password": node.get("password"),
                    "database": node.get("database"),
                    "charset": node.get("charset", "utf8mb4"),
                }

        return {
            "host": "localhost",
            "port": 3306,
            "user": None,
            "password": None,
            "database": None,
            "charset": "utf8mb4",
        }

    def set_db_params(self, db_params: Dict[str, Any]) -> None:
        self.db_params = db_params or {}

    def start(self) -> None:
        if self.start_time is not None:
            return
        self.start_time = datetime.now()
        self.process = psutil.Process()
        self._start_cpu_times = self.process.cpu_times()
        self.peak_rss = self.process.memory_info().rss

    def finish(self, status: str = "success", error_message: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if self.start_time is None:
            return None

        self.end_time = datetime.now()
        self._refresh_peak_memory()

        duration = (self.end_time - self.start_time).total_seconds()
        cpu_usage = self._calculate_cpu_usage(duration)
        usage_mem_mb = round(self.peak_rss / (1024 * 1024), 2)

        status_lower = str(status).lower()
        if status_lower in {"ok", "success", "sucesso"}:
            normalized_status = "OK"
        elif status_lower in {"warning", "warn", "parcial"}:
            normalized_status = "WARNING"
        else:
            normalized_status = "NOK"

        context_map = context or {}
        record = {
            "scriptName": self.script_name,
            "LogDate": self.start_time,
            "startDate": self.start_time,
            "endDate": self.end_time,
            "execTime": round(duration, 3),
            "usageCPU": cpu_usage,
            "usageMemoria": usage_mem_mb,
            "dbconn_wt": None,
            "dbconn_pt": None,
            "loading_wt": None,
            "loading_pt": None,
            "email_wt": None,
            "email_pt": None,
            "status": normalized_status,
            "errorMessage": self._truncate_error(error_message),
            "logMessage": self._truncate_error(context_map.get("log_message") if isinstance(context_map, dict) else None),
            "regDate": datetime.now(),
            "modDate": datetime.now(),
            "hostname": self.hostname,
            "osName": self.os_name,
            "osRelease": self.os_release,
            "osPlatform": self.os_platform,
            "pipelineId": (context or {}).get("pipeline_id"),
            "runId": (context or {}).get("run_id"),
            "attemptId": (context or {}).get("attempt_id"),
            "triggerType": (context or {}).get("trigger_type"),
            "owner": (context or {}).get("owner"),
            "criticality": (context or {}).get("criticality"),
        }

        self.log_id = self._persist_record(record)
        record["id"] = self.log_id
        record["frontend_url"] = self.get_frontend_url(self.log_id)
        record["extra_tags"] = self.extra_tags

        self._notify_slack(record=record, status=normalized_status, context=context)
        return record

    def step(
        self,
        module_id: str,
        *,
        parent_module_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "_MonitorStep":
        return _MonitorStep(
            monitor=self,
            module_id=module_id,
            parent_module_id=parent_module_id,
            context=context or {},
        )

    def track_step(
        self,
        module_id: str,
        *,
        parent_module_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        def decorator(func):
            def wrapper(*args, **kwargs):
                with self.step(module_id, parent_module_id=parent_module_id, context=context):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_frontend_url(self, log_id: Optional[int]) -> Optional[str]:
        if not self.frontend_base_url:
            return None
        base = self.frontend_base_url.rstrip("/")
        if log_id:
            return f"{base}?runId={log_id}"
        return base

    def _refresh_peak_memory(self) -> None:
        if not self.process:
            return
        try:
            self.peak_rss = max(self.peak_rss, self.process.memory_info().rss)
        except Exception:
            pass

    def _calculate_cpu_usage(self, duration: float) -> float:
        if duration <= 0 or not self.process or not self._start_cpu_times:
            return 0.0
        try:
            end_times = self.process.cpu_times()
            cpu_time = max(
                0.0,
                (end_times.user - self._start_cpu_times.user)
                + (end_times.system - self._start_cpu_times.system),
            )
            return round((cpu_time / duration) * 100, 2)
        except Exception:
            return 0.0

    def _truncate_error(self, error_message: Optional[str]) -> Optional[str]:
        if error_message is None:
            return None
        clean = str(error_message).strip()
        if not clean:
            return None
        if len(clean) > MAX_ERROR_LENGTH:
            return clean[: MAX_ERROR_LENGTH - 3] + "..."
        return clean

    def _persist_record(self, record: Dict[str, Any]) -> Optional[int]:
        if not self.db_params:
            self.logger.warning("Sem credenciais de DB para gravar logs.")
            return None
        try:
            return write_log_record(self.table_name, self.db_params, record)
        except Exception as exc:
            self.logger.warning("Falha ao gravar logs em DB: %s", exc)
            return None

    def _persist_module_event(self, record: Dict[str, Any]) -> Optional[int]:
        if not self.db_params:
            self.logger.warning("Sem credenciais de DB para gravar eventos de modulo.")
            return None
        try:
            return write_module_event_record(self.module_events_table, self.db_params, record)
        except Exception as exc:
            self.logger.warning("Falha ao gravar eventos de modulo em DB: %s", exc)
            return None

    def _notify_slack(self, record: Dict[str, Any], status: str, context: Optional[Dict[str, Any]]) -> None:
        if not self.slack:
            return
        if status == "OK" and not bool(getattr(self.slack, "notify_on_ok", False)):
            return
        if status == "WARNING" and not bool(getattr(self.slack, "notify_on_warning", True)):
            return
        try:
            self.slack.notify_run(
                status=status,
                run_id=record.get("id"),
                run_url=record.get("frontend_url"),
                script_name=self.script_name,
                duration_seconds=record.get("execTime"),
                error=record.get("errorMessage"),
                context={**(context or {}), **(self.extra_tags or {})},
            )
        except Exception as exc:
            self.logger.warning("Falha ao notificar Slack: %s", exc)


class _MonitorStep(ContextDecorator):
    def __init__(
        self,
        *,
        monitor: OverseerMonitor,
        module_id: str,
        parent_module_id: Optional[str],
        context: Dict[str, Any],
    ) -> None:
        self.monitor = monitor
        self.module_id = module_id
        self.parent_module_id = parent_module_id
        self.context = context
        self.started_at: Optional[datetime] = None

    def __enter__(self):
        self.started_at = datetime.now()
        return self

    def __exit__(self, exc_type, exc, tb):
        ended_at = datetime.now()
        started_at = self.started_at or ended_at
        duration = max(0.0, (ended_at - started_at).total_seconds())
        ok = exc is None
        error_message = None if ok else self.monitor._truncate_error(str(exc))
        payload = {
            "pipelineId": self.context.get("pipeline_id") or self.monitor.script_name,
            "runId": self.context.get("run_id"),
            "moduleId": self.module_id,
            "parentModuleId": self.parent_module_id,
            "status": "OK" if ok else "NOK",
            "startedAt": started_at,
            "endedAt": ended_at,
            "durationSec": round(duration, 3),
            "errorMessage": error_message,
            "logMessage": self.monitor._truncate_error(self.context.get("log_message")),
            "owner": self.context.get("owner"),
            "criticality": self.context.get("criticality"),
            "hostname": self.monitor.hostname,
            "triggerType": self.context.get("trigger_type"),
            "contextJson": json.dumps(self.context, ensure_ascii=False),
            "regDate": datetime.now(),
        }
        self.monitor._persist_module_event(payload)
        return False






