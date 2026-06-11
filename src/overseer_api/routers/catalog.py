from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from overseer_core import runner_catalog, runner_ssh, store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/catalog", tags=["catalog"], dependencies=[Depends(require_service_token)])

_CRON_RE = re.compile(r"^(\S+\s+){4}\S+$")


class CatalogNode(BaseModel):
    module_id: str
    label: str | None = None
    type: str = "task"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogEdge(BaseModel):
    from_module_id: str
    to_module_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineCatalogBody(BaseModel):
    pipeline_id: str
    host_id: str | None = None
    name: str | None = None
    owner: str = "unknown"
    criticality: str = "medium"
    schedule: str = "manual"
    runner_host: str = "any"
    metadata: dict[str, Any] = Field(default_factory=dict)
    nodes: list[CatalogNode] = Field(default_factory=list)
    edges: list[CatalogEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dag(self) -> "PipelineCatalogBody":
        node_ids = [node.module_id.strip() for node in self.nodes]
        if not self.pipeline_id.strip():
            raise ValueError("pipeline_id é obrigatório.")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("module_id duplicado no catálogo.")
        known = set(node_ids)
        for edge in self.edges:
            if edge.from_module_id not in known or edge.to_module_id not in known:
                raise ValueError("Todas as edges devem referenciar nodes existentes.")
            if edge.from_module_id == edge.to_module_id:
                raise ValueError("Uma edge não pode ligar um node a si próprio.")
        return self


class ReconcileBody(BaseModel):
    sync_remote: bool = False


class PipelinePatchBody(BaseModel):
    host_id: str
    name: str | None = None
    owner: str | None = None
    criticality: str | None = None
    schedule: str | None = None
    suspended: bool | None = None
    sync_remote: bool = True

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, value: str | None) -> str | None:
        if value is None:
            return value
        raw = value.strip()
        if not raw:
            raise ValueError("schedule não pode ser vazio.")
        if raw.lower() == "manual":
            return "manual"
        if raw.lower() == "paused":
            return "paused"
        if not _CRON_RE.match(raw):
            raise ValueError("schedule deve ser 'manual', 'paused' ou cron de 5 campos.")
        return raw

    @model_validator(mode="after")
    def validate_has_field(self) -> "PipelinePatchBody":
        if not any([self.name, self.owner, self.criticality, self.schedule, self.suspended is not None]):
            raise ValueError(
                "Indique pelo menos um campo a actualizar (name, owner, criticality, schedule, suspended)."
            )
        return self


@router.post("/pipelines")
def register_pipeline(body: PipelineCatalogBody) -> dict[str, Any]:
    try:
        dag = store.register_pipeline_catalog(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "dag": dag}


@router.post("/reconcile")
def reconcile_catalog(body: ReconcileBody | None = None) -> dict[str, Any]:
    options = body or ReconcileBody()
    try:
        result = store.reconcile_catalog_from_yaml()
        ssh_results: list[dict[str, Any]] = []
        if options.sync_remote:
            for host_id in result.get("hosts") or []:
                ssh_results.append(runner_ssh.sync_remote_runner(host_id, schedule_changed=False))
        return {"ok": True, "reconcile": result, "ssh": ssh_results or None}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/pipelines/{pipeline_id}")
def patch_pipeline(pipeline_id: str, body: PipelinePatchBody) -> dict[str, Any]:
    host_id = body.host_id.strip()
    fields = {
        "name": body.name,
        "owner": body.owner,
        "criticality": body.criticality,
        "schedule": body.schedule,
        "suspended": body.suspended,
    }
    schedule_changed = body.schedule is not None

    try:
        catalog_host = runner_ssh.resolve_catalog_host_id(host_id)
        dag = store.patch_pipeline_catalog(pipeline_id, host_id, fields)
        yaml_result: dict[str, Any] | None = None
        try:
            yaml_result = runner_catalog.patch_runner_catalog_yaml(catalog_host, pipeline_id, fields)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(str(exc)) from exc

        ssh_result: dict[str, Any] | None = None
        if body.sync_remote:
            ssh_result = runner_ssh.sync_remote_runner(catalog_host, schedule_changed=schedule_changed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sync_payload: dict[str, Any] = {
        "db": "ok",
        "yaml": yaml_result,
        "ssh": ssh_result,
    }
    if ssh_result:
        sync_payload["ssh_enabled"] = bool(ssh_result.get("enabled"))
        sync_payload["ssh_ok"] = bool(ssh_result.get("ok"))
        if ssh_result.get("stdout_tail"):
            sync_payload["ssh_stdout_tail"] = ssh_result["stdout_tail"]
        if ssh_result.get("schedule_note"):
            sync_payload["schedule_note"] = ssh_result["schedule_note"]

    return {"ok": True, "dag": dag, "sync": sync_payload}
