from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from scripts.export_payload_from_db import load_pipeline_catalog
from src.overseer_core.triggers import enqueue_schedule_update, load_catalog_entry

from ..auth import require_service_token

router = APIRouter(prefix="/v1/pipelines", tags=["pipelines"], dependencies=[Depends(require_service_token)])


class SchedulePatchBody(BaseModel):
    new_schedule: str
    requested_by: str = "api"
    requested_by_sso: str | None = None
    new_owner: str = ""
    new_criticality: str = ""


class PipelineMetaPatchBody(BaseModel):
    owner: str | None = None
    criticality: str | None = None
    requested_by: str = "api"
    requested_by_sso: str | None = None


@router.get("")
def pipelines_catalog() -> dict[str, Any]:
    return {"ok": True, "items": load_pipeline_catalog()}


@router.patch("/{pipeline_id}/schedule")
def pipeline_schedule_update(pipeline_id: str, body: SchedulePatchBody) -> dict[str, Any]:
    try:
        trigger_id = enqueue_schedule_update(
            pipeline_id=pipeline_id,
            new_schedule=body.new_schedule,
            requested_by=body.requested_by,
            requested_by_sso=body.requested_by_sso,
            new_owner=body.new_owner,
            new_criticality=body.new_criticality,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "ok", "trigger_id": trigger_id}


@router.patch("/{pipeline_id}")
def pipeline_meta_update(pipeline_id: str, body: PipelineMetaPatchBody) -> dict[str, Any]:
    meta = load_catalog_entry(pipeline_id)
    if meta is None:
        raise HTTPException(status_code=422, detail="pipeline_id inexistente no catálogo.")

    schedule = str(meta.get("schedule") or "manual")
    owner = (body.owner or meta.get("owner") or "").strip()
    criticality = (body.criticality or meta.get("criticality") or "medium").strip()

    try:
        trigger_id = enqueue_schedule_update(
            pipeline_id=pipeline_id,
            new_schedule=schedule,
            requested_by=body.requested_by,
            requested_by_sso=body.requested_by_sso,
            new_owner=owner,
            new_criticality=criticality,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "ok", "trigger_id": trigger_id}
