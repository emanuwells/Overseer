from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.overseer_core.triggers import enqueue_run_now, enqueue_schedule_update, list_triggers

from ..auth import require_service_token

router = APIRouter(prefix="/v1/triggers", tags=["triggers"], dependencies=[Depends(require_service_token)])


class TriggerEnqueueBody(BaseModel):
    pipeline_id: str
    requested_by: str = "api"
    requested_by_sso: str | None = None
    runner_host: str = "any"
    notes: str = ""
    trigger_id: str | None = None


class ScheduleUpdateBody(BaseModel):
    pipeline_id: str
    new_schedule: str
    requested_by: str = "api"
    requested_by_sso: str | None = None
    new_owner: str = ""
    new_criticality: str = ""


@router.get("")
def triggers_list(limit: int = 500) -> dict[str, Any]:
    return {"ok": True, "items": list_triggers(limit=limit)}


@router.post("")
def triggers_enqueue(body: TriggerEnqueueBody) -> dict[str, Any]:
    try:
        trigger_id = enqueue_run_now(
            pipeline_id=body.pipeline_id.strip(),
            requested_by=body.requested_by,
            requested_by_sso=body.requested_by_sso,
            runner_host=body.runner_host,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "status": "ok",
        "trigger_id": trigger_id,
        "requested_by_actor": body.requested_by,
        "requested_by_sso": body.requested_by_sso or body.requested_by,
    }
