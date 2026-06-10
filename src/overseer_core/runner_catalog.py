"""Actualização de metadata de pipelines em deploy/runners/<host>.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .repo_paths import repo_root

logger = logging.getLogger("overseer.runner_catalog")

PATCHABLE_YAML_KEYS = frozenset({"name", "owner", "schedule", "criticality"})


def runners_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "deploy" / "runners"


def catalog_path_for_host(host_id: str, root: Path | None = None) -> Path:
    path = runners_dir(root) / f"{host_id}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Catálogo não encontrado: {path}")
    return path


def patch_runner_catalog_yaml(
    host_id: str,
    pipeline_id: str,
    fields: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    path = catalog_path_for_host(host_id, root)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pipelines = data.get("pipelines")
    if not isinstance(pipelines, list):
        raise ValueError(f"Catálogo inválido (sem pipelines[]): {path}")

    updated_keys: list[str] = []
    found = False
    for entry in pipelines:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("id") or "") != pipeline_id:
            continue
        found = True
        for key, value in fields.items():
            if key in PATCHABLE_YAML_KEYS and value is not None:
                entry[key] = value
                updated_keys.append(key)
        break

    if not found:
        raise ValueError(f"Pipeline '{pipeline_id}' não encontrado em {path.name}")

    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    logger.info("Catálogo YAML actualizado: %s (%s)", path, ", ".join(updated_keys))
    return {"path": str(path), "pipeline_id": pipeline_id, "updated": updated_keys}
