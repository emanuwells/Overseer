from __future__ import annotations

from scripts.export_payload_from_db import (  # noqa: PLC0415 — shared canonical builder
    build_health_status,
    build_monitoring_payload,
    build_ops_fast,
    build_ops_heavy,
)


def build_full() -> dict:
    payload, _details = build_monitoring_payload(sweep_stale=True)
    return payload


def build_details() -> dict:
    _payload, details = build_monitoring_payload(sweep_stale=True)
    return details


def build_health() -> dict:
    try:
        payload, _ = build_monitoring_payload(sweep_stale=False)
        rows = len(payload.get("rows") or [])
    except Exception as exc:
        status = build_health_status()
        status["ok"] = False
        status["db_connectivity"]["overseer"]["reachable"] = False
        status["db_connectivity"]["overseer"]["error"] = str(exc)[:500]
        return status
    return build_health_status(rows=rows)
