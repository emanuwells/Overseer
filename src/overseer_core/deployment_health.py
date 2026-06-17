"""Schedule-aware deployment health signals for read API consumers."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from . import store
from .helpers import safe_metadata

_MANUAL_SCHEDULES = frozenset({"manual", "paused", ""})


def catalog_schedule(cat: dict[str, Any]) -> str:
    return str(cat.get("schedule") or "manual").strip()


def catalog_prev_schedule(cat: dict[str, Any]) -> str | None:
    if cat.get("prev_schedule"):
        return str(cat["prev_schedule"])
    meta = safe_metadata(cat)
    if meta.get("prev_schedule"):
        return str(meta["prev_schedule"])
    return None


def is_manual_schedule(schedule: str) -> bool:
    return str(schedule or "manual").strip().lower() in _MANUAL_SCHEDULES


def schedule_stale_threshold_hours(schedule: str) -> float | None:
    normalized = str(schedule or "manual").strip().lower()
    if is_manual_schedule(normalized):
        return None

    parts = normalized.split()
    if len(parts) != 5:
        return 168.0

    minute, hour, dom, month, dow = parts

    if minute.startswith("*/"):
        try:
            every_minutes = max(1, int(minute[2:]))
            return max(1.0, (every_minutes * 3) / 60.0)
        except ValueError:
            pass

    if "," in minute and hour in {"*", "0-23"}:
        return 3.0

    if hour == "*" and minute.isdigit():
        return 3.0

    if hour.startswith("*/"):
        try:
            every_hours = max(1, int(hour[2:]))
            return every_hours * 3.0
        except ValueError:
            pass

    if dow in {"1-5", "mon-fri"} and dom == "*":
        return 24.0 * 4

    if dow != "*" and dom == "*":
        return 24.0 * 8

    if dom != "*" and dow == "*":
        return 24.0 * 35

    if dom == "*" and month == "*" and dow == "*":
        return 24.0

    return 168.0


def hours_since(value: Any) -> float | None:
    started = store.parse_dt(value)
    if not started:
        return None
    return max(0.0, (store.utcnow() - started).total_seconds() / 3600.0)


def _status_bucket(status: str | None) -> str:
    raw = store.normalize_status(status)
    if raw == "ok":
        return "ok"
    if raw == "warning":
        return "warning"
    if raw == "running":
        return "running"
    return "failed"


def is_failed(status: str | None) -> bool:
    return _status_bucket(status) == "failed"


def is_warning(status: str | None) -> bool:
    return _status_bucket(status) == "warning"


def is_ok(status: str | None) -> bool:
    return _status_bucket(status) == "ok"


def is_stale_deployment(items: list[dict[str, Any]], cat: dict[str, Any]) -> bool:
    schedule = catalog_schedule(cat)
    threshold = schedule_stale_threshold_hours(schedule)
    if threshold is None:
        return False

    if not items:
        last_started = cat.get("last_started_at")
        if not last_started:
            return True
        hours = hours_since(last_started)
        return hours is not None and hours > threshold

    hours = hours_since(items[0].get("started_at"))
    if hours is None:
        return True
    return hours > threshold


def deployment_signal_counts(
    items: list[dict[str, Any]],
    cat: dict[str, Any] | None = None,
) -> tuple[bool, bool, bool]:
    catalog_row = cat or {}
    stale = is_stale_deployment(items, catalog_row)
    if not items:
        return stale, False, stale
    latest = items[0]
    recent = items[:7]
    fail_rate = sum(1 for row in recent if is_failed(row.get("status"))) / max(1, len(recent))
    failed = is_failed(latest.get("status"))
    regression = fail_rate > 0.2
    at_risk = failed or stale or regression
    return stale, regression, at_risk


def risk_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def risk_score_for_deployment(
    latest: dict[str, Any] | None,
    recent: list[dict[str, Any]],
    *,
    stale_hours: float | None,
    stale_threshold: float | None,
) -> int:
    stale_penalty = 0
    if stale_threshold is not None:
        if stale_hours is None or stale_hours > stale_threshold:
            stale_penalty = 25
    if latest is None:
        return stale_penalty
    failed_recent = sum(1 for row in recent if is_failed(row.get("status")))
    return min(
        100,
        max(
            0,
            (45 if is_failed(latest.get("status")) else 20 if is_warning(latest.get("status")) else 0)
            + stale_penalty
            + (20 if failed_recent / max(1, len(recent)) > 0.2 else 0),
        ),
    )


def metadata_cpu(metadata: dict[str, Any]) -> float:
    for key in ("usage_cpu", "cpu"):
        val = metadata.get(key)
        if val is not None and str(val).strip() != "":
            return float(val)
    return 0.0


def metadata_memory(metadata: dict[str, Any]) -> float:
    for key in ("usage_memoria", "memory_mb", "usage_mem_mb"):
        val = metadata.get(key)
        if val is not None and str(val).strip() != "":
            return float(val)
    return 0.0


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * quantile)))
    return float(ordered[index])


def run_resource_metrics(runs: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    durations: list[float] = []
    cpus: list[float] = []
    mems: list[float] = []
    for row in runs:
        if row.get("duration_sec") is not None:
            durations.append(float(row["duration_sec"]))
        metadata = safe_metadata(row)
        cpu = min(metadata_cpu(metadata), 100.0)
        memory = metadata_memory(metadata)
        if memory > 0:
            mems.append(memory)
            if cpu > 0:
                cpus.append(cpu)
        elif cpu > 0:
            cpus.append(cpu)
    avg_exec = round(sum(durations) / len(durations), 3) if durations else 0.0
    p95_exec = round(_percentile(durations, 0.95), 3) if durations else 0.0
    avg_cpu = round(min(sum(cpus) / len(cpus), 100.0), 2) if cpus else 0.0
    avg_mem = round(sum(mems) / len(mems), 2) if mems else 0.0
    return avg_exec, p95_exec, avg_cpu, avg_mem


def first_run_label(runs: list[dict[str, Any]]) -> str | None:
    oldest: datetime | None = None
    for row in runs:
        started = store.parse_dt(row.get("started_at"))
        if started and (oldest is None or started < oldest):
            oldest = started
    return oldest.strftime("%Y-%m-%d") if oldest else None


def compute_volume(runs: list[dict[str, Any]]) -> dict[str, Any]:
    runs_24h = 0
    prev_week = 0
    for row in runs:
        hours = hours_since(row.get("started_at"))
        if hours is None:
            continue
        if hours <= 24:
            runs_24h += 1
        elif hours <= 24 * 8:
            prev_week += 1
    baseline = round(prev_week / 7.0, 2) if prev_week else 0.0
    if baseline <= 0:
        return {"status": "good", "ratio": 1.0, "runs24h": runs_24h, "baseline": 0.0}
    ratio = round(runs_24h / baseline, 3)
    status = "good"
    if ratio < 0.5 or ratio > 2.0:
        status = "critical"
    elif ratio < 0.7 or ratio > 1.5:
        status = "warn"
    return {"status": status, "ratio": ratio, "runs24h": runs_24h, "baseline": baseline}


def group_runs_by_deployment(runs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        key = store.deployment_key_from_row(run)
        if key:
            grouped[key].append(run)
    for items in grouped.values():
        items.sort(key=lambda row: str(row.get("started_at") or ""), reverse=True)
    return grouped


def enrich_deployment(
    item: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    recent = runs[:7]
    latest = runs[0] if runs else None
    schedule = catalog_schedule(item)
    stale_threshold = schedule_stale_threshold_hours(schedule)
    stale_hours = hours_since((latest or {}).get("started_at") or item.get("last_started_at"))
    is_stale, is_regression, is_at_risk = deployment_signal_counts(runs, item)
    risk_score = risk_score_for_deployment(
        latest,
        recent,
        stale_hours=stale_hours,
        stale_threshold=stale_threshold,
    )
    failed_recent = sum(1 for row in recent if is_failed(row.get("status")))
    success_rate_7d = ((len(recent) - failed_recent) / len(recent) * 100) if recent else 100.0
    item = dict(item)
    item["deployment_key"] = store.deployment_key_from_row(item)
    item["prev_schedule"] = catalog_prev_schedule(item)
    item["is_stale"] = is_stale
    item["is_regression"] = is_regression
    item["is_at_risk"] = is_at_risk
    item["risk_score"] = risk_score
    item["risk_level"] = risk_level(risk_score)
    item["stale_hours"] = int(stale_hours) if stale_hours is not None else None
    item["success_rate_7d"] = round(success_rate_7d, 2)
    return item


def run_row_id(run: dict[str, Any] | str, index: int = 0) -> int:
    if isinstance(run, dict):
        local_id = run.get("run_local_id")
        if local_id is not None and str(local_id).strip() != "":
            return int(local_id)
        run_id = str(run.get("run_id") or "")
    else:
        run_id = str(run or "")
    return abs(hash(f"{run_id}:{index}")) % 2_000_000_000 or index + 1


def build_operational_summary(
    runs: list[dict[str, Any]],
    deployments: list[dict[str, Any]],
    *,
    total_runs: int | None = None,
    runs_7d: list[dict[str, Any]] | None = None,
    failed_7d: int | None = None,
) -> dict[str, Any]:
    grouped = group_runs_by_deployment(runs)
    at_risk = stale = regressions = 0
    for item in deployments:
        key = store.deployment_key_from_row(item)
        runs_for = grouped.get(key, [])
        is_stale, is_regression, is_at_risk = deployment_signal_counts(runs_for, item)
        if is_stale:
            stale += 1
        if is_regression:
            regressions += 1
        if is_at_risk:
            at_risk += 1

    window_runs = runs_7d if runs_7d is not None else runs
    total = int(total_runs if total_runs is not None else len(runs))
    sample_total = len(runs)
    ok = sum(1 for row in runs if is_ok(row.get("status")))
    failed = sum(1 for row in runs if is_failed(row.get("status")))
    warning = sum(1 for row in runs if is_warning(row.get("status")))
    window_ok = sum(1 for row in window_runs if is_ok(row.get("status")))
    window_total = len(window_runs)
    window_failed = (
        int(failed_7d)
        if failed_7d is not None
        else sum(1 for row in window_runs if is_failed(row.get("status")))
    )
    avg_exec, p95_exec, avg_cpu, avg_mem = run_resource_metrics(window_runs)
    volume = compute_volume(runs)
    return {
        "pipelines": len(deployments),
        "runs": total,
        "total_runs": total,
        "running": sum(1 for row in runs if _status_bucket(row.get("status")) == "running"),
        "ok": ok,
        "failed": failed,
        "failed_7d": window_failed,
        "warning": warning,
        "success_rate": round((ok / sample_total) * 100, 2) if sample_total else 100.0,
        "success_rate_7d": round((window_ok / window_total) * 100, 2) if window_total else 100.0,
        "metrics_period_label": "7d",
        "runs_24h": volume.get("runs24h", 0),
        "avg_exec_time": avg_exec,
        "p95_exec_time": p95_exec,
        "avg_cpu": avg_cpu,
        "avg_mem": avg_mem,
        "at_risk": at_risk,
        "stale": stale,
        "regressions": regressions,
        "first_run_label": first_run_label(runs),
        "volume": volume,
    }
