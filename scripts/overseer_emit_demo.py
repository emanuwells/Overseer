from __future__ import annotations

import os
import socket
import time
from datetime import datetime, timezone
from typing import Any

import httpx


API_URL = os.getenv("OVERSEER_API_URL", "http://127.0.0.1:8090").rstrip("/")
API_TOKEN = os.getenv("OVERSEER_API_TOKEN", "").strip()
PIPELINE_ID = os.getenv("OVERSEER_DEMO_PIPELINE", "microsoft_forms_2_datalake")


def headers() -> dict[str, str]:
    value = {"Accept": "application/json", "Content-Type": "application/json"}
    if API_TOKEN:
        value["Authorization"] = f"Bearer {API_TOKEN}"
    return value


def post(client: httpx.Client, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"{API_URL}{path}", json=payload, headers=headers())
    response.raise_for_status()
    return response.json()


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    host = socket.gethostname()
    started = time.monotonic()
    with httpx.Client(timeout=30) as client:
        post(
            client,
            "/v1/events/heartbeat",
            {
                "source_id": f"demo-{host}",
                "source_type": "demo",
                "pipeline_id": PIPELINE_ID,
                "hostname": host,
                "status": "ok",
                "payload": {"source": "scripts/overseer_emit_demo.py"},
            },
        )
        run = post(
            client,
            "/v1/events/runs/start",
            {
                "pipeline_id": PIPELINE_ID,
                "pipeline_name": "Microsoft Forms to Datalake",
                "trigger_type": "demo",
                "requested_by": "overseer-demo",
                "runner_host": host,
                "hostname": host,
                "metadata": {"flow": "official-db-smoke"},
            },
        )["run"]
        run_id = run["run_id"]
        modules = [
            ("extract_forms", "ok", 4.2, "Leitura de respostas Microsoft Forms concluída."),
            ("validate_payload", "ok", 1.1, "Validação de schema e campos obrigatórios concluída."),
            ("load_datalake", "ok", 2.8, "Carga no datalake simulada com sucesso."),
        ]
        for module_id, status, duration, message in modules:
            post(
                client,
                "/v1/events/modules",
                {
                    "run_id": run_id,
                    "pipeline_id": PIPELINE_ID,
                    "module_id": module_id,
                    "status": status,
                    "ended_at": now(),
                    "duration_sec": duration,
                    "metadata": {"demo": True},
                },
            )
            post(
                client,
                "/v1/events/logs",
                {
                    "run_id": run_id,
                    "pipeline_id": PIPELINE_ID,
                    "module_id": module_id,
                    "level": "info",
                    "event_type": "demo",
                    "message": message,
                    "metadata": {"demo": True},
                },
            )
        post(
            client,
            f"/v1/events/runs/{run_id}/finish",
            {
                "status": "ok",
                "ended_at": now(),
                "duration_sec": round(time.monotonic() - started, 3),
                "exit_code": 0,
                "metadata": {"flow": "official-db-smoke", "modules": len(modules)},
            },
        )
    print(f"Demo enviada para {API_URL} com run_id={run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
