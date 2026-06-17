from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from overseer_core import runner_ssh, store

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
    return {"ok": True, "items": store.list_deployments()}


@router.get("/runner-hosts")
def read_runner_hosts() -> dict[str, Any]:
    return {
        "ok": True,
        "ssh_sync_enabled": runner_ssh.ssh_sync_enabled(),
        "hosts": runner_ssh.runner_hosts_status(),
    }


@router.get("/pipelines/{pipeline_id}/dag")
def read_pipeline_dag(
    pipeline_id: str,
    host_id: str | None = None,
    include_inventory: bool = False,
) -> dict[str, Any]:
    dag = store.get_pipeline_dag(
        pipeline_id,
        host_id or "",
        include_inventory=include_inventory,
    )
    return {"ok": dag["pipeline"] is not None, "dag": dag}


@router.get("/runs")
def read_runs(
    limit: int = Query(default=200, ge=1, le=1000),
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
    limit: int = Query(default=500, ge=1, le=2000),
) -> dict[str, Any]:
    return {"ok": True, "items": store.list_logs(run_id=run_id, pipeline_id=pipeline_id, limit=limit)}


@router.get("/heartbeats")
def read_heartbeats(limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, Any]:
    return {"ok": True, "items": store.list_heartbeats(limit=limit)}


@router.get("/triggers")
def read_triggers(limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, Any]:
    return {"ok": True, "items": store.list_triggers(limit=limit)}
