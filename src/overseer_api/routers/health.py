from __future__ import annotations

from fastapi import APIRouter

from ..builders.payload import build_health

router = APIRouter(tags=["health"])


@router.get("/v1/health")
def health() -> dict:
    status = build_health()
    return {
        "ok": bool(status.get("ok", True)),
        "status": status,
        "dataFreshness": status.get("dataFreshness"),
        "db_now_utc": status.get("db_now_utc"),
        "db_reachability": {
            "overseer_api_db": status.get("db_connectivity", {})
            .get("overseer", {})
            .get("reachable", False),
            "error": status.get("db_connectivity", {}).get("overseer", {}).get("error"),
        },
    }
