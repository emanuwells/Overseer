"""Actualização de metadata de pipelines em deploy/runners/<host>.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .repo_paths import repo_root

logger = logging.getLogger("overseer.runner_catalog")

PATCHABLE_YAML_KEYS = frozenset({"name", "owner", "schedule", "criticality"})
HOSTS_FILE_NAME = "hosts.yaml"


def runners_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "deploy" / "runners"


def list_runner_catalog_files(root: Path | None = None) -> list[Path]:
    directory = runners_dir(root)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.yaml")
        if path.is_file()
        and path.name != HOSTS_FILE_NAME
        and not path.name.startswith("_")
    )


def load_all_runner_catalogs(root: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Devolve {catalog_host_stem: [pipeline entries]} a partir dos YAML de runners."""
    catalogs: dict[str, list[dict[str, Any]]] = {}
    for path in list_runner_catalog_files(root):
        host_stem = path.stem
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        pipelines = data.get("pipelines")
        if not isinstance(pipelines, list):
            continue
        entries: list[dict[str, Any]] = []
        for item in pipelines:
            if not isinstance(item, dict):
                continue
            pipeline_id = str(item.get("id") or "").strip()
            if not pipeline_id:
                continue
            entries.append(
                {
                    "pipeline_id": pipeline_id,
                    "catalog_host": host_stem,
                    "name": item.get("name"),
                    "owner": item.get("owner"),
                    "schedule": item.get("schedule"),
                    "criticality": item.get("criticality"),
                    "steps": item.get("steps") if isinstance(item.get("steps"), list) else [],
                }
            )
        if entries:
            catalogs[host_stem] = entries
    return catalogs


def catalog_entry_for(
    host_id: str,
    pipeline_id: str,
    *,
    root: Path | None = None,
) -> dict[str, Any] | None:
    logical_id = str(pipeline_id or "").strip()
    if not logical_id:
        return None
    host_raw = str(host_id or "").strip()
    host_lower = host_raw.lower()
    for catalog_host, entries in load_all_runner_catalogs(root).items():
        if catalog_host.lower() != host_lower and catalog_host.upper() != host_raw.upper():
            continue
        for entry in entries:
            if entry.get("pipeline_id") == logical_id:
                return dict(entry)
    return None


def catalog_path_for_host(host_id: str, root: Path | None = None) -> Path:
    from . import runner_ssh

    canonical = runner_ssh.resolve_catalog_host_id(host_id, root)
    path = runners_dir(root) / f"{canonical}.yaml"
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
    from . import runner_ssh

    canonical_host = runner_ssh.resolve_catalog_host_id(host_id, root)
    path = catalog_path_for_host(canonical_host, root)
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
    return {
        "path": str(path),
        "pipeline_id": pipeline_id,
        "host_id": canonical_host,
        "updated": updated_keys,
    }
