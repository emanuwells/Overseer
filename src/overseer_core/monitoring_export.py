"""Export v5 overseer_* data into legacy /v1/monitoring payloads for MAIATRON/WELLS."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from . import store

ROW_FIELDS: list[str] = [
    "id",
    "pipelineId",
    "scriptName",
    "startDate",
    "endDate",
    "execTime",
    "usageCPU",
    "usageMemoria",
    "status",
    "logMessage",
    "errorMessage",
    "hostname",
    "OS",
    "regDate",
    "owner",
    "criticality",
    "osName",
    "osRelease",
    "osPlatform",
    "triggerType",
    "runId",
    "requestedBy",
    "runnerHost",
    "attemptId",
    "requestedBySSO",
]

_STALE_HOURS = 24


def _iso_now() -> str:
    return store.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_dt(value: Any) -> datetime | None:
    return store.parse_dt(value)


def _status_bucket(status: str | None) -> str:
    raw = store.normalize_status(status)
    if raw == "ok":
        return "ok"
    if raw == "warning":
        return "warning"
    if raw == "running":
        return "running"
    return "failed"


def _is_failed(status: str | None) -> bool:
    return _status_bucket(status) == "failed"


def _is_warning(status: str | None) -> bool:
    return _status_bucket(status) == "warning"


def _is_ok(status: str | None) -> bool:
    return _status_bucket(status) == "ok"


def _hours_since(value: Any) -> float | None:
    started = _parse_dt(value)
    if not started:
        return None
    return max(0.0, (store.utcnow() - started).total_seconds() / 3600.0)


def _pipeline_lookup(pipelines: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in pipelines:
        key = store.deployment_key_from_row(row)
        if key:
            lookup[key] = row
        pid = store.logical_pipeline_id(str(row.get("pipeline_id") or ""))
        if pid and pid not in lookup:
            lookup[pid] = row
    return lookup


def _inactive_pipeline_ids(pipelines: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for row in pipelines:
        if row.get("active") is False:
            pid = store.logical_pipeline_id(str(row.get("pipeline_id") or ""))
            if pid:
                ids.add(pid)
    return ids


def _filter_runs_for_export(
    runs: list[dict[str, Any]],
    pipelines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    inactive = _inactive_pipeline_ids(pipelines)
    if not inactive:
        return runs
    return [
        run
        for run in runs
        if store.logical_pipeline_id(str(run.get("pipeline_id") or "")) not in inactive
        and not store.is_excluded_pipeline(str(run.get("pipeline_id") or ""))
    ]


def _filter_pipelines_for_export(pipelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in pipelines
        if row.get("active", True) and not store.is_excluded_pipeline(str(row.get("pipeline_id") or ""))
    ]


def _run_row_id(run_id: str, index: int) -> int:
  # Stable positive int for legacy UI (modulo keeps SQLite-scale ids).
    return abs(hash(f"{run_id}:{index}")) % 2_000_000_000 or index + 1


def _run_to_values(
    run: dict[str, Any],
    *,
    row_id: int,
    catalog: dict[str, dict[str, Any]],
) -> list[Any]:
    pipeline_id = store.logical_pipeline_id(str(run.get("pipeline_id") or ""))
    deployment = store.deployment_key_from_row(run)
    cat = catalog.get(deployment) or catalog.get(pipeline_id) or {}
    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    host_id = str(run.get("host_id") or "")
    os_label = str(metadata.get("os") or host_id or run.get("hostname") or "unknown")
    return [
        row_id,
        pipeline_id,
        str(run.get("pipeline_name") or pipeline_id),
        run.get("started_at"),
        run.get("ended_at"),
        run.get("duration_sec"),
        metadata.get("usage_cpu") or metadata.get("cpu") or 0,
        metadata.get("usage_memoria") or metadata.get("memory_mb") or 0,
        _status_bucket(run.get("status")),
        None,
        run.get("error_message"),
        run.get("hostname") or host_id or None,
        os_label,
        run.get("created_at"),
        cat.get("owner") or "unknown",
        cat.get("criticality") or "medium",
        metadata.get("os_name") or os_label,
        metadata.get("os_release"),
        metadata.get("os_platform"),
        run.get("trigger_type") or "manual",
        run.get("run_id"),
        run.get("requested_by"),
        run.get("runner_host") or host_id or "any",
        metadata.get("attempt_id"),
        run.get("requested_by"),
    ]


def _rows_and_index(runs: list[dict[str, Any]], pipelines: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]], dict[str, int]]:
    catalog = _pipeline_lookup(pipelines)
    fields = ROW_FIELDS
    rows: list[list[Any]] = []
    id_index: dict[str, int] = {}
    for index, run in enumerate(runs):
        row_id = _run_row_id(str(run.get("run_id") or ""), index)
        id_index[str(row_id)] = index
        id_index[str(run.get("run_id") or "")] = index
        rows.append(_run_to_values(run, row_id=row_id, catalog=catalog))
    return fields, rows, id_index


def _group_runs_by_deployment(runs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        key = store.deployment_key_from_row(run)
        if key:
            grouped[key].append(run)
    for items in grouped.values():
        items.sort(key=lambda row: str(row.get("started_at") or ""), reverse=True)
    return grouped


def _split_deployment_key(key: str) -> tuple[str, str]:
    logical, _, host = str(key or "").partition("::")
    return logical, host


def _lineage_export_key(deployment: str) -> str:
    pipeline_id, host_id = _split_deployment_key(deployment)
    if not host_id or host_id.lower() in {"local", "localhost"}:
        return pipeline_id
    return f"{pipeline_id}@{host_id}"


def _build_summary(runs: list[dict[str, Any]], pipelines: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    ok = sum(1 for row in runs if _is_ok(row.get("status")))
    failed = sum(1 for row in runs if _is_failed(row.get("status")))
    warning = sum(1 for row in runs if _is_warning(row.get("status")))
    durations = [float(row["duration_sec"]) for row in runs if row.get("duration_sec") is not None]
    avg_exec = round(sum(durations) / len(durations), 3) if durations else 0.0
    grouped = _group_runs_by_deployment(runs)
    at_risk = stale = regressions = 0
    for items in grouped.values():
        if not items:
            continue
        latest = items[0]
        stale_hours = _hours_since(latest.get("started_at"))
        is_stale = stale_hours is None or stale_hours > _STALE_HOURS
        is_failed = _is_failed(latest.get("status"))
        recent = items[:7]
        fail_rate = sum(1 for row in recent if _is_failed(row.get("status"))) / max(1, len(recent))
        if is_stale:
            stale += 1
        if fail_rate > 0.2:
            regressions += 1
        if is_failed or is_stale or fail_rate > 0.2:
            at_risk += 1
    return {
        "total_runs": total,
        "totalRuns": total,
        "ok_runs": ok,
        "ok": ok,
        "failed_runs": failed,
        "nok_runs": failed,
        "failed": failed,
        "warning_runs": warning,
        "warning": warning,
        "success_rate": round((ok / total) * 100, 2) if total else 100.0,
        "avg_exec_time": avg_exec,
        "pipeline_count": len(grouped) or len(pipelines),
        "at_risk": at_risk,
        "stale": stale,
        "regressions": regressions,
    }


def _build_overview(runs: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    grouped = _group_runs_by_deployment(runs)
    failed_count = sum(1 for items in grouped.values() if items and _is_failed(items[0].get("status")))
    immediate = []
    incidents = []
    for items in grouped.values():
        if not items:
            continue
        latest = items[0]
        row_id = _run_row_id(str(latest.get("run_id") or ""), 0)
        if _is_failed(latest.get("status")):
            immediate.append(
                {
                    "pipelineId": store.logical_pipeline_id(str(latest.get("pipeline_id") or "")),
                    "name": latest.get("pipeline_name"),
                    "runId": row_id,
                    "run_id_pipeline": f"{latest.get('pipeline_id')}#{row_id}",
                    "reason": "última run FAILED",
                    "when": latest.get("started_at"),
                }
            )
            incidents.append(
                {
                    "pipelineId": latest.get("pipeline_id"),
                    "name": latest.get("pipeline_name"),
                    "runId": row_id,
                    "run_id_pipeline": f"{latest.get('pipeline_id')}#{row_id}",
                    "reason": "falha",
                    "when": latest.get("started_at"),
                }
            )
        stale_hours = _hours_since(latest.get("started_at"))
        if stale_hours is None or stale_hours > _STALE_HOURS:
            incidents.append(
                {
                    "pipelineId": latest.get("pipeline_id"),
                    "name": latest.get("pipeline_name"),
                    "runId": row_id,
                    "run_id_pipeline": f"{latest.get('pipeline_id')}#{row_id}",
                    "reason": "stale",
                    "when": latest.get("started_at"),
                }
            )
    runs_24h = sum(1 for row in runs if (_hours_since(row.get("started_at")) or 999) <= 24)
    return {
        "generatedAt": _iso_now(),
        "globalKpis": {
            "totalRuns": summary["total_runs"],
            "okRuns": summary["ok_runs"],
            "warningRuns": summary["warning_runs"],
            "failedRuns": summary["failed_runs"],
            "nokRuns": summary["nok_runs"],
            "successRate": summary["success_rate"],
            "avgExecTime": summary["avg_exec_time"],
            "avgCpu": 0,
            "avgMem": 0,
            "p95ExecTime": 0,
        },
        "operationalSignals": {
            "pipelineCount": summary["pipeline_count"],
            "atRisk": summary["at_risk"],
            "stale": summary["stale"],
            "regressions": summary["regressions"],
            "failed": failed_count,
            "warnings": summary["warning_runs"],
            "volume": {
                "status": "good",
                "ratio": 1,
                "runs24h": runs_24h,
                "baseline": 0,
            },
        },
        "topAlerts": {
            "immediate": immediate[:5],
            "incidents": incidents[:10],
        },
    }


def _build_pipelines(runs: list[dict[str, Any]], pipelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = _group_runs_by_deployment(runs)
    catalog = _pipeline_lookup(pipelines)
    items: list[dict[str, Any]] = []
    for deployment, items_runs in grouped.items():
        pipeline_id, host_id = _split_deployment_key(deployment)
        latest = items_runs[0]
        recent = items_runs[:7]
        failed_recent = sum(1 for row in recent if _is_failed(row.get("status")))
        success_rate_7d = ((len(recent) - failed_recent) / len(recent) * 100) if recent else 100.0
        stale_hours = _hours_since(latest.get("started_at"))
        risk_score = min(
            100,
            max(
                0,
                (45 if _is_failed(latest.get("status")) else 20 if _is_warning(latest.get("status")) else 0)
                + (25 if (stale_hours or 0) > _STALE_HOURS else 0)
                + (20 if failed_recent / max(1, len(recent)) > 0.2 else 0),
            ),
        )
        risk_level = "critical" if risk_score >= 80 else "high" if risk_score >= 55 else "medium" if risk_score >= 30 else "low"
        cat = catalog.get(deployment) or catalog.get(pipeline_id) or {}
        items.append(
            {
                "pipelineId": pipeline_id,
                "hostId": host_id or latest.get("host_id"),
                "name": latest.get("pipeline_name") or cat.get("name") or pipeline_id,
                "owner": cat.get("owner") or "unknown",
                "criticality": cat.get("criticality") or "medium",
                "schedule": cat.get("schedule") or "manual",
                "lastRun": latest.get("started_at"),
                "lastStatus": _status_bucket(latest.get("status")),
                "successRate7d": round(success_rate_7d, 2),
                "regressionDelta": 0,
                "staleHours": int(stale_hours) if stale_hours is not None else None,
                "riskScore": risk_score,
                "riskLevel": risk_level,
            }
        )
    items.sort(key=lambda row: (-int(row.get("riskScore") or 0), str(row.get("lastRun") or "")), reverse=False)
    return items


def _build_pipeline_catalog(pipelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "pipeline_id": row.get("pipeline_id"),
            "name": row.get("name"),
            "owner": row.get("owner"),
            "criticality": row.get("criticality"),
            "schedule": row.get("schedule"),
            "runner_host": row.get("runner_host"),
            "active": row.get("active", True),
            "updated_at": row.get("updated_at"),
            "host_id": row.get("host_id"),
        }
        for row in _filter_pipelines_for_export(pipelines)
    ]


def _build_orchestrator_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "runId": run.get("run_id"),
            "pipelineId": store.logical_pipeline_id(str(run.get("pipeline_id") or "")),
            "status": _status_bucket(run.get("status")),
            "source": run.get("trigger_type") or "manual",
            "requestedBy": run.get("requested_by"),
            "requestedBySso": run.get("requested_by"),
            "runnerHost": run.get("runner_host") or run.get("host_id") or "any",
            "pipelineName": run.get("pipeline_name"),
            "startedAt": run.get("started_at"),
            "finishedAt": run.get("ended_at"),
            "createdAt": run.get("created_at"),
            "updatedAt": run.get("updated_at"),
        }
        for run in runs[:500]
    ]


def _build_orchestrator_triggers(triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "triggerId": row.get("trigger_id"),
            "triggerType": row.get("trigger_type"),
            "pipelineId": store.logical_pipeline_id(str(row.get("pipeline_id") or "")),
            "requestedBy": row.get("requested_by"),
            "requestedBySso": row.get("requested_by"),
            "requestedAt": row.get("created_at"),
            "source": "api",
            "runnerHost": row.get("runner_host") or row.get("host_id") or "any",
            "status": row.get("status"),
            "notes": "",
            "createdAt": row.get("created_at"),
        }
        for row in triggers[:500]
    ]


def _module_event_level(status: str | None) -> str:
    bucket = _status_bucket(status)
    if bucket == "failed":
        return "error"
    if bucket == "warning":
        return "warning"
    if bucket == "ok":
        return "ok"
    return "unknown"


def _node_metadata(node: dict[str, Any]) -> dict[str, Any]:
    meta = node.get("metadata")
    return meta if isinstance(meta, dict) else {}


def _script_path_from_node(node: dict[str, Any]) -> str:
    meta = _node_metadata(node)
    command = meta.get("command")
    if isinstance(command, list) and command:
        if len(command) == 1:
            return str(command[0])
        return " ".join(str(part) for part in command[:3])
    module_id = str(node.get("module_id") or node.get("id") or "").strip()
    return module_id or "-"


def _iso_dt(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _build_lineage_blocks(
    runs: list[dict[str, Any]],
    pipelines: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    grouped = _group_runs_by_deployment(runs)
    module_lineage: dict[str, Any] = {}
    pipeline_scripts: dict[str, Any] = {}

    catalog = _pipeline_lookup(pipelines)
    deployments: set[str] = set(grouped.keys())
    for row in pipelines:
        key = store.deployment_key_from_row(row)
        if key and row.get("active", True):
            deployments.add(key)

    for deployment in sorted(deployments):
        pipeline_id, host_id = _split_deployment_key(deployment)
        export_key = _lineage_export_key(deployment)
        cat = catalog.get(deployment) or catalog.get(pipeline_id) or {}
        if cat and cat.get("active") is False and deployment not in grouped:
            continue
        latest_runs = grouped.get(deployment, [])
        latest = latest_runs[0] if latest_runs else None
        latest_run_id = str(latest.get("run_id") or "") if latest else ""
        row_id = _run_row_id(latest_run_id, 0) if latest_run_id else None

        modules_by_id: dict[str, dict[str, Any]] = {}
        if latest_run_id:
            for mod in store.list_modules(run_id=latest_run_id):
                mid = str(mod.get("module_id") or "").strip()
                if mid:
                    modules_by_id[mid] = mod

        dag = store.get_pipeline_dag(pipeline_id, host_id)
        catalog_nodes = list(dag.get("nodes") or [])
        catalog_edges = list(dag.get("edges") or [])
        if not catalog_nodes and modules_by_id:
            catalog_nodes = [
                {"module_id": mid, "label": mid, "metadata": {}}
                for mid in sorted(modules_by_id.keys())
            ]

        export_nodes: list[dict[str, Any]] = []
        scripts: list[dict[str, Any]] = []
        seen_modules: set[str] = set()

        for node in catalog_nodes:
            mid = str(node.get("module_id") or "").strip()
            if not mid:
                continue
            seen_modules.add(mid)
            label = str(node.get("label") or mid)
            meta = _node_metadata(node)
            critical = meta.get("critical", True)
            path = _script_path_from_node(node)
            mod = modules_by_id.get(mid)

            if mod:
                level = _module_event_level(mod.get("status"))
                mod_meta = mod.get("metadata") if isinstance(mod.get("metadata"), dict) else {}
                when = _iso_dt(mod.get("ended_at") or mod.get("started_at"))
                message = mod.get("error_message") or mod_meta.get("message")
                export_nodes.append(
                    {
                        "id": mid,
                        "label": label,
                        "script": path,
                        "status": mod.get("status"),
                        "lastEventLevel": level,
                        "lastSeenAt": when,
                        "lastMessage": message,
                        "critical": critical is not False,
                        "duration_sec": mod.get("duration_sec"),
                    }
                )
                scripts.append(
                    {
                        "path": path,
                        "executed": True,
                        "lastStatus": _status_bucket(mod.get("status")).upper(),
                        "lastEventLevel": level,
                        "lastRunId": row_id,
                        "lastSeenAt": when,
                        "lastMessage": message,
                        "source": "latest_run",
                        "errorCount": 1 if level == "error" else 0,
                        "warningCount": 1 if level == "warning" else 0,
                        "lastErrorAt": when if level == "error" else None,
                        "lastWarningAt": when if level == "warning" else None,
                    }
                )
            else:
                export_nodes.append(
                    {
                        "id": mid,
                        "label": label,
                        "script": path,
                        "status": "inventory",
                        "lastEventLevel": "inventory",
                        "critical": critical is not False,
                    }
                )
                scripts.append(
                    {
                        "path": path,
                        "executed": False,
                        "lastEventLevel": "inventory",
                        "source": "catalog",
                        "errorCount": 0,
                        "warningCount": 0,
                    }
                )

        for mid, mod in sorted(modules_by_id.items()):
            if mid in seen_modules:
                continue
            level = _module_event_level(mod.get("status"))
            when = _iso_dt(mod.get("ended_at") or mod.get("started_at"))
            message = mod.get("error_message")
            export_nodes.append(
                {
                    "id": mid,
                    "label": mid,
                    "script": mid,
                    "status": mod.get("status"),
                    "lastEventLevel": level,
                    "lastSeenAt": when,
                    "lastMessage": message,
                    "critical": True,
                }
            )
            scripts.append(
                {
                    "path": mid,
                    "executed": True,
                    "lastStatus": _status_bucket(mod.get("status")).upper(),
                    "lastEventLevel": level,
                    "lastRunId": row_id,
                    "lastSeenAt": when,
                    "lastMessage": message,
                    "source": "latest_run",
                    "errorCount": 1 if level == "error" else 0,
                    "warningCount": 1 if level == "warning" else 0,
                }
            )

        edges = [
            {
                "source": str(edge.get("from_module_id") or ""),
                "target": str(edge.get("to_module_id") or ""),
            }
            for edge in catalog_edges
            if edge.get("from_module_id") and edge.get("to_module_id")
        ]

        if export_nodes or scripts:
            module_lineage[export_key] = {"nodes": export_nodes, "edges": edges}
            pipeline_scripts[export_key] = scripts

    return module_lineage, pipeline_scripts


def build_details_map(runs: list[dict[str, Any]], pipelines: list[dict[str, Any]]) -> dict[str, Any]:
    fields, rows, _ = _rows_and_index(runs, pipelines)
    details: dict[str, Any] = {}
    for row in rows:
        row_id = str(row[0])
        details[row_id] = {
            "errorMessage": row[fields.index("errorMessage")],
            "logMessage": row[fields.index("logMessage")],
            "run_id_pipeline": f"{row[fields.index('pipelineId')]}#{row_id}",
            "run_local_id": row_id,
        }
    for run in runs:
        run_id = str(run.get("run_id") or "")
        if not run_id:
            continue
        logs = store.list_logs(run_id=run_id, limit=20)
        if not logs:
            continue
        messages = [str(log.get("message") or "") for log in logs if log.get("message")]
        text = "\n".join(messages)[-60000:]
        idx = _run_row_id(run_id, 0)
        key = str(idx)
        entry = details.setdefault(key, {})
        entry["logMessage"] = text or entry.get("logMessage")
        entry["errorMessage"] = entry.get("errorMessage") or run.get("error_message")
        modules = store.list_modules(run_id=run_id)
        entry["modules"] = [
            {
                "module_id": mod.get("module_id"),
                "status": mod.get("status"),
                "duration_sec": mod.get("duration_sec"),
                "error_message": mod.get("error_message"),
            }
            for mod in modules
        ]
    return details


def build_full_payload(*, run_limit: int = 5000) -> dict[str, Any]:
    all_pipelines = store.list_pipelines()
    pipelines = _filter_pipelines_for_export(all_pipelines)
    runs = _filter_runs_for_export(store.list_runs(limit=run_limit), all_pipelines)
    inactive = _inactive_pipeline_ids(all_pipelines)
    triggers = [
        row
        for row in store.list_triggers(limit=500)
        if store.logical_pipeline_id(str(row.get("pipeline_id") or "")) not in inactive
    ]
    fields, rows, _ = _rows_and_index(runs, pipelines)
    summary = _build_summary(runs, pipelines)
    overview = _build_overview(runs, summary)
    module_lineage, pipeline_scripts = _build_lineage_blocks(runs, pipelines)
    return {
        "generated_at": _iso_now(),
        "source": "overseer_v5",
        "fields": fields,
        "rows": rows,
        "summary": summary,
        "overview": overview,
        "pipelines": _build_pipelines(runs, pipelines),
        "pipeline_catalog": _build_pipeline_catalog(pipelines),
        "orchestrator_runs": _build_orchestrator_runs(runs),
        "orchestrator_triggers": _build_orchestrator_triggers(triggers),
        "module_lineage": module_lineage,
        "pipeline_scripts": pipeline_scripts,
    }


def build_ops_fast_payload(*, run_limit: int = 1000) -> dict[str, Any]:
    all_pipelines = store.list_pipelines()
    pipelines = _filter_pipelines_for_export(all_pipelines)
    runs = _filter_runs_for_export(store.list_runs(limit=run_limit), all_pipelines)
    summary = _build_summary(runs, pipelines)
    return {
        "generated_at": _iso_now(),
        "summary": summary,
        "overview": _build_overview(runs, summary),
    }


def build_ops_heavy_payload(*, run_limit: int = 5000) -> dict[str, Any]:
    full = build_full_payload(run_limit=run_limit)
    return {
        "generated_at": full["generated_at"],
        "summary": full["summary"],
        "overview": full["overview"],
        "pipelines": full["pipelines"],
        "orchestrator_runs": full["orchestrator_runs"],
        "orchestrator_triggers": full["orchestrator_triggers"],
        "fields": full["fields"],
        "rows": full["rows"],
        "pipeline_catalog": full["pipeline_catalog"],
        "module_lineage": full.get("module_lineage") or {},
        "pipeline_scripts": full.get("pipeline_scripts") or {},
    }
