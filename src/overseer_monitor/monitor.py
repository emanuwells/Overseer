from __future__ import annotations

import logging
import os
import platform
import socket
import time
from contextlib import ContextDecorator
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("overseer.monitor")

from overseer_core.run_telemetry import TelemetryTracker, enrich_finish_metadata
from overseer_sdk.client import OverseerClient


class OverseerMonitor:
    """Adaptador compatível que regista telemetria na API Overseer."""

    def __init__(
        self,
        script_name: str,
        table_name: str = "overseer_runs",
        db_params: Optional[Dict[str, Any]] = None,
        frontend_base_url: Optional[str] = None,
        slack_config: Optional[Dict[str, Any] | str] = None,
        extra_tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.script_name = script_name
        self.table_name = table_name
        self.db_params = db_params or {}
        self.frontend_base_url = frontend_base_url
        self.slack_config = slack_config
        self.extra_tags = extra_tags or {}
        self.hostname = socket.gethostname()
        self.os_name = platform.system()
        self.os_release = platform.release()
        self.os_platform = platform.platform()
        self.client = OverseerClient()
        self.run_id = os.getenv("OVERSEER_RUN_ID") or None
        self.pipeline_id = os.getenv("OVERSEER_PIPELINE_ID") or script_name
        self.start_time: datetime | None = None
        self.telemetry: TelemetryTracker | None = None

    @staticmethod
    def from_env(script_name: str) -> "OverseerMonitor":
        return OverseerMonitor(script_name=script_name)

    @staticmethod
    def from_json_config(script_name: str, config_path: str) -> "OverseerMonitor":
        return OverseerMonitor(script_name=script_name)

    def set_db_params(self, db_params: Dict[str, Any]) -> None:
        self.db_params = db_params or {}

    def start(self) -> None:
        if self.start_time is not None:
            return
        self.start_time = datetime.now()
        self.telemetry = TelemetryTracker()
        if not self.run_id:
            try:
                self.run_id = self.client.start_run(
                    self.pipeline_id,
                    pipeline_name=self.script_name,
                    trigger_type=os.getenv("P_TRIGGER_TYPE", "standalone"),
                    metadata={"adapter": "overseer_monitor"},
                )
            except Exception:
                logger.warning(
                    "Falha ao iniciar run na API Overseer para pipeline %s",
                    self.pipeline_id,
                    exc_info=True,
                )
                self.run_id = None

    def finish(
        self,
        status: str = "success",
        error_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if self.start_time is None:
            return None

        context_map = context or {}
        pipeline_id = context_map.get("pipeline_id") or self.pipeline_id
        run_id = self.run_id or os.getenv("OVERSEER_RUN_ID")
        duration = max(0.0, (datetime.now() - self.start_time).total_seconds())
        metadata = enrich_finish_metadata(
            {
                **context_map,
                "script_name": self.script_name,
                "hostname": self.hostname,
                "os_name": self.os_name,
                "os_release": self.os_release,
                "os_platform": self.os_platform,
                "extra_tags": self.extra_tags,
            },
            tracker=self.telemetry,
        )

        payload = {
            "status": status,
            "duration_sec": round(duration, 3),
            "error_message": error_message,
            "metadata": metadata,
        }

        if not run_id:
            return None
        try:
            data = self.client.finish_run(run_id, **payload)
        except Exception:
            logger.warning(
                "Falha ao finalizar run %s na API Overseer",
                run_id,
                exc_info=True,
            )
            return None
        run = data.get("run") or {}
        return {"id": run.get("run_id"), "run_id": run.get("run_id"), "frontend_url": self.get_frontend_url(run.get("run_id"))}

    def step(
        self,
        module_id: str,
        *,
        parent_module_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "_MonitorStep":
        return _MonitorStep(self, module_id, parent_module_id, context or {})

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

    def get_frontend_url(self, log_id: Optional[Any]) -> Optional[str]:
        if not self.frontend_base_url:
            return None
        base = self.frontend_base_url.rstrip("/")
        return f"{base}?runId={log_id}" if log_id else base


class _MonitorStep(ContextDecorator):
    def __init__(
        self,
        monitor: OverseerMonitor,
        module_id: str,
        parent_module_id: str | None,
        context: dict[str, Any],
    ) -> None:
        self.monitor = monitor
        self.module_id = module_id
        self.parent_module_id = parent_module_id
        self.context = context
        self.started = 0.0

    def __enter__(self):
        self.started = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb):
        run_id = self.context.get("run_id") or self.monitor.run_id or os.getenv("OVERSEER_RUN_ID")
        pipeline_id = self.context.get("pipeline_id") or self.monitor.pipeline_id
        if not run_id:
            return False
        duration = round(max(0.0, time.monotonic() - self.started), 3)
        try:
            self.monitor.client.module(
                run_id=run_id,
                pipeline_id=pipeline_id,
                module_id=self.module_id,
                parent_module_id=self.parent_module_id,
                status="ok" if exc is None else "failed",
                duration_sec=duration,
                error_message=None if exc is None else str(exc),
                metadata=self.context,
            )
        except Exception:
            logger.warning(
                "Falha ao registar módulo %s (run=%s) na API Overseer",
                self.module_id,
                run_id,
                exc_info=True,
            )
        return False
