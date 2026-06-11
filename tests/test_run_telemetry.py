from __future__ import annotations

from overseer_core.run_telemetry import (
    TelemetryTracker,
    enrich_finish_metadata,
    merge_run_metadata,
)


def test_merge_run_metadata_prefers_higher_peaks() -> None:
    merged = merge_run_metadata(
        {"usage_cpu": 10.0, "usage_memoria": 100.0},
        None,
        telemetry={"usage_cpu": 25.5, "usage_memoria": 256.0, "usage_mem_mb": 256.0},
    )
    assert merged["usage_cpu"] == 25.5
    assert merged["usage_memoria"] == 256.0


def test_enrich_finish_metadata_adds_cpu_and_mem() -> None:
    tracker = TelemetryTracker()
    meta = enrich_finish_metadata({"command": ["echo", "ok"]}, tracker=tracker)
    assert "usage_cpu" in meta
    assert "usage_memoria" in meta
    assert meta["usage_mem_mb"] == meta["usage_memoria"]
