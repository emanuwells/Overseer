from __future__ import annotations

from unittest.mock import MagicMock, patch

from overseer_core import pipeline_inventory


# ------------------------------------------------------------------
# _node_metadata
# ------------------------------------------------------------------


def test_node_metadata_dict() -> None:
    node = {"metadata": {"cwd": "/opt", "command": "run.py"}}
    assert pipeline_inventory._node_metadata(node) == {"cwd": "/opt", "command": "run.py"}


def test_node_metadata_missing() -> None:
    assert pipeline_inventory._node_metadata({}) == {}


def test_node_metadata_non_dict() -> None:
    assert pipeline_inventory._node_metadata({"metadata": "not_a_dict"}) == {}


# ------------------------------------------------------------------
# workspace_paths_from_nodes
# ------------------------------------------------------------------


def test_workspace_paths_empty_list() -> None:
    assert pipeline_inventory.workspace_paths_from_nodes([]) == []


def test_workspace_paths_no_cwd() -> None:
    nodes = [{"module_id": "a", "metadata": {"command": "run.py"}}]
    assert pipeline_inventory.workspace_paths_from_nodes(nodes) == []


def test_workspace_paths_multiple_nodes_same_cwd() -> None:
    nodes = [
        {"module_id": "a", "metadata": {"cwd": "/opt/pipe"}},
        {"module_id": "b", "metadata": {"cwd": "/opt/pipe"}},
    ]
    assert pipeline_inventory.workspace_paths_from_nodes(nodes) == ["/opt/pipe"]


def test_workspace_paths_multiple_unique() -> None:
    nodes = [
        {"module_id": "a", "metadata": {"cwd": "/z/pipe"}},
        {"module_id": "b", "metadata": {"cwd": "/a/pipe"}},
    ]
    result = pipeline_inventory.workspace_paths_from_nodes(nodes)
    assert result == ["/a/pipe", "/z/pipe"]


def test_workspace_paths_whitespace_cwd() -> None:
    nodes = [{"module_id": "a", "metadata": {"cwd": "  "}}]
    assert pipeline_inventory.workspace_paths_from_nodes(nodes) == []


# ------------------------------------------------------------------
# _relative_module_id
# ------------------------------------------------------------------


def test_relative_module_id_posix() -> None:
    cwd = "/opt/pipeline"
    full = "/opt/pipeline/steps/extract.py"
    assert pipeline_inventory._relative_module_id(cwd, full) == "steps/extract"


def test_relative_module_id_windows() -> None:
    cwd = r"C:\MAIATRON\Pipeline"
    full = r"C:\MAIATRON\Pipeline\utils\helper.py"
    assert pipeline_inventory._relative_module_id(cwd, full) == "utils/helper"


def test_relative_module_id_same_dir() -> None:
    cwd = "/opt/pipeline"
    full = "/opt/pipeline/main.py"
    assert pipeline_inventory._relative_module_id(cwd, full) == "main"


def test_relative_module_id_unrelated_paths() -> None:
    cwd = "/opt/pipeline"
    full = "/other/path/script.py"
    result = pipeline_inventory._relative_module_id(cwd, full)
    assert result == "script"


# ------------------------------------------------------------------
# _build_discovery_command
# ------------------------------------------------------------------


def test_build_discovery_command_linux() -> None:
    cmd = pipeline_inventory._build_discovery_command("/opt/pipe", "linux")
    assert "find" in cmd
    assert "*.py" in cmd
    assert "/opt/pipe" in cmd


def test_build_discovery_command_windows() -> None:
    cmd = pipeline_inventory._build_discovery_command(r"C:\pipe", "windows")
    assert "powershell" in cmd.lower() or "Get-ChildItem" in cmd
    assert "*.py" in cmd


def test_build_discovery_command_shell_injection_safe() -> None:
    cmd = pipeline_inventory._build_discovery_command("/opt/my dir; rm -rf /", "linux")
    assert "find" in cmd


