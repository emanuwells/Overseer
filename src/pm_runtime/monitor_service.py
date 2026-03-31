from __future__ import annotations

from datetime import timedelta
from typing import Any

from .repository import (
    MonitorRepository,
    decode_cursor,
    encode_cursor,
    group_runs_by_pipeline,
    now_utc,
    percentile_95,
    to_run_summary,
    compute_pipeline_cadence_hours,
)


class MonitorService:
    def __init__(self, repo: MonitorRepository | None = None) -> None:
        self.repo = repo or MonitorRepository()

    def overview(self, window: str = "24h") -> dict[str, Any]:
        runs = self.repo.load_runs()
        grouped = group_runs_by_pipeline(runs)

        now = now_utc()
        window_delta = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}.get(window, timedelta(hours=24))
        filtered = [r for r in runs if r.start_date and now - r.start_date <= window_delta]
        if not filtered:
            filtered = runs[:]

        total = len(filtered)
        ok = sum(1 for r in filtered if r.status == "OK")
        nok = sum(1 for r in filtered if r.status == "NOK")
        execs = [r.exec_time for r in filtered]
        cpus = [r.usage_cpu for r in filtered]
        mems = [r.usage_memoria for r in filtered]

        at_risk = 0
        stale = 0
        regressions = 0
        failed = 0
        alert_immediate: list[dict[str, Any]] = []
        incidents: list[dict[str, Any]] = []

        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        for pipeline_id, pipeline_runs in grouped.items():
            latest = pipeline_runs[0]
            latest_dt = latest.start_date
            cadence_h = compute_pipeline_cadence_hours(pipeline_runs)
            stale_threshold_h = max((cadence_h or 24) * 1.75, 24)
            is_stale = latest_dt is None or (now - latest_dt).total_seconds() / 3600 > stale_threshold_h

            current = [r for r in pipeline_runs if r.start_date and r.start_date >= seven_days_ago]
            previous = [r for r in pipeline_runs if r.start_date and fourteen_days_ago <= r.start_date < seven_days_ago]
            curr_rate = (sum(1 for r in current if r.status == "NOK") / len(current)) if current else 0
            prev_rate = (sum(1 for r in previous if r.status == "NOK") / len(previous)) if previous else 0
            delta = curr_rate - prev_rate

            is_failed = latest.status == "NOK"
            if is_failed:
                failed += 1
                alert_immediate.append(
                    {
                        "pipelineId": pipeline_id,
                        "name": latest.script_name,
                        "runId": latest.id,
                        "when": latest_dt.isoformat().replace("+00:00", "Z") if latest_dt else None,
                        "reason": "ultima run NOK",
                    }
                )

            if is_stale:
                stale += 1
                incidents.append(
                    {
                        "pipelineId": pipeline_id,
                        "name": latest.script_name,
                        "runId": latest.id,
                        "when": latest_dt.isoformat().replace("+00:00", "Z") if latest_dt else None,
                        "reason": "pipeline sem run recente",
                    }
                )

            if len(current) >= 2 and delta > 0.1:
                regressions += 1
                incidents.append(
                    {
                        "pipelineId": pipeline_id,
                        "name": latest.script_name,
                        "runId": latest.id,
                        "when": latest_dt.isoformat().replace("+00:00", "Z") if latest_dt else None,
                        "reason": f"regressao +{delta * 100:.1f}pp",
                    }
                )

            risky = is_failed or is_stale or curr_rate >= 0.2 or (len(current) >= 2 and delta > 0.1)
            if risky and not is_failed:
                at_risk += 1

        runs24h = [r for r in runs if r.start_date and (now - r.start_date) <= timedelta(hours=24)]
        baseline_days = []
        for d in range(1, 8):
            day_start = (now - timedelta(days=d)).date()
            count = sum(1 for r in runs if r.start_date and r.start_date.date() == day_start)
            baseline_days.append(count)
        baseline = sum(baseline_days) / len(baseline_days) if baseline_days else 0.0
        ratio = (len(runs24h) / baseline) if baseline > 0 else 1.0
        volume_status = "good"
        if ratio < 0.35:
            volume_status = "critical"
        elif ratio < 0.6:
            volume_status = "warning"

        return {
            "generatedAt": now.isoformat().replace("+00:00", "Z"),
            "globalKpis": {
                "totalRuns": total,
                "okRuns": ok,
                "nokRuns": nok,
                "successRate": round((ok / total) * 100, 2) if total else 100.0,
                "avgExecTime": round((sum(execs) / len(execs)) if execs else 0.0, 2),
                "avgCpu": round((sum(cpus) / len(cpus)) if cpus else 0.0, 2),
                "avgMem": round((sum(mems) / len(mems)) if mems else 0.0, 2),
                "p95ExecTime": round(percentile_95(execs), 2),
            },
            "operationalSignals": {
                "pipelineCount": len(grouped),
                "atRisk": at_risk,
                "stale": stale,
                "regressions": regressions,
                "failed": failed,
                "volume": {
                    "status": volume_status,
                    "ratio": round(ratio, 3),
                    "runs24h": len(runs24h),
                    "baseline": round(baseline, 2),
                },
            },
            "topAlerts": {
                "immediate": alert_immediate[:5],
                "incidents": incidents[:10],
            },
        }

    def pipelines(self, q: str = "", status: str = "", risk: str = "", stale: str = "", cursor: str | None = None, limit: int = 25) -> dict[str, Any]:
        runs = self.repo.load_runs()
        grouped = group_runs_by_pipeline(runs)
        now = now_utc()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        items = []
        for pipeline_id, pipeline_runs in grouped.items():
            latest = pipeline_runs[0]
            current = [r for r in pipeline_runs if r.start_date and r.start_date >= seven_days_ago]
            previous = [r for r in pipeline_runs if r.start_date and fourteen_days_ago <= r.start_date < seven_days_ago]

            curr_total = len(current)
            curr_nok = sum(1 for r in current if r.status == "NOK")
            prev_total = len(previous)
            prev_nok = sum(1 for r in previous if r.status == "NOK")
            curr_rate = (curr_nok / curr_total) if curr_total else 0.0
            prev_rate = (prev_nok / prev_total) if prev_total else 0.0
            regression_delta = curr_rate - prev_rate

            cadence_h = compute_pipeline_cadence_hours(pipeline_runs)
            stale_threshold_h = max((cadence_h or 24) * 1.75, 24)
            stale_hours = None
            if latest.start_date:
                stale_hours = int((now - latest.start_date).total_seconds() // 3600)
            is_stale = stale_hours is None or stale_hours > stale_threshold_h

            risk_score = 0
            if latest.status == "NOK":
                risk_score += 45
            if is_stale:
                risk_score += 25
            if curr_rate >= 0.2:
                risk_score += 20
            if curr_total >= 2 and regression_delta > 0.1:
                risk_score += 10
            risk_score = max(0, min(100, risk_score))
            if risk_score >= 80:
                risk_level = "critical"
            elif risk_score >= 55:
                risk_level = "high"
            elif risk_score >= 30:
                risk_level = "medium"
            else:
                risk_level = "low"

            item = {
                "pipelineId": pipeline_id,
                "name": latest.script_name,
                "owner": latest.owner,
                "criticality": latest.criticality,
                "lastRun": latest.start_date.isoformat().replace("+00:00", "Z") if latest.start_date else None,
                "lastStatus": latest.status,
                "successRate7d": round((1 - curr_rate) * 100, 2) if curr_total else 100.0,
                "regressionDelta": round(regression_delta * 100, 2),
                "staleHours": stale_hours,
                "riskScore": risk_score,
                "riskLevel": risk_level,
            }
            items.append(item)

        if q:
            query = q.lower().strip()
            items = [i for i in items if query in i["name"].lower() or query in i["pipelineId"].lower() or query in i["owner"].lower()]
        if status:
            items = [i for i in items if i["lastStatus"].lower() == status.lower()]
        if risk:
            items = [i for i in items if i["riskLevel"] == risk.lower()]
        if stale.lower() == "true":
            items = [i for i in items if (i["staleHours"] or 0) >= 24]

        items.sort(key=lambda x: (x["riskScore"], x["lastRun"] or ""), reverse=True)

        total = len(items)
        offset = decode_cursor(cursor)
        limit = max(1, min(limit, 200))
        paged = items[offset : offset + limit]
        next_cursor = encode_cursor(offset + limit, total)

        return {"items": paged, "nextCursor": next_cursor, "total": total}

    def pipeline_runs(self, pipeline_id: str, cursor: str | None = None, limit: int = 50) -> dict[str, Any]:
        runs = [r for r in self.repo.load_runs() if r.pipeline_id == pipeline_id]
        runs.sort(key=lambda r: r.start_date or now_utc(), reverse=True)
        total = len(runs)
        offset = decode_cursor(cursor)
        limit = max(1, min(limit, 200))
        page = runs[offset : offset + limit]
        next_cursor = encode_cursor(offset + limit, total)
        return {"items": [to_run_summary(r) for r in page], "nextCursor": next_cursor, "total": total}

    def runs(self, q: str = "", status: str = "", pipeline_id: str = "", cursor: str | None = None, limit: int = 50) -> dict[str, Any]:
        runs = self.repo.load_runs()
        if q:
            query = q.lower().strip()
            runs = [r for r in runs if query in r.script_name.lower() or query in r.hostname.lower() or query in str(r.id)]
        if status:
            runs = [r for r in runs if r.status.lower() == status.lower()]
        if pipeline_id:
            runs = [r for r in runs if r.pipeline_id == pipeline_id]

        runs.sort(key=lambda r: r.start_date or now_utc(), reverse=True)
        total = len(runs)
        offset = decode_cursor(cursor)
        limit = max(1, min(limit, 200))
        page = runs[offset : offset + limit]
        next_cursor = encode_cursor(offset + limit, total)
        return {"items": [to_run_summary(r) for r in page], "nextCursor": next_cursor, "total": total}

    def run_detail(self, run_id: int) -> dict[str, Any] | None:
        run = self.repo.load_run_by_id(run_id)
        if run is None:
            return None
        detail = self.repo.load_error_detail(run_id)
        return {
            "run": to_run_summary(run),
            "errorMessage": run.error_message,
            "log": detail,
        }

    def lineage(self, pipeline_id: str) -> dict[str, Any]:
        runs = self.repo.load_runs()
        target = next((r for r in runs if r.pipeline_id == pipeline_id), None)
        target_status = target.status if target else "UNKNOWN"
        return {
            "pipelineId": pipeline_id,
            "nodes": [
                {"pipelineId": pipeline_id, "name": pipeline_id, "status": target_status},
            ],
            "edges": [],
        }

    def watermark(self, sla_minutes: int) -> dict[str, Any]:
        runs = self.repo.load_runs()
        now = now_utc()
        latest = next((r for r in runs if r.start_date), None)
        if latest and latest.start_date:
            stale_minutes = int((now - latest.start_date).total_seconds() // 60)
            last_ingested = latest.start_date.isoformat().replace("+00:00", "Z")
        else:
            stale_minutes = None
            last_ingested = None
        return {
            "lastIngestedAt": last_ingested,
            "now": now.isoformat().replace("+00:00", "Z"),
            "staleMinutes": stale_minutes,
            "slaBreached": stale_minutes is not None and stale_minutes > sla_minutes,
        }

