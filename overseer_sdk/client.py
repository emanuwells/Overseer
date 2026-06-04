from __future__ import annotations

import os
import socket
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

import httpx


def _api_url(value: str | None = None) -> str:
    return (value or os.getenv("OVERSEER_API_URL") or "http://127.0.0.1:8090").rstrip("/")


def _api_token(value: str | None = None) -> str:
    return value if value is not None else os.getenv("OVERSEER_API_TOKEN", "")


@dataclass
class OverseerClient:
    api_url: str | None = None
    api_token: str | None = None
    timeout: float = 30.0
    hostname: str = field(default_factory=socket.gethostname)

    def __post_init__(self) -> None:
        self.api_url = _api_url(self.api_url)
        self.api_token = _api_token(self.api_token)

    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.api_url}{path}", json=payload, headers=self.headers())
            response.raise_for_status()
            return response.json()

    def start_run(
        self,
        pipeline_id: str,
        *,
        pipeline_name: str | None = None,
        trigger_type: str = "manual",
        requested_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        body = {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "trigger_type": trigger_type,
            "requested_by": requested_by,
            "hostname": self.hostname,
            "metadata": metadata or {},
        }
        data = self.post("/v1/events/runs/start", body)
        return str(data["run"]["run_id"])

    def finish_run(
        self,
        run_id: str,
        *,
        status: str = "ok",
        exit_code: int | None = None,
        error_message: str | None = None,
        duration_sec: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.post(
            f"/v1/events/runs/{run_id}/finish",
            {
                "status": status,
                "exit_code": exit_code,
                "error_message": error_message,
                "duration_sec": duration_sec,
                "metadata": metadata or {},
            },
        )

    def module(
        self,
        *,
        run_id: str,
        pipeline_id: str,
        module_id: str,
        parent_module_id: str | None = None,
        status: str = "ok",
        duration_sec: float | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.post(
            "/v1/events/modules",
            {
                "run_id": run_id,
                "pipeline_id": pipeline_id,
                "module_id": module_id,
                "parent_module_id": parent_module_id,
                "status": status,
                "duration_sec": duration_sec,
                "error_message": error_message,
                "metadata": metadata or {},
            },
        )

    def log(
        self,
        message: str,
        *,
        run_id: str | None = None,
        pipeline_id: str | None = None,
        module_id: str | None = None,
        level: str = "info",
        event_type: str = "log",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.post(
            "/v1/events/logs",
            {
                "run_id": run_id,
                "pipeline_id": pipeline_id,
                "module_id": module_id,
                "level": level,
                "event_type": event_type,
                "message": message,
                "metadata": metadata or {},
            },
        )

    def heartbeat(
        self,
        *,
        source_id: str | None = None,
        source_type: str = "runner",
        pipeline_id: str | None = None,
        run_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.post(
            "/v1/events/heartbeat",
            {
                "source_id": source_id or self.hostname,
                "source_type": source_type,
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "hostname": self.hostname,
                "status": status,
                "payload": payload or {},
            },
        )

    @contextmanager
    def run(self, pipeline_id: str, **kwargs: Any) -> Iterator[str]:
        started = time.monotonic()
        run_id = self.start_run(pipeline_id, **kwargs)
        try:
            yield run_id
        except Exception as exc:
            self.finish_run(
                run_id,
                status="failed",
                error_message=str(exc),
                duration_sec=round(time.monotonic() - started, 3),
            )
            raise
        else:
            self.finish_run(run_id, status="ok", duration_sec=round(time.monotonic() - started, 3))

    @contextmanager
    def step(self, *, run_id: str, pipeline_id: str, module_id: str, parent_module_id: str | None = None) -> Iterator[None]:
        started = time.monotonic()
        try:
            yield
        except Exception as exc:
            self.module(
                run_id=run_id,
                pipeline_id=pipeline_id,
                module_id=module_id,
                parent_module_id=parent_module_id,
                status="failed",
                duration_sec=round(time.monotonic() - started, 3),
                error_message=str(exc),
            )
            raise
        else:
            self.module(
                run_id=run_id,
                pipeline_id=pipeline_id,
                module_id=module_id,
                parent_module_id=parent_module_id,
                status="ok",
                duration_sec=round(time.monotonic() - started, 3),
            )


def run_command(
    command: list[str],
    *,
    pipeline_id: str,
    pipeline_name: str | None = None,
    requested_by: str | None = None,
    api_url: str | None = None,
    api_token: str | None = None,
    cwd: str | None = None,
) -> int:
    client = OverseerClient(api_url=api_url, api_token=api_token)
    started = time.monotonic()
    run_id = client.start_run(
        pipeline_id,
        pipeline_name=pipeline_name,
        trigger_type="cli",
        requested_by=requested_by,
        metadata={"command": command},
    )
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if proc.stdout:
        client.log(proc.stdout[-60000:], run_id=run_id, pipeline_id=pipeline_id, level="info")
    if proc.stderr:
        client.log(proc.stderr[-60000:], run_id=run_id, pipeline_id=pipeline_id, level="error")
    client.finish_run(
        run_id,
        status="ok" if proc.returncode == 0 else "failed",
        exit_code=proc.returncode,
        error_message=proc.stderr[-4000:] if proc.returncode else None,
        duration_sec=round(time.monotonic() - started, 3),
    )
    return int(proc.returncode)
