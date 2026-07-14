"""Descobre ficheiros de módulos no workspace de cada pipeline (cwd do catálogo)."""

from __future__ import annotations

import logging
import os
import shlex
from fnmatch import fnmatch
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import Any

from . import runner_ssh

logger = logging.getLogger("overseer.pipeline_inventory")

MAX_FILES = 500
DISCOVERY_TIMEOUT = int(os.getenv("OVERSEER_INVENTORY_TIMEOUT", "20"))
DEFAULT_INVENTORY_GLOBS = ["*.py"]


def _node_metadata(node: dict[str, Any]) -> dict[str, Any]:
    meta = node.get("metadata")
    if isinstance(meta, dict):
        return meta
    return {}


def workspace_paths_from_nodes(nodes: list[dict[str, Any]]) -> list[str]:
    paths: set[str] = set()
    for node in nodes:
        meta = _node_metadata(node)
        cwd = str(meta.get("cwd") or "").strip()
        if cwd:
            paths.add(cwd)
    return sorted(paths)


def _relative_module_id(cwd: str, full_path: str) -> str:
    try:
        cwd_path = PureWindowsPath(cwd) if (":" in cwd or cwd.startswith("\\\\")) else PurePosixPath(cwd)
        file_path = PureWindowsPath(full_path) if (":" in full_path or full_path.startswith("\\\\")) else PurePosixPath(full_path)
        rel = file_path.relative_to(cwd_path)
        stem = str(rel.with_suffix("")).replace("\\", "/")
        return stem or file_path.stem
    except Exception:
        return PurePath(full_path).stem


def _normalise_patterns(patterns: list[str] | None) -> list[str]:
    cleaned = [str(pattern or "").strip() for pattern in (patterns or [])]
    return [pattern for pattern in cleaned if pattern] or list(DEFAULT_INVENTORY_GLOBS)


def _matches_glob(name: str, pattern: str) -> bool:
    return fnmatch(name.lower(), pattern.lower())


def _build_discovery_command(cwd: str, platform: str, patterns: list[str] | None = None) -> str:
    selected = _normalise_patterns(patterns)
    if platform == "windows":
        escaped = cwd.replace("'", "''")
        escaped_patterns = [pattern.replace("'", "''") for pattern in selected]
        filters = " -or ".join(f"$_.Name -like '{pattern}'" for pattern in escaped_patterns)
        return (
            "powershell -NoProfile -Command "
            f"\"Get-ChildItem -LiteralPath '{escaped}' -Recurse -File "
            f"| Where-Object {{ {filters} }} "
            f"| Select-Object -First {MAX_FILES} "
            f"| ForEach-Object {{ $_.FullName }}\""
        )
    cwd_q = shlex.quote(cwd)
    name_expr = " -o ".join(f"-name {shlex.quote(pattern)}" for pattern in selected)
    return f"find {cwd_q} -type f \\( {name_expr} \\) 2>/dev/null | head -n {MAX_FILES}"


def _run_on_host(host_id: str, command: str) -> tuple[int, str]:
    canonical = runner_ssh.resolve_catalog_host_id(host_id)
    cfg = runner_ssh.get_host_config(canonical)
    ssh_target = str(cfg.get("ssh") or "").strip()
    if runner_ssh.is_local_ssh_target(ssh_target):
        result = runner_ssh._run_local(command, timeout=DISCOVERY_TIMEOUT)
    else:
        result = runner_ssh._run_ssh(ssh_target, command, timeout=DISCOVERY_TIMEOUT)
    return int(result.get("exit_code", 1)), str(result.get("stdout") or "")


def discover_files(
    host_id: str,
    cwd: str,
    *,
    platform: str = "linux",
    patterns: list[str] | None = None,
) -> list[str]:
    cwd = str(cwd or "").strip()
    if not cwd or not host_id:
        return []
    selected = _normalise_patterns(patterns)
    command = _build_discovery_command(cwd, platform, selected)
    try:
        exit_code, stdout = _run_on_host(host_id, command)
    except Exception as exc:
        logger.debug("Inventário falhou para %s@%s: %s", host_id, cwd, exc)
        return []
    if exit_code != 0 and not stdout.strip():
        return []
    files: list[str] = []
    for line in stdout.splitlines():
        path = line.strip()
        name = PurePath(path).name
        if any(_matches_glob(name, pattern) for pattern in selected):
            files.append(path)
    return files[:MAX_FILES]


def discover_python_files(host_id: str, cwd: str, *, platform: str = "linux") -> list[str]:
    return discover_files(host_id, cwd, platform=platform, patterns=DEFAULT_INVENTORY_GLOBS)


def discover_inventory_nodes(
    pipeline: dict[str, Any] | None,
    catalog_nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not pipeline:
        return []
    host_id = str(pipeline.get("host_id") or "").strip()
    meta = pipeline.get("metadata") if isinstance(pipeline.get("metadata"), dict) else {}
    catalog_host = str(meta.get("host_id") or host_id).strip()
    if not catalog_host:
        return []
    raw_patterns = meta.get("inventory_globs")
    patterns = [str(item) for item in raw_patterns] if isinstance(raw_patterns, list) else None

    try:
        cfg = runner_ssh.get_host_config(catalog_host)
        platform = str(cfg.get("platform") or "linux").strip().lower()
    except Exception:
        platform = "linux"

    known_ids = {str(n.get("module_id") or "").strip() for n in catalog_nodes}
    known_paths: set[str] = set()
    for node in catalog_nodes:
        meta = _node_metadata(node)
        cmd = meta.get("command")
        if isinstance(cmd, list) and len(cmd) > 1:
            known_paths.add(str(cmd[-1]).lower())
        elif isinstance(cmd, str) and cmd.strip():
            known_paths.add(cmd.strip().lower())

    inventory: list[dict[str, Any]] = []
    seen_ids: set[str] = set(known_ids)
    for cwd in workspace_paths_from_nodes(catalog_nodes):
        for full_path in discover_files(catalog_host, cwd, platform=platform, patterns=patterns):
            module_id = _relative_module_id(cwd, full_path)
            if not module_id or module_id in seen_ids:
                continue
            if full_path.lower() in known_paths:
                continue
            seen_ids.add(module_id)
            inventory.append(
                {
                    "module_id": module_id,
                    "label": PurePath(full_path).name,
                    "type": "inventory",
                    "metadata": {
                        "path": full_path,
                        "cwd": cwd,
                        "source": "folder_scan",
                    },
                }
            )
    return inventory
