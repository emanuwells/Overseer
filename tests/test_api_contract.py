from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.overseer_api.main import create_app

SAMPLE_PAYLOAD = {
    "schema_version": "3.2.0-api",
    "generated_at": "2026-06-03T12:00:00Z",
    "fields": ["id", "pipelineId"],
    "rows": [[1, "demo"]],
    "summary": {"total_runs": 1, "ok_runs": 1, "nok_runs": 0},
    "overview": {"globalKpis": {"totalRuns": 1}},
    "pipelines": [],
    "orchestrator_runs": [],
    "orchestrator_triggers": [],
}

SAMPLE_DETAILS = {"1": {"errorMessage": "", "logMessage": "ok"}}


@patch("src.overseer_api.routers.monitoring.build_full")
def test_monitoring_full(mock_build):
    mock_build.return_value = SAMPLE_PAYLOAD
    client = TestClient(create_app())
    response = client.get("/v1/monitoring/full")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "3.2.0-api"
    assert body["rows"] == [[1, "demo"]]


@patch("src.overseer_api.routers.monitoring.build_ops_fast")
@patch("src.overseer_api.routers.monitoring.build_full")
def test_monitoring_ops_fast(mock_full, mock_ops):
    mock_full.return_value = SAMPLE_PAYLOAD
    mock_ops.return_value = {
        "generated_at": SAMPLE_PAYLOAD["generated_at"],
        "overview": {},
        "summary": {},
    }
    client = TestClient(create_app())
    response = client.get("/v1/monitoring/ops/fast")
    assert response.status_code == 200
    body = response.json()
    assert "overview" in body
    assert body["generated_at"] == SAMPLE_PAYLOAD["generated_at"]


@patch("src.overseer_api.routers.health.build_health")
def test_health(mock_health):
    mock_health.return_value = {
        "ok": True,
        "db_connectivity": {"overseer": {"reachable": True}},
    }
    client = TestClient(create_app())
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
