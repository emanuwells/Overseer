from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.overseer_core import store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/events", tags=["events"], dependencies=[Depends(require_service_token)])


class RunStartBody(BaseModel):
    pipeline_id: str
    pipeline_name: str | None = None
    run_id: str | None = None
    trigger_type: str = "manual"
    requested_by: str | None = None
    runner_host: str | None = None
    hostname: str | None = None
    started_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunFinishBody(BaseModel):
    status: str = "ok"
    ended_at: str | None = None
    duration_sec: float | None = None
    exit_code: int | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleBody(BaseModel):
    run_id: str
    pipeline_id: str
    module_id: str
    parent_module_id: str | None = None
    status: str = "running"
    started_at: str | None = None
    ended_at: str | None = None
    duration_sec: float | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogBody(BaseModel):
    run_id: str | None = None
    pipeline_id: str | None = None
    module_id: str | None = None
    level: str = "info"
    event_type: str = "log"
    message: str
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HeartbeatBody(BaseModel):
    source_id: str | None = None
    source_type: str = "runner"
    pipeline_id: str | None = None
    run_id: str | None = None
    hostname: str | None = None
    status: str = "ok"
    seen_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/runs/start")
def event_run_start(body: RunStartBody) -> dict[str, Any]:
    return {"ok": True, "run": store.start_run(body.model_dump())}


@router.post("/runs/{run_id}/finish")
def event_run_finish(run_id: str, body: RunFinishBody) -> dict[str, Any]:
    return {"ok": True, "run": store.finish_run(run_id, body.model_dump())}


@router.post("/modules")
def event_module(body: ModuleBody) -> dict[str, Any]:
    return {"ok": True, "module": store.record_module(body.model_dump())}


@router.post("/logs")
def event_log(body: LogBody) -> dict[str, Any]:
    return {"ok": True, "log": store.record_log(body.model_dump())}


@router.post("/heartbeat")
def event_heartbeat(body: HeartbeatBody) -> dict[str, Any]:
    return {"ok": True, "heartbeat": store.record_heartbeat(body.model_dump())}
