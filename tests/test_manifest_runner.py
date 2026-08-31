from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from overseer_sdk.manifest_runner import (
    _catalog_nodes_edges,
    load_manifest,
    register_catalog,
    run_manifest,
)

MANIFEST_YAML = """
pipeline_id: forms_to_lake
pipeline_name: Forms to Lake
owner: data
steps:
  - module_id: extract
    command: ["python3", "extract.py"]
  - module_id: load
    command: ["python3", "load.py"]
"""


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "manifest.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_manifest_parses_steps(tmp_path):
    manifest = load_manifest(_write(tmp_path, MANIFEST_YAML))
    assert manifest.pipeline_id == "forms_to_lake"
    assert manifest.name == "Forms to Lake"
    assert [step.module_id for step in manifest.steps] == ["extract", "load"]
    assert manifest.steps[0].command == ["python3", "extract.py"]
    assert manifest.steps[0].warning_exit_codes == frozenset()


def test_load_manifest_requires_pipeline_id(tmp_path):
    with pytest.raises(ValueError, match="pipeline_id"):
        load_manifest(_write(tmp_path, "steps: []\n"))


def test_load_manifest_requires_steps(tmp_path):
    with pytest.raises(ValueError, match="steps"):
        load_manifest(_write(tmp_path, "pipeline_id: x\n"))


def test_load_manifest_rejects_duplicate_module_id(tmp_path):
    content = """
pipeline_id: x
steps:
  - module_id: a
    command: ["echo", "1"]
  - module_id: a
    command: ["echo", "2"]
"""
    with pytest.raises(ValueError, match="duplicado"):
        load_manifest(_write(tmp_path, content))


@pytest.mark.parametrize("value", ["2", 0, [0], [-1], [True], ["2"]])
def test_load_manifest_rejects_invalid_warning_exit_codes(tmp_path, value):
    content = f"""
pipeline_id: x
steps:
  - module_id: a
    command: ["echo", "1"]
    warning_exit_codes: {value!r}
"""
    with pytest.raises(ValueError, match="warning_exit_codes|warning exit code"):
        load_manifest(_write(tmp_path, content))


def test_catalog_nodes_edges_linear(tmp_path):
    manifest = load_manifest(_write(tmp_path, MANIFEST_YAML))
    nodes, edges = _catalog_nodes_edges(manifest)
    assert [node["module_id"] for node in nodes] == ["extract", "load"]
    assert nodes[0]["metadata"]["command"] == ["python3", "extract.py"]
    assert edges == [{"from_module_id": "extract", "to_module_id": "load"}]


def test_register_catalog_calls_client(tmp_path):
    manifest = load_manifest(_write(tmp_path, MANIFEST_YAML))
    client = MagicMock()
    register_catalog(manifest, client)
    client.register_pipeline.assert_called_once()
    kwargs = client.register_pipeline.call_args.kwargs
    assert kwargs["pipeline_id"] == "forms_to_lake"
    assert len(kwargs["nodes"]) == 2


def test_run_manifest_success(tmp_path, monkeypatch):
    manifest = load_manifest(_write(tmp_path, MANIFEST_YAML))
    client = MagicMock()
    client.start_run.return_value = "run-1"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("overseer_sdk.manifest_runner.run_subprocess_with_telemetry", fake_run)
    exit_code = run_manifest(manifest, client=client)

    assert exit_code == 0
    assert client.module.call_count == 2
    finish_kwargs = client.finish_run.call_args.kwargs
    assert finish_kwargs["status"] == "ok"


def test_run_manifest_stops_on_failure(tmp_path, monkeypatch):
    manifest = load_manifest(_write(tmp_path, MANIFEST_YAML))
    client = MagicMock()
    client.start_run.return_value = "run-1"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="boom")

    monkeypatch.setattr("overseer_sdk.manifest_runner.run_subprocess_with_telemetry", fake_run)
    exit_code = run_manifest(manifest, client=client)

    assert exit_code == 2
    assert client.module.call_count == 1
    finish_kwargs = client.finish_run.call_args.kwargs
    assert finish_kwargs["status"] == "failed"
    assert finish_kwargs["exit_code"] == 2


def test_run_manifest_records_warning_and_continues(tmp_path, monkeypatch):
    content = """
pipeline_id: warning_pipeline
steps:
  - module_id: partial
    command: ["python3", "partial.py"]
    warning_exit_codes: [2]
  - module_id: next
    command: ["python3", "next.py"]
"""
    manifest = load_manifest(_write(tmp_path, content))
    client = MagicMock()
    client.start_run.return_value = "run-warning"
    results = iter(
        [
            subprocess.CompletedProcess([], 2, stdout="partial", stderr="camera unavailable"),
            subprocess.CompletedProcess([], 0, stdout="ok", stderr=""),
        ]
    )

    monkeypatch.setattr(
        "overseer_sdk.manifest_runner.run_subprocess_with_telemetry",
        lambda command, **kwargs: next(results),
    )

    exit_code = run_manifest(manifest, client=client)

    assert exit_code == 0
    assert [call.kwargs["status"] for call in client.module.call_args_list] == ["warning", "ok"]
    finish_kwargs = client.finish_run.call_args.kwargs
    assert finish_kwargs["status"] == "warning"
    assert finish_kwargs["exit_code"] == 2
    assert any(call.kwargs.get("level") == "warning" for call in client.log.call_args_list)


def test_run_manifest_failure_overrides_previous_warning(tmp_path, monkeypatch):
    content = """
pipeline_id: warning_then_failure
steps:
  - module_id: partial
    command: ["python3", "partial.py"]
    warning_exit_codes: [2]
  - module_id: failed
    command: ["python3", "failed.py"]
"""
    manifest = load_manifest(_write(tmp_path, content))
    client = MagicMock()
    client.start_run.return_value = "run-failed"
    results = iter(
        [
            subprocess.CompletedProcess([], 2, stdout="", stderr="partial"),
            subprocess.CompletedProcess([], 3, stdout="", stderr="failed"),
        ]
    )

    monkeypatch.setattr(
        "overseer_sdk.manifest_runner.run_subprocess_with_telemetry",
        lambda command, **kwargs: next(results),
    )

    exit_code = run_manifest(manifest, client=client)

    assert exit_code == 3
    finish_kwargs = client.finish_run.call_args.kwargs
    assert finish_kwargs["status"] == "failed"
    assert finish_kwargs["exit_code"] == 3
