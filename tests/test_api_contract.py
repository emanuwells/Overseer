from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from overseer_api.main import create_app
from overseer_core import store


def client() -> TestClient:
    app = create_app()
    app.router.on_startup.clear()
    return TestClient(app)


def test_monitoring_routes_removed():
    response = client().get("/v1/monitoring/ops/fast")
    assert response.status_code == 404


def test_health_shape():
    with patch("overseer_api.routers.health.get_engine") as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = [1]
        response = client().get("/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "overseer-api"


@patch("overseer_api.routers.read.store.overview")
def test_read_overview(mock_overview):
    mock_overview.return_value = {
        "summary": {"pipelines": 1, "runs": 1},
        "pipelines": [{"pipeline_id": "demo"}],
        "recent_runs": [],
    }
    response = client().get("/v1/read/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["summary"]["pipelines"] == 1


@patch("overseer_api.routers.read.store.database_status")
def test_read_database(mock_database):
    mock_database.return_value = {
        "reachable": True,
        "mode": "external",
        "driver": "mysql+pymysql",
        "database": "Overseer",
        "url": "mysql+pymysql://user:***@db:3306/Overseer",
        "tables": {"runs": 3},
    }
    response = client().get("/v1/read/database")
    assert response.status_code == 200
    assert response.json()["database"]["mode"] == "external"


@patch("overseer_api.routers.events.store.start_run")
def test_event_run_start(mock_start_run):
    mock_start_run.return_value = {"run_id": "run-1", "pipeline_id": "demo", "status": "running"}
    response = client().post("/v1/events/runs/start", json={"pipeline_id": "demo"})
    assert response.status_code == 200
    assert response.json()["run"]["run_id"] == "run-1"


@patch("overseer_api.routers.orchestrate.runner_ssh.execute_pipeline_run")
@patch("overseer_api.routers.orchestrate.store.complete_trigger")
@patch("overseer_api.routers.orchestrate.store.claim_trigger")
@patch("overseer_api.routers.orchestrate.store.enqueue_trigger")
@patch("overseer_api.routers.orchestrate.runner_ssh.ssh_sync_enabled", return_value=True)
@patch("overseer_api.routers.orchestrate.store.find_pipeline_catalog")
def test_orchestrate_trigger(
    mock_find,
    _mock_ssh_enabled,
    mock_enqueue,
    mock_claim,
    mock_complete,
    mock_dispatch,
):
    mock_find.return_value = {"pipeline_id": "demo", "host_id": "BAZE2", "metadata": {}}
    mock_enqueue.return_value = {"trigger_id": "trg-1", "pipeline_id": "demo", "status": "queued"}
    mock_claim.return_value = {"trigger_id": "trg-1", "status": "claimed"}
    mock_dispatch.return_value = {"ok": True, "host": "baze2", "exit_code": 0}
    mock_complete.return_value = {"trigger_id": "trg-1", "status": "done"}
    response = client().post(
        "/v1/orchestrate/triggers",
        json={"pipeline_id": "demo", "host_id": "BAZE2"},
    )
    assert response.status_code == 200
    assert response.json()["trigger"]["status"] == "done"


def test_root_redirects_to_dashboard():
    response = client().get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/dashboard.html"


def test_ui_root_redirects_to_dashboard():
    response = client().get("/ui", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/dashboard.html"


def test_pipeline_catalog_registers_dag(tmp_path, monkeypatch):
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{tmp_path / 'overseer.db'}")
    store._engine = None
    store.init_schema()
    api = client()
    payload = {
        "pipeline_id": "demo_pipeline",
        "name": "Demo Pipeline",
        "owner": "data",
        "criticality": "medium",
        "schedule": "manual",
        "metadata": {"area": "demo"},
        "nodes": [
            {"module_id": "extract", "label": "Extrair", "type": "task"},
            {"module_id": "load", "label": "Carregar", "type": "task"},
        ],
        "edges": [{"from_module_id": "extract", "to_module_id": "load"}],
    }

    response = api.post("/v1/catalog/pipelines", json=payload)
    assert response.status_code == 200
    assert response.json()["dag"]["pipeline"]["pipeline_id"] == "demo_pipeline"

    response = api.get("/v1/read/pipelines/demo_pipeline/dag")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["dag"]["nodes"]) == 2
    assert body["dag"]["edges"][0]["from_module_id"] == "extract"


def test_module_events_still_reference_pipeline_and_module(tmp_path, monkeypatch):
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{tmp_path / 'overseer.db'}")
    store._engine = None
    store.init_schema()
    api = client()
    api.post(
        "/v1/catalog/pipelines",
        json={
            "pipeline_id": "demo_pipeline",
            "nodes": [{"module_id": "extract"}],
            "edges": [],
        },
    )
    run = api.post("/v1/events/runs/start", json={"pipeline_id": "demo_pipeline"}).json()["run"]

    response = api.post(
        "/v1/events/modules",
        json={
            "run_id": run["run_id"],
            "pipeline_id": "demo_pipeline",
            "module_id": "extract",
            "status": "ok",
        },
    )
    assert response.status_code == 200
    module = response.json()["module"]
    assert module["pipeline_id"] == "demo_pipeline"
    assert module["module_id"] == "extract"


def test_local_pipeline_execution_endpoint_removed():
    response = client().post("/v1/orchestrate/pipelines/demo/run", json={"requested_by": "test"})
    assert response.status_code == 404
