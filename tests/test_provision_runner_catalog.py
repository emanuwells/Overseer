from __future__ import annotations

import pathlib

import pytest

from scripts.provision_runners import (
    list_runner_catalogs,
    normalize_host_id,
    resolve_runner_catalog,
    runners_catalog_dir,
)


def test_normalize_host_id() -> None:
    assert normalize_host_id("HP-Z2-EF") == "HP-Z2-EF"
    assert normalize_host_id("win test box") == "win-test-box"


def test_resolve_runner_catalog_explicit(tmp_path: pathlib.Path) -> None:
    catalog = tmp_path / "custom.yaml"
    catalog.write_text("pipelines: []\n", encoding="utf-8")
    resolved = resolve_runner_catalog(explicit=str(catalog), repo_root=tmp_path)
    assert resolved == catalog.resolve()


def test_resolve_runner_catalog_by_hostname(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runners = tmp_path / "runners-root"
    runners.mkdir()
    catalog_dir = tmp_path / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    catalog = catalog_dir / "linux-host.yaml"
    catalog.write_text("pipelines: []\n", encoding="utf-8")

    monkeypatch.setattr("scripts.provision_runners.socket.gethostname", lambda: "linux-host")
    resolved = resolve_runner_catalog(runners_root=runners, repo_root=tmp_path)
    assert resolved == catalog.resolve()


def test_resolve_runner_catalog_from_env_host_id(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runners = tmp_path / "runners-root"
    runners.mkdir()
    (runners / ".env.overseer").write_text("OVERSEER_HOST_ID=example-host\n", encoding="utf-8")
    catalog_dir = tmp_path / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    catalog = catalog_dir / "example-host.yaml"
    catalog.write_text("pipelines: []\n", encoding="utf-8")

    monkeypatch.setattr("scripts.provision_runners.socket.gethostname", lambda: "other-host")
    resolved = resolve_runner_catalog(runners_root=runners, repo_root=tmp_path)
    assert resolved == catalog.resolve()


def test_runners_catalog_dir_uses_configured_directory(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = tmp_path / "private-runners"
    monkeypatch.setenv("OVERSEER_RUNNERS_DIR", str(configured))

    assert runners_catalog_dir(tmp_path / "repo") == configured


def test_list_runner_catalogs_excludes_templates(tmp_path: pathlib.Path) -> None:
    catalog_dir = tmp_path / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "linux-host.yaml").write_text("pipelines: []\n", encoding="utf-8")
    (catalog_dir / "_example.yaml").write_text("pipelines: []\n", encoding="utf-8")

    names = [path.name for path in list_runner_catalogs(tmp_path)]
    assert names == ["linux-host.yaml"]


def test_resolve_runner_catalog_missing_lists_available(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runners = tmp_path / "runners-root"
    runners.mkdir()
    catalog_dir = tmp_path / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "linux-host.yaml").write_text("pipelines: []\n", encoding="utf-8")

    monkeypatch.setattr("scripts.provision_runners.socket.gethostname", lambda: "unknown-host")
    with pytest.raises(FileNotFoundError, match="linux-host.yaml"):
        resolve_runner_catalog(runners_root=runners, repo_root=tmp_path)
