from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from overseer_api.main import create_app


def client() -> TestClient:
    app = create_app()
    app.router.on_startup.clear()
    return TestClient(app)


@patch("overseer_api.routers.orchestrate.runner_ssh.execute_pipeline_run")
@patch("overseer_api.routers.orchestrate.store.complete_trigger")
@patch("overseer_api.routers.orchestrate.store.claim_trigger")
@patch("overseer_api.routers.orchestrate.store.enqueue_trigger")
@patch("overseer_api.routers.orchestrate.runner_ssh.ssh_sync_enabled", return_value=True)
@patch("overseer_api.routers.orchestrate.store.find_pipeline_catalog")
def test_orchestrate_trigger_dispatches_via_ssh(
    mock_find,
    _mock_ssh_enabled,
    mock_enqueue,
    mock_claim,
    mock_complete,
    mock_dispatch,
):
    mock_find.return_value = {
        "pipeline_id": "traffic_flow",
        "host_id": "BAZE2",
        "metadata": {},
    }
    mock_enqueue.return_value = {"trigger_id": "trg-1", "status": "queued"}
    mock_claim.return_value = {"trigger_id": "trg-1", "status": "claimed"}
    mock_dispatch.return_value = {"ok": True, "host": "baze2", "mode": "local", "exit_code": 0}
    mock_complete.return_value = {"trigger_id": "trg-1", "status": "done"}

    response = client().post(
        "/v1/orchestrate/triggers",
        json={
            "pipeline_id": "traffic_flow",
            "host_id": "BAZE2",
            "requested_by": "tester",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["dispatch"]["ok"] is True
    mock_dispatch.assert_called_once()


@patch("overseer_api.routers.orchestrate.runner_ssh.ssh_sync_enabled", return_value=True)
@patch("overseer_api.routers.orchestrate.store.find_pipeline_catalog")
def test_orchestrate_trigger_rejects_suspended(mock_find, _mock_ssh_enabled):
    mock_find.return_value = {
        "pipeline_id": "medidata_pipeline",
        "host_id": "WS1207",
        "metadata": {"suspended": True},
    }
    response = client().post(
        "/v1/orchestrate/triggers",
        json={"pipeline_id": "medidata_pipeline", "host_id": "WS1207"},
    )
    assert response.status_code == 409


@patch("overseer_api.routers.orchestrate.runner_ssh.ssh_sync_enabled", return_value=False)
def test_orchestrate_trigger_requires_ssh(_mock_ssh_enabled):
    response = client().post(
        "/v1/orchestrate/triggers",
        json={"pipeline_id": "demo", "host_id": "BAZE2"},
    )
    assert response.status_code == 503


def test_orchestrate_trigger_requires_host_id():
    response = client().post("/v1/orchestrate/triggers", json={"pipeline_id": "demo"})
    assert response.status_code == 422


@patch("overseer_core.runner_ssh._run_local")
def test_execute_pipeline_run_local(mock_local, tmp_path, monkeypatch):
    from overseer_core import runner_ssh

    hosts = tmp_path / "deploy" / "runners"
    hosts.mkdir(parents=True)
    (hosts / "hosts.yaml").write_text(
        "hosts:\n  baze2:\n    ssh: localhost\n    platform: linux\n    repo_path: /tmp\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OVERSEER_SSH_SYNC_ENABLED", "1")
    mock_local.return_value = {"exit_code": 0, "stdout": "", "stderr": ""}

    result = runner_ssh.execute_pipeline_run("baze2", "traffic_flow", requested_by="tester", root=tmp_path)
    assert result["ok"] is True
    assert result["mode"] == "local"
    assert "traffic_flow" in mock_local.call_args[0][0]


@patch("overseer_api.routers.orchestrate.runner_ssh.execute_pipeline_run")
@patch("overseer_api.routers.orchestrate.store.complete_trigger")
@patch("overseer_api.routers.orchestrate.store.claim_trigger")
@patch("overseer_api.routers.orchestrate.store.enqueue_trigger")
@patch("overseer_api.routers.orchestrate.runner_ssh.ssh_sync_enabled", return_value=True)
@patch("overseer_api.routers.orchestrate.store.find_pipeline_catalog")
def test_orchestrate_trigger_fails_when_dispatch_fails(
    mock_find,
    _mock_ssh_enabled,
    mock_enqueue,
    mock_claim,
    mock_complete,
    mock_dispatch,
):
    mock_find.return_value = {"pipeline_id": "demo", "host_id": "WS1207", "metadata": {}}
    mock_enqueue.return_value = {"trigger_id": "trg-2", "status": "queued"}
    mock_claim.return_value = {"trigger_id": "trg-2", "status": "claimed"}
    mock_dispatch.return_value = {"ok": False, "exit_code": 1, "stderr_tail": "ssh failed"}
    mock_complete.return_value = {"trigger_id": "trg-2", "status": "failed"}

    response = client().post(
        "/v1/orchestrate/triggers",
        json={"pipeline_id": "demo", "host_id": "WS1207"},
    )
    assert response.status_code == 502
