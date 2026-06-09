from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from src.overseer_core import monitoring_export

from ..auth import require_service_token

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])

_ops_public = APIRouter(prefix="/ops", tags=["monitoring"], dependencies=[])


@router.get("/full", dependencies=[Depends(require_service_token)])
def monitoring_full() -> dict[str, Any]:
    return monitoring_export.build_full_payload()


@router.get("/details", dependencies=[Depends(require_service_token)])
def monitoring_details() -> dict[str, Any]:
    from src.overseer_core import store

    runs = store.list_runs(limit=5000)
    pipelines = store.list_pipelines()
    return monitoring_export.build_details_map(runs, pipelines)


@_ops_public.get("/fast")
def monitoring_ops_fast() -> dict[str, Any]:
    return monitoring_export.build_ops_fast_payload()


@_ops_public.get("/heavy")
def monitoring_ops_heavy() -> dict[str, Any]:
    return monitoring_export.build_ops_heavy_payload()


router.include_router(_ops_public)
