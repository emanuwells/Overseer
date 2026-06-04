from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.overseer_api.main import create_app


def client() -> TestClient:
    app = create_app()
    app.router.on_startup.clear()
    return TestClient(app)


def test_health_shape():
    with patch("src.overseer_api.routers.health.get_engine") as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value.execute.return_value.first.return_value = [1]
        response = client().get("/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "overseer-api"


@patch("src.overseer_api.routers.read.store.overview")
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


@patch("src.overseer_api.routers.read.store.database_status")
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


@patch("src.overseer_api.routers.events.store.start_run")
def test_event_run_start(mock_start_run):
    mock_start_run.return_value = {"run_id": "run-1", "pipeline_id": "demo", "status": "running"}
    response = client().post("/v1/events/runs/start", json={"pipeline_id": "demo"})
    assert response.status_code == 200
    assert response.json()["run"]["run_id"] == "run-1"


@patch("src.overseer_api.routers.orchestrate.store.enqueue_trigger")
@patch("src.overseer_api.routers.orchestrate.store.get_pipeline")
def test_orchestrate_trigger(mock_get_pipeline, mock_enqueue):
    mock_get_pipeline.return_value = {"pipeline_id": "demo"}
    mock_enqueue.return_value = {"trigger_id": "trg-1", "pipeline_id": "demo", "status": "queued"}
    response = client().post("/v1/orchestrate/triggers", json={"pipeline_id": "demo"})
    assert response.status_code == 200
    assert response.json()["trigger"]["status"] == "queued"
