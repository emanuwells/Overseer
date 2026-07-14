from __future__ import annotations

from overseer_core import pipeline_inventory


def test_relative_module_id_windows() -> None:
    cwd = r"C:\Pipelines\Example_Pipeline\pipeline"
    full = r"C:\Pipelines\Example_Pipeline\pipeline\steps\extract.py"
    assert pipeline_inventory._relative_module_id(cwd, full) == "steps/extract"


def test_workspace_paths_from_nodes() -> None:
    nodes = [
        {"module_id": "run", "metadata": {"cwd": "/opt/pipeline", "command": ["python", "run.py"]}},
    ]
    assert pipeline_inventory.workspace_paths_from_nodes(nodes) == ["/opt/pipeline"]


def test_build_discovery_command_defaults_to_python() -> None:
    command = pipeline_inventory._build_discovery_command("/opt/pipeline", "linux")
    assert "-name '*.py'" in command


def test_discover_inventory_nodes_uses_pipeline_inventory_globs(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_inventory.runner_ssh,
        "get_host_config",
        lambda host_id: {"platform": "linux"},
    )
    monkeypatch.setattr(
        pipeline_inventory,
        "_run_on_host",
        lambda host_id, command: (
            0,
            "/opt/pipelines/scripts/operations_clean.sh\n"
            "/opt/pipelines/scripts/rotate_logs.sh\n"
            "/opt/pipelines/README.md\n",
        ),
    )

    pipeline = {
        "host_id": "LINUX-HOST",
        "metadata": {"host_id": "linux-host", "inventory_globs": ["*.sh"]},
    }
    nodes = [
        {
            "module_id": "operations_clean",
            "metadata": {
                "cwd": "/opt/pipelines",
                "command": ["bash", "/opt/pipelines/scripts/operations_clean.sh"],
            },
        }
    ]

    inventory = pipeline_inventory.discover_inventory_nodes(pipeline, nodes)

    assert [node["module_id"] for node in inventory] == ["scripts/rotate_logs"]
    assert inventory[0]["label"] == "rotate_logs.sh"
