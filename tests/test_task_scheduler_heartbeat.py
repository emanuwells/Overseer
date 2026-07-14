from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from overseer_agent import __version__
from overseer_agent import __main__ as agent_main
from overseer_api.main import create_app
from overseer_core import store


@pytest.fixture
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def test_agent_heartbeat_merges_payload_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(
        json.dumps(
            {
                "agent_version": "external",
                "api_reachable": True,
                "task_scheduler": {"ok": True, "pipelines": [{"pipeline_id": "demo"}]},
            }
        ),
        encoding="utf-8",
    )
    sent: dict[str, Any] = {}

    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def heartbeat(self, **kwargs: Any) -> dict[str, Any]:
            sent.update(kwargs)
            return {"heartbeat": {"source_id": "host-a"}}

    monkeypatch.setattr(agent_main, "_probe_api", lambda _api_url: False)
    monkeypatch.setattr(agent_main, "OverseerClient", FakeClient)

    code = agent_main.cmd_heartbeat(argparse.Namespace(payload_file=str(payload_file)))

    assert code == 0
    assert sent["status"] == "degraded"
    assert sent["payload"]["agent_version"] == __version__
    assert sent["payload"]["api_reachable"] is False
    assert sent["payload"]["task_scheduler"]["pipelines"][0]["pipeline_id"] == "demo"


def test_agent_heartbeat_rejects_invalid_payload_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_file = tmp_path / "payload.json"
    payload_file.write_text("[1, 2, 3]", encoding="utf-8")

    code = agent_main.cmd_heartbeat(argparse.Namespace(payload_file=str(payload_file)))

    assert code == 2
    assert "objeto JSON" in capsys.readouterr().err


def test_record_heartbeat_preserves_task_scheduler_payload(sqlite_store) -> None:
    heartbeat = store.record_heartbeat(
        {
            "source_id": "windows-host",
            "host_id": "windows-host",
            "status": "ok",
            "payload": {
                "task_scheduler": {
                    "ok": True,
                    "pipelines": [{"pipeline_id": "example_pipeline", "task_found": True}],
                }
            },
        }
    )

    assert heartbeat["payload"]["task_scheduler"]["ok"] is True
    assert heartbeat["payload"]["task_scheduler"]["pipelines"][0]["task_found"] is True


def test_read_heartbeats_returns_task_scheduler_payload(sqlite_store) -> None:
    store.record_heartbeat(
        {
            "source_id": "windows-host",
            "host_id": "windows-host",
            "status": "ok",
            "payload": {
                "task_scheduler": {
                    "ok": True,
                    "pipelines": [{"pipeline_id": "example_pipeline", "next_run_time": "2026-06-17T07:30:00Z"}],
                }
            },
        }
    )
    app = create_app()
    app.router.on_startup.clear()
    client = TestClient(app)

    response = client.get("/v1/read/heartbeats?limit=1")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["payload"]["task_scheduler"]["pipelines"][0]["pipeline_id"] == "example_pipeline"
