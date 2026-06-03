from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import text

from src.pm_runtime.db import get_engine

ROOT = Path(__file__).resolve().parents[2]
PIPELINES_DIR = ROOT / "pipelines"


def _normalize_runner(value: str | None) -> str:
    raw = (value or "any").strip().lower()
    if raw in {"", "auto", "local", "localhost", "this-host", "self", "*"}:
        return "any"
    return raw


def _valid_schedule(value: str) -> bool:
    s = value.strip().lower()
    if s in {"manual", "paused"}:
        return True
    parts = s.split()
    return len(parts) == 5 and all(parts)


def _valid_criticality(value: str) -> bool:
    return value.strip().lower() in {"low", "medium", "high", "critical"}


def load_catalog_entry(pipeline_id: str) -> dict[str, Any] | None:
    pipeline_id = pipeline_id.strip()
    if not pipeline_id:
        return None
    for path in sorted(PIPELINES_DIR.rglob("*.y*ml")):
        if any(part.startswith("_") for part in path.parts):
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if str(payload.get("pipeline_id") or "").strip() == pipeline_id:
            return payload
    return None


def enqueue_trigger(trigger: dict[str, Any]) -> None:
    engine = get_engine()
    sql = text(
        """
        INSERT INTO orchestrator_triggers_local (
          trigger_id, trigger_type, pipeline_id, requested_by, requested_by_sso,
          requested_at, source, runner_host, status, payload_json, notes,
          created_at, updated_at
        ) VALUES (
          :trigger_id, :trigger_type, :pipeline_id, :requested_by, :requested_by_sso,
          UTC_TIMESTAMP(), :source, :runner_host, 'queued', :payload_json, :notes,
          UTC_TIMESTAMP(), UTC_TIMESTAMP()
        )
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "trigger_id": trigger["trigger_id"],
                "trigger_type": trigger.get("trigger_type", "run_now"),
                "pipeline_id": trigger["pipeline_id"],
                "requested_by": trigger.get("requested_by", "api"),
                "requested_by_sso": trigger.get("requested_by_sso")
                or trigger.get("requested_by", "api"),
                "source": trigger.get("source", "overseer_api"),
                "runner_host": _normalize_runner(trigger.get("runner_host")),
                "payload_json": json.dumps(
                    trigger.get("payload_json") or {},
                    ensure_ascii=False,
                ),
                "notes": trigger.get("notes", ""),
            },
        )


def new_trigger_id(prefix: str = "trg") -> str:
    return f"{prefix}-{int(time.time())}-{secrets.token_hex(4)}"


def enqueue_run_now(
    *,
    pipeline_id: str,
    requested_by: str,
    requested_by_sso: str | None = None,
    runner_host: str = "any",
    notes: str = "",
) -> str:
    meta = load_catalog_entry(pipeline_id)
    if meta is None:
        raise ValueError("pipeline_id inexistente no catálogo.")

    trigger_id = new_trigger_id("trg")
    enqueue_trigger(
        {
            "trigger_id": trigger_id,
            "trigger_type": "run_now",
            "pipeline_id": pipeline_id,
            "requested_by": requested_by,
            "requested_by_sso": requested_by_sso or requested_by,
            "runner_host": runner_host,
            "source": "overseer_api",
            "notes": notes or "Run now via API",
            "payload_json": {
                "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "requested_by": requested_by,
                "requested_by_sso": requested_by_sso or requested_by,
            },
        }
    )
    return trigger_id


def enqueue_schedule_update(
    *,
    pipeline_id: str,
    new_schedule: str,
    requested_by: str,
    requested_by_sso: str | None = None,
    new_owner: str = "",
    new_criticality: str = "",
) -> str:
    if not _valid_schedule(new_schedule):
        raise ValueError("Schedule inválido.")
    meta = load_catalog_entry(pipeline_id)
    if meta is None:
        raise ValueError("pipeline_id inexistente no catálogo.")
    if new_criticality and not _valid_criticality(new_criticality):
        raise ValueError("criticality inválida.")

    trigger_id = new_trigger_id("sched")
    enqueue_trigger(
        {
            "trigger_id": trigger_id,
            "trigger_type": "schedule_update",
            "pipeline_id": pipeline_id,
            "requested_by": requested_by,
            "requested_by_sso": requested_by_sso or requested_by,
            "runner_host": "any",
            "source": "overseer_api",
            "notes": "Alteração de schedule via API",
            "payload_json": {
                "new_schedule": new_schedule,
                "new_owner": new_owner,
                "new_criticality": new_criticality,
                "requested_by_actor": requested_by,
                "requested_by_sso": requested_by_sso or requested_by,
            },
        }
    )
    return trigger_id


def list_triggers(*, limit: int = 500) -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(
        """
        SELECT trigger_id AS triggerId, trigger_type AS triggerType,
               pipeline_id AS pipelineId, requested_by AS requestedBy,
               requested_by_sso AS requestedBySso, requested_at AS requestedAt,
               source, runner_host AS runnerHost, status, notes,
               created_at AS createdAt
          FROM orchestrator_triggers_local
         ORDER BY created_at DESC
         LIMIT :lim
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"lim": max(1, min(limit, 2000))}).mappings().all()
    return [dict(row) for row in rows]
