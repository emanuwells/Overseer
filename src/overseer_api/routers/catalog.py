from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from src.overseer_core import store

from ..auth import require_service_token

router = APIRouter(prefix="/v1/catalog", tags=["catalog"], dependencies=[Depends(require_service_token)])


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


@router.post("/pipelines")
def register_pipeline(body: PipelineCatalogBody) -> dict[str, Any]:
    try:
        dag = store.register_pipeline_catalog(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "dag": dag}
