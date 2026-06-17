"""Actualização de metadata de pipelines em deploy/runners/<host>.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .helpers import safe_metadata
from .repo_paths import repo_root

logger = logging.getLogger("overseer.runner_catalog")

PATCHABLE_YAML_KEYS = frozenset({"name", "owner", "schedule", "criticality"})
YAML_META_KEYS = frozenset({"prev_schedule"})
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
                    "prev_schedule": item.get("prev_schedule"),
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


def resolve_schedule_patch(entry: dict[str, Any], new_schedule: str) -> dict[str, Any]:
    """Calcula schedule/prev_schedule para pause, resume ou alteração de cron."""
    current = str(entry.get("schedule") or "manual").strip()
    new = str(new_schedule or "").strip()
    if not new:
        raise ValueError("schedule não pode ser vazio.")
    patch: dict[str, Any] = {"schedule": new}
    if new.lower() == "paused":
        if current.lower() not in {"manual", "paused", ""}:
            patch["prev_schedule"] = current
        elif entry.get("prev_schedule"):
            patch["prev_schedule"] = entry.get("prev_schedule")
    elif new.lower() != "manual":
        patch["prev_schedule"] = None
    return patch


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
        effective = dict(fields)
        if "schedule" in effective and effective["schedule"] is not None:
            effective.update(resolve_schedule_patch(entry, str(effective["schedule"])))
        for key, value in effective.items():
            if key in PATCHABLE_YAML_KEYS:
                if value is not None:
                    entry[key] = value
                    updated_keys.append(key)
            elif key in YAML_META_KEYS:
                if value is None:
                    entry.pop(key, None)
                    updated_keys.append(f"-{key}")
                else:
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


def dag_to_yaml_steps(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converte nodes/edges da DB em ``steps[]`` para o YAML do runner."""
    from collections import defaultdict

    if not nodes:
        return []
    node_ids = {str(node["module_id"]) for node in nodes}
    adj: dict[str, list[str]] = defaultdict(list)
    indeg = {module_id: 0 for module_id in node_ids}
    for edge in edges:
        source = str(edge.get("from_module_id") or "").strip()
        target = str(edge.get("to_module_id") or "").strip()
        if source not in node_ids or target not in node_ids or source == target:
            continue
        adj[source].append(target)
        indeg[target] = indeg.get(target, 0) + 1
    queue = sorted(module_id for module_id, degree in indeg.items() if degree == 0)
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for nxt in sorted(adj.get(current, [])):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
        queue.sort()
    for module_id in sorted(node_ids):
        if module_id not in order:
            order.append(module_id)

    is_linear_chain = len(order) > 1
    if is_linear_chain:
        for index in range(len(order) - 1):
            if not any(
                edge.get("from_module_id") == order[index] and edge.get("to_module_id") == order[index + 1]
                for edge in edges
            ):
                is_linear_chain = False
                break

    deps_map: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        target = str(edge.get("to_module_id") or "").strip()
        source = str(edge.get("from_module_id") or "").strip()
        if target in node_ids and source in node_ids:
            deps_map[target].append(source)

    node_by_id = {str(node["module_id"]): node for node in nodes}
    steps: list[dict[str, Any]] = []
    for module_id in order:
        node = node_by_id[module_id]
        meta = safe_metadata(node)
        step: dict[str, Any] = {"module_id": module_id}
        label = node.get("label")
        if label and str(label) != module_id:
            step["label"] = label
        if meta.get("command"):
            step["command"] = meta["command"]
        if meta.get("cwd"):
            step["cwd"] = meta["cwd"]
        if meta.get("critical") is False:
            step["critical"] = False
        if meta.get("description"):
            step["description"] = str(meta["description"])
        deps = sorted({dep for dep in deps_map.get(module_id, []) if dep in node_ids})
        if not is_linear_chain and deps:
            step["depends_on"] = deps[0] if len(deps) == 1 else deps
        steps.append(step)
    return steps


def sync_pipeline_yaml_from_db(
    host_id: str,
    pipeline_id: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Exporta metadata e steps da DB para o YAML — a DB é a fonte de verdade."""
    from . import runner_ssh, store

    canonical_host = runner_ssh.resolve_catalog_host_id(host_id, root)
    path = catalog_path_for_host(canonical_host, root)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pipelines = data.get("pipelines")
    if not isinstance(pipelines, list):
        raise ValueError(f"Catálogo inválido (sem pipelines[]): {path}")

    host_db = store.host_key(canonical_host)
    pipeline = store.get_pipeline(pipeline_id, host_db)
    if not pipeline:
        raise ValueError(f"Pipeline '{pipeline_id}' não encontrado na DB para {canonical_host}")

    dag = store.get_pipeline_dag(pipeline_id, host_db, include_inventory=False)
    nodes = [
        node
        for node in (dag.get("nodes") or [])
        if str(node.get("type") or "task") != "inventory"
    ]
    edges = dag.get("edges") or []
    meta = safe_metadata(pipeline)
    schedule = str(pipeline.get("schedule") or "manual")

    found = False
    for entry in pipelines:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("id") or "") != pipeline_id:
            continue
        found = True
        entry["name"] = str(pipeline.get("name") or pipeline_id)
        entry["owner"] = str(pipeline.get("owner") or "unknown")
        entry["criticality"] = str(pipeline.get("criticality") or "medium").lower()
        entry["schedule"] = schedule
        prev_schedule = meta.get("prev_schedule") or pipeline.get("prev_schedule")
        if prev_schedule and schedule.lower() == "paused":
            entry["prev_schedule"] = str(prev_schedule)
        else:
            entry.pop("prev_schedule", None)
        if meta.get("suspended"):
            entry["suspended"] = True
        else:
            entry.pop("suspended", None)
        steps = dag_to_yaml_steps(nodes, edges)
        if steps:
            entry["steps"] = steps
        break

    if not found:
        raise ValueError(f"Pipeline '{pipeline_id}' não encontrado em {path.name}")

    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    logger.info("Catálogo YAML sincronizado da DB: %s (%s)", path, pipeline_id)
    return {
        "path": str(path),
        "pipeline_id": pipeline_id,
        "host_id": canonical_host,
        "synced_from": "db",
    }


def export_catalog_from_db(*, host_id: str | None = None, root: Path | None = None) -> dict[str, Any]:
    """Sincroniza todos os pipelines com YAML a partir da DB."""
    from . import runner_ssh, store

    exported: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    filter_host = runner_ssh.resolve_catalog_host_id(host_id, root).lower() if host_id else ""

    for deployment in store.list_deployments():
        if deployment.get("catalog_source") == "runs_only":
            continue
        pipeline_id = str(deployment.get("pipeline_id") or "").strip()
        catalog_host = str(deployment.get("catalog_host") or deployment.get("host_id") or "").strip()
        if not pipeline_id or not catalog_host:
            continue
        try:
            canonical = runner_ssh.resolve_catalog_host_id(catalog_host, root)
            if filter_host and canonical.lower() != filter_host:
                continue
            exported.append(sync_pipeline_yaml_from_db(canonical, pipeline_id, root=root))
        except FileNotFoundError as exc:
            errors.append({"pipeline_id": pipeline_id, "host_id": catalog_host, "error": str(exc)})
        except ValueError as exc:
            errors.append({"pipeline_id": pipeline_id, "host_id": catalog_host, "error": str(exc)})

    return {"exported": exported, "errors": errors}
