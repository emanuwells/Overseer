from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from overseer_api.main import app
from overseer_core import store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OVERSEER_ROOT", str(tmp_path))
    monkeypatch.setenv("OVERSEER_API_TOKEN", "test-token")
    store._engine = None
    store.init_schema()
    yield
    store._engine = None


def _write_catalog(root: Path) -> None:
    catalog_dir = root / "deploy" / "runners"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "baze2.yaml").write_text(
        yaml.dump(
            {
                "pipelines": [
                    {
                        "id": "demo_pipe",
                        "name": "Demo",
                        "owner": "data",
                        "schedule": "manual",
                        "steps": [{"module_id": "demo_pipe", "command": ["echo", "ok"]}],
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_reconcile_registers_yaml_pipelines(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    result = store.reconcile_catalog_from_yaml()
    assert len(result["created"]) == 1
    row = store.get_pipeline("demo_pipe", "BAZE2")
    assert row is not None
    assert row["owner"] == "data"


def test_reconcile_api_endpoint(sqlite_store, tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    client = TestClient(app)
    response = client.post(
        "/v1/catalog/reconcile",
        json={"sync_remote": False},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert len(payload["reconcile"]["created"]) == 1
