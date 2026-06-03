from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from src.pm_runtime.db import get_engine

AGENT_VERSION = "1.0.0"


def register_runner(
    *,
    hostname: str | None = None,
    agent_version: str = AGENT_VERSION,
    os_name: str | None = None,
    os_release: str | None = None,
) -> dict[str, Any]:
    host = (hostname or socket.gethostname()).strip().lower() or "unknown-runner"
    os_n = os_name or platform.system()
    os_r = os_release or platform.release()
    now = datetime.now(timezone.utc)

    engine = get_engine()
    sql = text(
        """
        INSERT INTO overseer_runners
            (hostname, os_name, os_release, agent_version, last_seen_at, created_at, updated_at)
        VALUES
            (:hostname, :os_name, :os_release, :agent_version, :last_seen, :last_seen, :last_seen)
        ON DUPLICATE KEY UPDATE
            os_name = VALUES(os_name),
            os_release = VALUES(os_release),
            agent_version = VALUES(agent_version),
            last_seen_at = VALUES(last_seen_at),
            updated_at = VALUES(last_seen_at)
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "hostname": host,
                "os_name": os_n,
                "os_release": os_r,
                "agent_version": agent_version,
                "last_seen": now.replace(tzinfo=None),
            },
        )

    return {
        "hostname": host,
        "os_name": os_n,
        "os_release": os_r,
        "agent_version": agent_version,
        "last_seen_at": now.isoformat().replace("+00:00", "Z"),
    }


def list_runners(*, limit: int = 200) -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(
        """
        SELECT hostname, os_name AS osName, os_release AS osRelease,
               agent_version AS agentVersion, last_seen_at AS lastSeenAt
          FROM overseer_runners
         ORDER BY last_seen_at DESC
         LIMIT :lim
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, {"lim": max(1, min(limit, 500))}).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        return []
