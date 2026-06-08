"""
Runner por manifest — observabilidade por script sem alterar o código dos pipelines.

Cada manifest descreve um pipeline como uma sequência de passos (`steps`), em que
cada passo é um comando externo (tipicamente um script). O runner executa os
comandos por ordem, abrindo um módulo no Overseer por passo, registando stdout e
stderr como logs e marcando o estado de cada módulo. A primeira falha interrompe
a execução e a run termina com estado ``failed``.

Formato mínimo do manifest::

    pipeline_id: forms_to_lake
    pipeline_name: Forms to Lake
    owner: data
    steps:
      - module_id: extract
        command: ["python3", "/caminho/extract.py"]
        cwd: /caminho/opcional
      - module_id: load
        command: ["python3", "/caminho/load.py"]

O código dos pipelines não é alterado: o manifest vive fora dos repos
(por exemplo em ``~/overseer-runners/<pipeline_id>/manifest.yaml``).
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from overseer_sdk.client import OverseerClient

MAX_LOG_CHARS = 60000
MAX_ERROR_CHARS = 4000


@dataclass
class ManifestStep:
    module_id: str
    command: list[str]
    cwd: str | None = None
    critical: bool = True


@dataclass
class PipelineManifest:
    pipeline_id: str
    steps: list[ManifestStep]
    pipeline_name: str | None = None
    owner: str = "data"
    criticality: str = "medium"
    schedule: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.pipeline_name or self.pipeline_id


def load_manifest(path: str | Path) -> PipelineManifest:
    """Lê e valida um manifest YAML, devolvendo um ``PipelineManifest``."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest não encontrado: {manifest_path}")

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Manifest inválido: o conteúdo deve ser um mapeamento YAML.")

    pipeline_id = str(raw.get("pipeline_id") or "").strip()
    if not pipeline_id:
        raise ValueError("Manifest inválido: 'pipeline_id' é obrigatório.")

    raw_steps = raw.get("steps") or []
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("Manifest inválido: 'steps' deve conter pelo menos um passo.")

    steps: list[ManifestStep] = []
    seen: set[str] = set()
    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise ValueError(f"Manifest inválido: passo {index} deve ser um mapeamento.")
        module_id = str(raw_step.get("module_id") or "").strip()
        if not module_id:
            raise ValueError(f"Manifest inválido: passo {index} sem 'module_id'.")
        if module_id in seen:
            raise ValueError(f"Manifest inválido: 'module_id' duplicado: {module_id}.")
        seen.add(module_id)

        command = raw_step.get("command")
        if isinstance(command, str):
            command = command.split()
        if not isinstance(command, list) or not command:
            raise ValueError(f"Manifest inválido: passo '{module_id}' sem 'command'.")

        steps.append(
            ManifestStep(
                module_id=module_id,
                command=[str(part) for part in command],
                cwd=str(raw_step["cwd"]) if raw_step.get("cwd") else None,
                critical=bool(raw_step.get("critical", True)),
            )
        )

    return PipelineManifest(
        pipeline_id=pipeline_id,
        steps=steps,
        pipeline_name=str(raw["pipeline_name"]) if raw.get("pipeline_name") else None,
        owner=str(raw.get("owner") or "data"),
        criticality=str(raw.get("criticality") or "medium"),
        schedule=str(raw.get("schedule") or "manual"),
        metadata=raw.get("metadata") or {},
    )


def _catalog_nodes_edges(manifest: PipelineManifest) -> tuple[list[dict], list[dict]]:
    """Deriva nodes e edges de um DAG linear a partir da ordem dos passos."""
    nodes = [{"module_id": step.module_id, "label": step.module_id} for step in manifest.steps]
    edges = [
        {
            "from_module_id": manifest.steps[i].module_id,
            "to_module_id": manifest.steps[i + 1].module_id,
        }
        for i in range(len(manifest.steps) - 1)
    ]
    return nodes, edges


def register_catalog(manifest: PipelineManifest, client: OverseerClient) -> dict[str, Any]:
    """Regista (ou atualiza) o catálogo DAG do pipeline a partir do manifest."""
    nodes, edges = _catalog_nodes_edges(manifest)
    return client.register_pipeline(
        pipeline_id=manifest.pipeline_id,
        name=manifest.name,
        owner=manifest.owner,
        criticality=manifest.criticality,
        schedule=manifest.schedule,
        metadata=manifest.metadata,
        nodes=nodes,
        edges=edges,
    )


def run_manifest(
    manifest: PipelineManifest,
    *,
    client: OverseerClient | None = None,
    requested_by: str = "manifest",
) -> int:
    """
    Executa os passos do manifest, registando run, módulos e logs no Overseer.

    Devolve o código de saída do primeiro passo que falhar, ou 0 se todos os
    passos críticos terminarem com sucesso.
    """
    client = client or OverseerClient()
    started = time.monotonic()
    run_id = client.start_run(
        manifest.pipeline_id,
        pipeline_name=manifest.name,
        trigger_type="cron",
        requested_by=requested_by,
        metadata={"runner": "manifest", "steps": [step.module_id for step in manifest.steps]},
    )

    overall_exit = 0
    failed = False
    for step in manifest.steps:
        step_started = time.monotonic()
        proc = subprocess.run(
            step.command,
            cwd=step.cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        duration = round(time.monotonic() - step_started, 3)

        if proc.stdout:
            client.log(
                proc.stdout[-MAX_LOG_CHARS:],
                run_id=run_id,
                pipeline_id=manifest.pipeline_id,
                module_id=step.module_id,
                level="info",
            )
        if proc.stderr:
            client.log(
                proc.stderr[-MAX_LOG_CHARS:],
                run_id=run_id,
                pipeline_id=manifest.pipeline_id,
                module_id=step.module_id,
                level="error" if proc.returncode else "warning",
            )

        step_ok = proc.returncode == 0
        client.module(
            run_id=run_id,
            pipeline_id=manifest.pipeline_id,
            module_id=step.module_id,
            status="ok" if step_ok else "failed",
            duration_sec=duration,
            error_message=None if step_ok else proc.stderr[-MAX_ERROR_CHARS:],
            metadata={"command": step.command, "exit_code": proc.returncode},
        )

        if not step_ok and step.critical:
            overall_exit = proc.returncode
            failed = True
            break

    client.finish_run(
        run_id,
        status="failed" if failed else "ok",
        exit_code=overall_exit,
        duration_sec=round(time.monotonic() - started, 3),
    )
    return int(overall_exit)
