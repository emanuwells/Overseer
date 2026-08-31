"""Process telemetry helpers for pipeline runs (CPU %, RSS MB)."""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Any

import psutil


def _telemetry_has_value(key: str, metadata: dict[str, Any]) -> bool:
    if key not in metadata:
        return False
    value = metadata.get(key)
    if value is None or value == "":
        return False
    return True


def collect_process_telemetry(
    process: psutil.Process | None = None,
    *,
    peak_cpu: float | None = None,
    peak_rss: int | None = None,
) -> dict[str, float]:
    rss = int(peak_rss or 0)
    cpu = float(peak_cpu or 0.0)
    proc = process
    if proc is not None:
        try:
            rss = max(rss, int(proc.memory_info().rss))
            cpu_sample = proc.cpu_percent(interval=None)
            if cpu_sample is not None:
                cpu = max(cpu, float(cpu_sample))
        except Exception:
            pass
    result: dict[str, float] = {}
    if rss > 0:
        usage_mem_mb = round(rss / (1024 * 1024), 2)
        result["usage_memoria"] = usage_mem_mb
        result["usage_mem_mb"] = usage_mem_mb
    result["usage_cpu"] = round(cpu, 2)
    return result


class TelemetryTracker:
    """Tracks peak CPU and RSS for a run across parent and child processes."""

    def __init__(self) -> None:
        self.peak_cpu = 0.0
        self.peak_rss = 0
        self._parent = psutil.Process()
        try:
            self._parent.cpu_percent()
        except Exception:
            pass
        self.sample()

    def sample(self, process: psutil.Process | None = None) -> None:
        targets = [self._parent]
        if process is not None:
            targets.append(process)
        for proc in targets:
            try:
                self.peak_rss = max(self.peak_rss, int(proc.memory_info().rss))
                cpu_sample = proc.cpu_percent(interval=None)
                if cpu_sample is not None:
                    self.peak_cpu = max(self.peak_cpu, float(cpu_sample))
            except Exception:
                continue

    def as_metadata(self) -> dict[str, float]:
        return collect_process_telemetry(
            self._parent,
            peak_cpu=self.peak_cpu,
            peak_rss=self.peak_rss,
        )


def merge_run_metadata(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
    *,
    telemetry: dict[str, float] | None = None,
) -> dict[str, Any]:
    merged = {**(existing or {}), **(incoming or {})}
    tel = telemetry or {}
    for key in ("usage_cpu", "usage_memoria", "usage_mem_mb"):
        if key not in tel:
            continue
        tel_value = tel.get(key)
        if tel_value is None:
            continue
        if not _telemetry_has_value(key, merged):
            merged[key] = tel_value
            continue
        try:
            merged[key] = max(float(merged[key]), float(tel_value))
        except (TypeError, ValueError):
            merged[key] = tel_value
    return merged


def enrich_finish_metadata(
    metadata: dict[str, Any] | None,
    *,
    tracker: TelemetryTracker | None = None,
    child_process: psutil.Process | None = None,
) -> dict[str, Any]:
    base = dict(metadata or {})
    if tracker is not None:
        tracker.sample(child_process)
        telemetry = tracker.as_metadata()
    elif child_process is not None:
        telemetry = collect_process_telemetry(child_process)
    else:
        telemetry = collect_process_telemetry()
    return merge_run_metadata(base, None, telemetry=telemetry)


def run_subprocess_with_telemetry(
    command: list[str],
    *,
    cwd: str | None,
    tracker: TelemetryTracker,
    env: dict[str, str] | None = None,
    text: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess while sampling peak CPU/RSS into ``tracker``."""
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=text,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
    )
    child_ps: psutil.Process | None = None
    try:
        child_ps = psutil.Process(proc.pid)
        child_ps.cpu_percent()
    except Exception:
        child_ps = None

    def _sample_loop() -> None:
        while proc.poll() is None:
            tracker.sample(child_ps)
            time.sleep(0.15)

    sampler = threading.Thread(target=_sample_loop, daemon=True)
    sampler.start()
    stdout, stderr = proc.communicate()
    sampler.join(timeout=1.0)
    tracker.sample(child_ps)
    return subprocess.CompletedProcess(
        args=command,
        returncode=int(proc.returncode or 0),
        stdout=stdout or "",
        stderr=stderr or "",
    )
