from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from overseer_core import runner_ssh, store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/orchestrate", tags=["orchestrate"], dependencies=[Depends(require_service_token)])


class TriggerBody(BaseModel):
    pipeline_id: str
    host_id: str | None = None
    trigger_type: str = "run_now"
    requested_by: str = "api"
    runner_host: str = "any"
    payload: dict[str, Any] = Field(default_factory=dict)


class ClaimBody(BaseModel):
    claimed_by: str | None = None


class CompleteBody(BaseModel):
    status: str = "done"


def _pipeline_suspended(catalog: dict[str, Any] | None) -> bool:
    if not catalog:
        return False
    meta = catalog.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    return bool(meta.get("suspended"))


@router.post("/triggers")
def orchestrate_trigger(body: TriggerBody) -> dict[str, Any]:
    host_id = str(body.host_id or "").strip()
    if not host_id:
        raise HTTPException(status_code=422, detail="host_id é obrigatório.")

    if not runner_ssh.ssh_sync_enabled():
        raise HTTPException(
            status_code=503,
            detail="Dispatch SSH desactivado (OVERSEER_SSH_SYNC_ENABLED).",
        )

    catalog = store.find_pipeline_catalog(body.pipeline_id, host_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Pipeline inexistente para este host.")

    if _pipeline_suspended(catalog):
        raise HTTPException(status_code=409, detail="Pipeline suspenso. Resume antes de executar.")

    trigger = store.enqueue_trigger(body.model_dump())
    trigger_id = str(trigger.get("trigger_id") or "")
    claimed = store.claim_trigger(trigger_id, claimed_by="overseer-api")
    if not claimed:
        raise HTTPException(status_code=500, detail="Falha ao reivindicar trigger.")

    requested_by = str(body.requested_by or "run_now").strip() or "run_now"
    dispatch = runner_ssh.execute_pipeline_run(
        host_id,
        body.pipeline_id,
        requested_by=requested_by,
    )

    final_status = "done" if dispatch.get("ok") else "failed"
    completed = store.complete_trigger(trigger_id, status=final_status)
    if not completed:
        raise HTTPException(status_code=500, detail="Falha ao concluir trigger.")

    if not dispatch.get("ok"):
        raise HTTPException(
            status_code=502,
            detail=dispatch.get("reason") or dispatch.get("stderr_tail") or "Dispatch remoto falhou.",
        )

    return {"ok": True, "trigger": completed, "dispatch": dispatch}


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
