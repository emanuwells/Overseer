from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from overseer_sdk.client import OverseerClient, _api_url, _api_token, run_command


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------


def test_api_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OVERSEER_API_URL", raising=False)
    assert _api_url() == "http://127.0.0.1:8090"


def test_api_url_explicit() -> None:
    assert _api_url("https://custom.api/") == "https://custom.api"


def test_api_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_API_URL", "http://env-host:9090")
    assert _api_url() == "http://env-host:9090"


def test_api_token_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OVERSEER_API_TOKEN", raising=False)
    assert _api_token() == ""


def test_api_token_explicit() -> None:
    assert _api_token("my-token") == "my-token"


def test_api_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_API_TOKEN", "env-token")
    assert _api_token() == "env-token"


# ------------------------------------------------------------------
# OverseerClient.__post_init__
# ------------------------------------------------------------------


def test_client_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OVERSEER_API_URL", raising=False)
    monkeypatch.delenv("OVERSEER_API_TOKEN", raising=False)
    monkeypatch.delenv("OVERSEER_HOST_ID", raising=False)
    client = OverseerClient()
    assert client.api_url == "http://127.0.0.1:8090"
    assert client.api_token == ""
    assert client.timeout == 30.0


def test_client_with_host_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OVERSEER_HOST_ID", "baze2")
    monkeypatch.delenv("OVERSEER_API_URL", raising=False)
    monkeypatch.delenv("OVERSEER_API_TOKEN", raising=False)
    client = OverseerClient()
    assert client.host_id == "baze2"


def test_client_explicit_params() -> None:
    client = OverseerClient(
        api_url="https://my-api", api_token="tok",
        host_id="host-1", timeout=5.0,
    )
    assert client.api_url == "https://my-api"
    assert client.api_token == "tok"
    assert client.host_id == "host-1"
    assert client.timeout == 5.0


# ------------------------------------------------------------------
# _with_host / headers
# ------------------------------------------------------------------


def test_with_host_adds_host_id() -> None:
    client = OverseerClient(api_url="http://x", api_token="t", host_id="h1")
    result = client._with_host({"pipeline_id": "p1"})
    assert result == {"pipeline_id": "p1", "host_id": "h1"}


def test_with_host_no_host_id() -> None:
    client = OverseerClient(api_url="http://x", api_token="t", host_id="")
    result = client._with_host({"pipeline_id": "p1"})
    assert "host_id" not in result


def test_headers_with_token() -> None:
    client = OverseerClient(api_url="http://x", api_token="tok-123")
    h = client.headers()
    assert h["Authorization"] == "Bearer tok-123"
    assert h["Accept"] == "application/json"


def test_headers_without_token() -> None:
    client = OverseerClient(api_url="http://x", api_token="")
    h = client.headers()
    assert "Authorization" not in h


# ------------------------------------------------------------------
# post
# ------------------------------------------------------------------


