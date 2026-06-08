from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from src.overseer_core import store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/read", tags=["read"], dependencies=[Depends(require_service_token)])


@router.get("/overview")
def read_overview() -> dict[str, Any]:
    return {"ok": True, "data": store.overview()}


@router.get("/database")
def read_database() -> dict[str, Any]:
    return {"ok": True, "database": store.database_status()}


@router.get("/pipelines")
def read_pipelines() -> dict[str, Any]:
    return {"ok": True, "items": store.list_pipelines()}


@router.get("/pipelines/{pipeline_id}/dag")
def read_pipeline_dag(pipeline_id: str) -> dict[str, Any]:
    dag = store.get_pipeline_dag(pipeline_id)
    return {"ok": dag["pipeline"] is not None, "dag": dag}


@router.get("/runs")
def read_runs(
    limit: int = 200,
    pipeline_id: str | None = None,
    host_id: str | None = None,
) -> dict[str, Any]:
    return {"ok": True, "items": store.list_runs(limit=limit, pipeline_id=pipeline_id, host_id=host_id)}


@router.get("/runs/{run_id}")
def read_run_detail(run_id: str) -> dict[str, Any]:
    run = store.get_run(run_id)
    return {
        "ok": run is not None,
        "run": run,
        "modules": store.list_modules(run_id=run_id),
        "logs": store.list_logs(run_id=run_id),
    }


@router.get("/modules")
def read_modules(run_id: str | None = None, pipeline_id: str | None = None) -> dict[str, Any]:
    return {"ok": True, "items": store.list_modules(run_id=run_id, pipeline_id=pipeline_id)}


@router.get("/logs")
def read_logs(
    run_id: str | None = None,
    pipeline_id: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    return {"ok": True, "items": store.list_logs(run_id=run_id, pipeline_id=pipeline_id, limit=limit)}


@router.get("/heartbeats")
def read_heartbeats(limit: int = 200) -> dict[str, Any]:
    return {"ok": True, "items": store.list_heartbeats(limit=limit)}


@router.get("/triggers")
def read_triggers(limit: int = 200) -> dict[str, Any]:
    return {"ok": True, "items": store.list_triggers(limit=limit)}