# ------------------------------------------------------------------
# discover_python_files
# ------------------------------------------------------------------


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_success(mock_run: MagicMock) -> None:
    mock_run.return_value = (0, "/opt/pipe/main.py\n/opt/pipe/utils/helper.py\n")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == ["/opt/pipe/main.py", "/opt/pipe/utils/helper.py"]


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_empty_stdout(mock_run: MagicMock) -> None:
    mock_run.return_value = (0, "")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == []


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_error_exit(mock_run: MagicMock) -> None:
    mock_run.return_value = (1, "")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == []


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_exception(mock_run: MagicMock) -> None:
    mock_run.side_effect = RuntimeError("ssh failed")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == []


def test_discover_python_files_empty_cwd() -> None:
    result = pipeline_inventory.discover_python_files("host-1", "")
    assert result == []


def test_discover_python_files_empty_host() -> None:
    result = pipeline_inventory.discover_python_files("", "/opt/pipe")
    assert result == []


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_filters_non_py(mock_run: MagicMock) -> None:
    mock_run.return_value = (0, "/opt/pipe/readme.txt\n/opt/pipe/run.py\n")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == ["/opt/pipe/run.py"]


@patch("overseer_core.pipeline_inventory._run_on_host")
def test_discover_python_files_nonzero_exit_with_output(mock_run: MagicMock) -> None:
    mock_run.return_value = (2, "/opt/pipe/main.py\n")
    result = pipeline_inventory.discover_python_files("host-1", "/opt/pipe")
    assert result == ["/opt/pipe/main.py"]


# ------------------------------------------------------------------
# discover_inventory_nodes
# ------------------------------------------------------------------


@patch("overseer_core.pipeline_inventory.discover_python_files")
@patch("overseer_core.pipeline_inventory.runner_ssh")
def test_discover_inventory_nodes_basic(mock_ssh: MagicMock, mock_discover: MagicMock) -> None:
    mock_ssh.get_host_config.return_value = {"platform": "linux"}
    mock_discover.return_value = ["/opt/pipe/extra.py"]

    pipeline = {"host_id": "host-1", "metadata": {}}
    catalog_nodes = [
        {"module_id": "main", "metadata": {"cwd": "/opt/pipe", "command": ["python", "main.py"]}},
    ]
    result = pipeline_inventory.discover_inventory_nodes(pipeline, catalog_nodes)
    assert len(result) == 1
    assert result[0]["module_id"] == "extra"
    assert result[0]["type"] == "inventory"


def test_discover_inventory_nodes_none_pipeline() -> None:
    assert pipeline_inventory.discover_inventory_nodes(None, []) == []


def test_discover_inventory_nodes_no_host_id() -> None:
    pipeline = {"metadata": {}}
    assert pipeline_inventory.discover_inventory_nodes(pipeline, []) == []


@patch("overseer_core.pipeline_inventory.discover_python_files")
@patch("overseer_core.pipeline_inventory.runner_ssh")
def test_discover_inventory_nodes_skips_known(mock_ssh: MagicMock, mock_discover: MagicMock) -> None:
    mock_ssh.get_host_config.return_value = {"platform": "linux"}
    mock_discover.return_value = ["/opt/pipe/main.py"]

    pipeline = {"host_id": "host-1", "metadata": {}}
    catalog_nodes = [
        {"module_id": "main", "metadata": {"cwd": "/opt/pipe", "command": ["python", "main.py"]}},
    ]
    result = pipeline_inventory.discover_inventory_nodes(pipeline, catalog_nodes)
    assert result == []


@patch("overseer_core.pipeline_inventory.runner_ssh")
def test_discover_inventory_nodes_platform_fallback(mock_ssh: MagicMock) -> None:
    mock_ssh.get_host_config.side_effect = RuntimeError("no config")

    pipeline = {"host_id": "host-1", "metadata": {}}
    result = pipeline_inventory.discover_inventory_nodes(pipeline, [])
    assert result == []
