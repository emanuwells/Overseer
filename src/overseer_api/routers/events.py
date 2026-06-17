from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from overseer_core import store

from ..auth import require_service_token

logger = logging.getLogger("overseer.api.events")

router = APIRouter(prefix="/v1/events", tags=["events"], dependencies=[Depends(require_service_token)])


class RunStartBody(BaseModel):
    pipeline_id: str
    host_id: str | None = None
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
    host_id: str | None = None
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
    host_id: str | None = None
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
    host_id: str | None = None
    run_id: str | None = None
    hostname: str | None = None
    status: str = "ok"
    seen_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/runs/start")
def event_run_start(body: RunStartBody) -> dict[str, Any]:
    try:
        return {"ok": True, "run": store.start_run(body.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erro ao iniciar run para pipeline %s", body.pipeline_id)
        raise HTTPException(status_code=500, detail=f"Falha ao registar run: {exc.__class__.__name__}") from exc


@router.post("/runs/{run_id}/finish")
def event_run_finish(run_id: str, body: RunFinishBody) -> dict[str, Any]:
    try:
        return {"ok": True, "run": store.finish_run(run_id, body.model_dump())}
    except Exception as exc:
        logger.exception("Erro ao finalizar run %s", run_id)
        raise HTTPException(status_code=500, detail=f"Falha ao finalizar run: {exc.__class__.__name__}") from exc


@router.post("/modules")
def event_module(body: ModuleBody) -> dict[str, Any]:
    try:
        return {"ok": True, "module": store.record_module(body.model_dump())}
    except Exception as exc:
        logger.exception("Erro ao registar módulo %s (run=%s)", body.module_id, body.run_id)
        raise HTTPException(status_code=500, detail=f"Falha ao registar módulo: {exc.__class__.__name__}") from exc


@router.post("/logs")
def event_log(body: LogBody) -> dict[str, Any]:
    try:
        return {"ok": True, "log": store.record_log(body.model_dump())}
    except Exception as exc:
        logger.exception("Erro ao registar log (run=%s)", body.run_id)
        raise HTTPException(status_code=500, detail=f"Falha ao registar log: {exc.__class__.__name__}") from exc


@router.post("/heartbeat")
def event_heartbeat(body: HeartbeatBody) -> dict[str, Any]:
    try:
        return {"ok": True, "heartbeat": store.record_heartbeat(body.model_dump())}
    except Exception as exc:
        logger.exception("Erro ao registar heartbeat (source=%s)", body.source_id)
        raise HTTPException(status_code=500, detail=f"Falha ao registar heartbeat: {exc.__class__.__name__}") from exc
