from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from overseer_core import deployment_health, store


@pytest.fixture()
def sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "metrics.db"
    monkeypatch.setenv("OVERSEER_DB_URL", f"sqlite:///{db_path}")
    store._engine = None  # noqa: SLF001
    store.init_schema()
    yield
    store._engine = None  # noqa: SLF001


def _finished_run(status: str, started_at: datetime) -> None:
    run = store.start_run({"pipeline_id": f"pipeline_{status}", "host_id": "host"})
    store.finish_run(run["run_id"], {"status": status})
    with store.get_engine().begin() as connection:
        connection.execute(
            store.runs_table.update()
            .where(store.runs_table.c.run_id == run["run_id"])
            .values(started_at=started_at, ended_at=started_at + timedelta(seconds=1))
        )


def test_operational_metrics_are_exact_and_warning_is_success(sqlite_store) -> None:
    now = datetime(2026, 8, 31, 12, 0, 0)
    _finished_run("ok", now - timedelta(hours=1))
    _finished_run("warning", now - timedelta(hours=2))
    _finished_run("failed", now - timedelta(hours=3))
    _finished_run("ok", now - timedelta(days=7, hours=12))

    metrics = store.operational_run_metrics(now=now)

    assert metrics["total_runs"] == 4
    assert metrics["ok_7d"] == 1
    assert metrics["warning_7d"] == 1
    assert metrics["failed_7d"] == 1
    assert metrics["terminal_7d"] == 3
    assert metrics["runs_24h"] == 3
    assert metrics["success_rate_7d"] == 66.67
    assert metrics["volume"]["baseline"] == pytest.approx(1 / 7, abs=0.01)


def test_summary_counts_current_warning_and_failure_deployments() -> None:
    metrics = {
        "total_runs": 3,
        "ok": 1,
        "warning": 1,
        "failed": 1,
        "running": 0,
        "ok_7d": 1,
        "warning_7d": 1,
        "failed_7d": 1,
        "terminal": 3,
        "terminal_7d": 3,
        "success_rate": 66.67,
        "success_rate_7d": 66.67,
        "runs_24h": 3,
        "volume": {"status": "good", "ratio": 1.0, "runs24h": 3, "baseline": 3.0},
    }
    summary = deployment_health.build_operational_summary(
        [],
        [
            {"pipeline_id": "ok", "last_status": "ok", "schedule": "manual"},
            {"pipeline_id": "warn", "last_status": "warning", "schedule": "manual"},
            {"pipeline_id": "fail", "last_status": "failed", "schedule": "manual"},
        ],
        run_metrics=metrics,
    )

    assert summary["warning_deployments"] == 1
    assert summary["failed_deployments"] == 1
    assert summary["operational_status"] == "failed"
    assert summary["success_rate_7d"] == 66.67


@pytest.mark.parametrize(
    ("deployments", "expected"),
    [
        ([{"pipeline_id": "ok", "last_status": "ok"}], "ok"),
        ([{"pipeline_id": "warn", "last_status": "warning"}], "warning"),
        ([{"pipeline_id": "fail", "last_status": "failed"}], "failed"),
        (
            [
                {"pipeline_id": "warn", "last_status": "warning"},
                {"pipeline_id": "fail", "last_status": "failed"},
            ],
            "failed",
        ),
        ([{"pipeline_id": "stale", "last_status": "ok", "is_stale": True}], "warning"),
    ],
)
def test_operational_status_precedence(
    deployments: list[dict[str, object]], expected: str
) -> None:
    summary = deployment_health.build_operational_summary([], deployments)

    assert summary["operational_status"] == expected


def test_operational_status_ignores_inactive_deployments_and_includes_future_catalog_rows() -> None:
    summary = deployment_health.build_operational_summary(
        [],
        [
            {"pipeline_id": "inactive_failure", "last_status": "failed", "active": False},
            {"pipeline_id": "future_pipeline", "last_status": "warning", "active": True},
        ],
    )

    assert summary["pipelines"] == 1
    assert summary["failed_deployments"] == 0
    assert summary["warning_deployments"] == 1
    assert summary["operational_status"] == "warning"
