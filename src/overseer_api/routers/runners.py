from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.overseer_core.runners import list_runners, register_runner

from ..auth import require_service_token

router = APIRouter(prefix="/v1/runners", tags=["runners"], dependencies=[Depends(require_service_token)])


class HeartbeatBody(BaseModel):
    hostname: str | None = None
    agent_version: str | None = None
    os_name: str | None = None
    os_release: str | None = None


@router.get("")
def runners_list(limit: int = 200) -> dict[str, Any]:
    return {"ok": True, "items": list_runners(limit=limit)}


@router.post("/heartbeat")
def runners_heartbeat(body: HeartbeatBody) -> dict[str, Any]:
    row = register_runner(
        hostname=body.hostname,
        agent_version=body.agent_version or "1.0.0",
        os_name=body.os_name,
        os_release=body.os_release,
    )
    return {"ok": True, "runner": row}
