from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter
from sqlalchemy import text

from src.overseer_core.store import get_db_url, get_engine, utcnow

router = APIRouter(tags=["health"])


@router.get("/v1/health")
def health() -> dict:
    reachable = True
    error: str | None = None
    db_now: str | None = None
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text("SELECT 1")).first()
            db_now = str(row[0]) if row else "1"
    except Exception as exc:
        reachable = False
        error = str(exc)[:500]

    return {
        "ok": reachable,
        "service": "overseer-api",
        "generated_at": utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "db": {
            "reachable": reachable,
            "url_configured": bool(get_db_url()),
            "probe": db_now,
            "error": error,
        },
    }
