from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from src.overseer_core import store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/orchestrate", tags=["orchestrate"], dependencies=[Depends(require_service_token)])


class TriggerBody(BaseModel):
    pipeline_id: str
    trigger_type: str = "run_now"
    requested_by: str = "api"
    runner_host: str = "any"
    payload: dict[str, Any] = Field(default_factory=dict)


class ClaimBody(BaseModel):
    claimed_by: str | None = None


class CompleteBody(BaseModel):
    status: str = "done"


class RunBody(BaseModel):
    requested_by: str = "api"
    background: bool = True


@router.post("/triggers")
def orchestrate_trigger(body: TriggerBody) -> dict[str, Any]:
    if not store.get_pipeline(body.pipeline_id):
        raise HTTPException(status_code=404, detail="Pipeline inexistente.")
    trigger = store.enqueue_trigger(body.model_dump())
    return {"ok": True, "trigger": trigger}


@router.post("/triggers/{trigger_id}/claim")
def orchestrate_claim_trigger(trigger_id: str, body: ClaimBody) -> dict[str, Any]:
    trigger = store.claim_trigger(trigger_id, claimed_by=body.claimed_by)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger inexistente.")
    return {"ok": True, "trigger": trigger}


@router.post("/triggers/{trigger_id}/complete")
def orchestrate_complete_trigger(trigger_id: str, body: CompleteBody) -> dict[str, Any]:
    trigger = store.complete_trigger(trigger_id, status=body.status)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger inexistente.")
    return {"ok": True, "trigger": trigger}


@router.post("/pipelines/{pipeline_id}/run")
def orchestrate_run_pipeline(
    pipeline_id: str,
    body: RunBody,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    if not store.get_pipeline(pipeline_id):
        raise HTTPException(status_code=404, detail="Pipeline inexistente.")

    if body.background:
        background_tasks.add_task(store.run_pipeline_subprocess, pipeline_id, body.requested_by)
        return {"ok": True, "status": "queued_background", "pipeline_id": pipeline_id}

    return {
        "ok": True,
        "run": store.run_pipeline_subprocess(pipeline_id, requested_by=body.requested_by),
    }
