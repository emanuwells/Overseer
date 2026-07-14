"""Nomes de exibição canónicos para pipelines (catálogo + remoção de prefixos)."""

from __future__ import annotations

import os
from typing import Any, Iterable

_DEFAULT_PREFIX_STRIP = ("Yunex ",)


def logical_pipeline_id(pipeline_id: str) -> str:
    raw = str(pipeline_id or "")
    idx = raw.rfind("__")
    if idx > 0 and raw[idx + 2 :]:
        return raw[:idx]
    return raw


def load_prefix_strip_list() -> tuple[str, ...]:
    raw = (os.getenv("OVERSEER_NAME_PREFIX_STRIP") or "").strip()
    if not raw:
        return _DEFAULT_PREFIX_STRIP
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return tuple(parts) if parts else _DEFAULT_PREFIX_STRIP


def strip_display_prefixes(name: str, prefixes: Iterable[str] | None = None) -> str:
    text = str(name or "").strip()
    if not text:
        return text
    for prefix in prefixes or load_prefix_strip_list():
        p = str(prefix)
        if not p:
            continue
        if text.lower().startswith(p.lower()):
            text = text[len(p) :].lstrip()
    return text


def _pick_shortest(*candidates: str) -> str:
    cleaned = [c.strip() for c in candidates if c and str(c).strip()]
    if not cleaned:
        return ""
    return min(cleaned, key=len)


def build_catalog_name_index(deployments: Iterable[dict[str, Any]]) -> dict[str, str]:
    """pipeline_id lógico -> nome curto preferido (após strip de prefixos)."""
    index: dict[str, str] = {}
    for item in deployments:
        pid = logical_pipeline_id(str(item.get("pipeline_id") or ""))
        if not pid:
            continue
        raw = str(item.get("name") or item.get("pipeline_name") or "").strip()
        if not raw:
            continue
        name = strip_display_prefixes(raw)
        existing = index.get(pid)
        if not existing:
            index[pid] = name
        else:
            index[pid] = _pick_shortest(existing, name)
    return index


def resolve_display_name(
    pipeline_id: str,
    host_id: str = "",
    raw_name: str | None = None,
    catalog_index: dict[str, str] | None = None,
) -> str:
    """Ordem: catálogo -> strip(raw_name) -> pipeline_id."""
    _ = host_id  # reservado para aliases por deployment no futuro
    pid = logical_pipeline_id(pipeline_id)
    if catalog_index and pid in catalog_index:
        return catalog_index[pid]
    if raw_name:
        stripped = strip_display_prefixes(str(raw_name))
        if stripped:
            return stripped
    return pid or str(raw_name or "").strip() or "--"


def normalize_pipeline_item(
    item: dict[str, Any],
    catalog_index: dict[str, str],
) -> dict[str, Any]:
    out = dict(item)
    pid = str(out.get("pipeline_id") or "")
    host = str(out.get("host_id") or "")
    raw = str(out.get("name") or out.get("pipeline_name") or "")
    display = resolve_display_name(pid, host, raw, catalog_index)
    out["name"] = display
    if "pipeline_name" in out:
        out["pipeline_name"] = display
    return out


def normalize_run_item(
    run: dict[str, Any],
    catalog_index: dict[str, str],
) -> dict[str, Any]:
    out = dict(run)
    pid = str(out.get("pipeline_id") or "")
    host = str(out.get("host_id") or "")
    raw = str(out.get("pipeline_name") or "")
    out["pipeline_name"] = resolve_display_name(pid, host, raw, catalog_index)
    return out