@patch("overseer_sdk.client.httpx.Client")
def test_post_success(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = MagicMock()

    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = mock_response
    mock_client_cls.return_value = mock_http

    client = OverseerClient(api_url="http://test:8090", api_token="")
    result = client.post("/v1/health", {})
    assert result == {"ok": True}


# ------------------------------------------------------------------
# register_pipeline
# ------------------------------------------------------------------


@patch.object(OverseerClient, "post")
def test_register_pipeline(mock_post: MagicMock) -> None:
    mock_post.return_value = {"pipeline": {"id": "p1"}}
    client = OverseerClient(api_url="http://x", api_token="t", host_id="h1")
    result = client.register_pipeline(pipeline_id="p1", name="Test")
    mock_post.assert_called_once()
    call_path, call_payload = mock_post.call_args.args
    assert call_path == "/v1/catalog/pipelines"
    assert call_payload["pipeline_id"] == "p1"
    assert call_payload["host_id"] == "h1"


# ------------------------------------------------------------------
# start_run / finish_run
# ------------------------------------------------------------------


@patch.object(OverseerClient, "post")
def test_start_run(mock_post: MagicMock) -> None:
    mock_post.return_value = {"run": {"run_id": "run-abc"}}
    client = OverseerClient(api_url="http://x", api_token="t")
    run_id = client.start_run("pipeline-1", pipeline_name="Test")
    assert run_id == "run-abc"
    call_path = mock_post.call_args.args[0]
    assert call_path == "/v1/events/runs/start"


@patch.object(OverseerClient, "post")
def test_finish_run(mock_post: MagicMock) -> None:
    mock_post.return_value = {"run": {"status": "ok"}}
    client = OverseerClient(api_url="http://x", api_token="t")
    result = client.finish_run("run-1", status="ok", exit_code=0, duration_sec=1.5)
    call_path = mock_post.call_args.args[0]
    assert "/v1/events/runs/run-1/finish" == call_path


# ------------------------------------------------------------------
# module / log / heartbeat
# ------------------------------------------------------------------


@patch.object(OverseerClient, "post")
def test_module(mock_post: MagicMock) -> None:
    mock_post.return_value = {"module": {}}
    client = OverseerClient(api_url="http://x", api_token="t", host_id="h1")
    client.module(run_id="r1", pipeline_id="p1", module_id="m1")
    call_path = mock_post.call_args.args[0]
    assert call_path == "/v1/events/modules"


@patch.object(OverseerClient, "post")
def test_log(mock_post: MagicMock) -> None:
    mock_post.return_value = {"log": {}}
    client = OverseerClient(api_url="http://x", api_token="t")
    client.log("test message", run_id="r1", pipeline_id="p1")
    call_path = mock_post.call_args.args[0]
    assert call_path == "/v1/events/logs"


@patch.object(OverseerClient, "post")
def test_heartbeat(mock_post: MagicMock) -> None:
    mock_post.return_value = {"heartbeat": {}}
    client = OverseerClient(api_url="http://x", api_token="t")
    client.heartbeat(source_id="runner-1")
    call_path = mock_post.call_args.args[0]
    assert call_path == "/v1/events/heartbeat"


# ------------------------------------------------------------------
# run context manager
# ------------------------------------------------------------------


@patch.object(OverseerClient, "finish_run")
@patch.object(OverseerClient, "start_run", return_value="run-ctx")
def test_run_context_success(mock_start: MagicMock, mock_finish: MagicMock) -> None:
    client = OverseerClient(api_url="http://x", api_token="t")
    with client.run("pipe-1") as run_id:
        assert run_id == "run-ctx"
    mock_finish.assert_called_once()
    assert mock_finish.call_args.kwargs["status"] == "ok"


@patch.object(OverseerClient, "finish_run")
@patch.object(OverseerClient, "start_run", return_value="run-ctx")
def test_run_context_failure(mock_start: MagicMock, mock_finish: MagicMock) -> None:
    client = OverseerClient(api_url="http://x", api_token="t")
    with pytest.raises(ValueError, match="boom"):
        with client.run("pipe-1") as run_id:
            raise ValueError("boom")
    mock_finish.assert_called_once()
    assert mock_finish.call_args.kwargs["status"] == "failed"


# ------------------------------------------------------------------
# step context manager
# ------------------------------------------------------------------


@patch.object(OverseerClient, "module")
def test_step_context_success(mock_module: MagicMock) -> None:
    client = OverseerClient(api_url="http://x", api_token="t")
    with client.step(run_id="r1", pipeline_id="p1", module_id="m1"):
        pass
    mock_module.assert_called_once()
    assert mock_module.call_args.kwargs["status"] == "ok"


@patch.object(OverseerClient, "module")
def test_step_context_failure(mock_module: MagicMock) -> None:
    client = OverseerClient(api_url="http://x", api_token="t")
    with pytest.raises(RuntimeError, match="step fail"):
        with client.step(run_id="r1", pipeline_id="p1", module_id="m1"):
            raise RuntimeError("step fail")
    mock_module.assert_called_once()
    assert mock_module.call_args.kwargs["status"] == "failed"


# ------------------------------------------------------------------
# run_command
# ------------------------------------------------------------------


@patch.object(OverseerClient, "finish_run")
@patch.object(OverseerClient, "log")
@patch.object(OverseerClient, "start_run", return_value="run-cmd")
@patch("overseer_sdk.client.run_subprocess_with_telemetry")
def test_run_command_success(
    mock_subprocess: MagicMock,
    mock_start: MagicMock,
    mock_log: MagicMock,
    mock_finish: MagicMock,
) -> None:
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout="output", stderr="",
    )
    exit_code = run_command(
        ["echo", "hello"], pipeline_id="p1", pipeline_name="test",
    )
    assert exit_code == 0
    mock_finish.assert_called_once()
    assert mock_finish.call_args.kwargs["status"] == "ok"


@patch.object(OverseerClient, "finish_run")
@patch.object(OverseerClient, "log")
@patch.object(OverseerClient, "start_run", return_value="run-cmd")
@patch("overseer_sdk.client.run_subprocess_with_telemetry")
def test_run_command_failure(
    mock_subprocess: MagicMock,
    mock_start: MagicMock,
    mock_log: MagicMock,
    mock_finish: MagicMock,
) -> None:
    mock_subprocess.return_value = MagicMock(
        returncode=1, stdout="", stderr="error output",
    )
    exit_code = run_command(
        ["bad-cmd"], pipeline_id="p1",
    )
    assert exit_code == 1
    mock_finish.assert_called_once()
    assert mock_finish.call_args.kwargs["status"] == "failed"
