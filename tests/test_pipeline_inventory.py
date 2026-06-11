from __future__ import annotations

from overseer_core import pipeline_inventory


def test_relative_module_id_windows() -> None:
    cwd = r"C:\MAIATRON\Medidata_Pipeline\pipeline"
    full = r"C:\MAIATRON\Medidata_Pipeline\pipeline\steps\extract.py"
    assert pipeline_inventory._relative_module_id(cwd, full) == "steps/extract"


def test_workspace_paths_from_nodes() -> None:
    nodes = [
        {"module_id": "run", "metadata": {"cwd": "/opt/pipeline", "command": ["python", "run.py"]}},
    ]
    assert pipeline_inventory.workspace_paths_from_nodes(nodes) == ["/opt/pipeline"]
