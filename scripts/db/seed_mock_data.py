from __future__ import annotations

import argparse
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_payload_from_db import load_pipeline_catalog
from src.pm_runtime.db import get_engine
from src.pm_runtime.settings import settings

PIPELINES = [
    ("webapp_medidata", "Webapp Medidata", "Emanuel", "high"),
    ("microsoft_forms_2_datalake", "Forms to Datalake", "Emanuel", "medium"),
    ("example_pipeline", "Example Pipeline", "dev", "low"),
]


def _table_columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT COLUMN_NAME AS col
              FROM information_schema.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t
            """
        ),
        {"t": table},
    ).mappings().all()
    return {str(r["col"]) for r in rows}


def _ensure_pipeline_catalog(conn) -> None:
    if "pipeline_catalog" not in {t.lower() for t in _list_tables(conn)}:
        return
    cols = _table_columns(conn, "pipeline_catalog")
    for pid, name, owner, crit in PIPELINES:
        row = {
            "pipeline_id": pid,
            "name": name,
            "owner": owner,
            "criticality": crit,
            "schedule": "0 8 * * *" if pid == "webapp_medidata" else "manual",
            "runner_host": "any",
            "active": 1,
        }
        fields = [k for k in row if k in cols]
        if not fields:
            continue
        placeholders = ", ".join(f":{k}" for k in fields)
        col_list = ", ".join(f"`{k}`" for k in fields)
        sql = text(
            f"""
            INSERT INTO pipeline_catalog ({col_list})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
              name = VALUES(name),
              owner = VALUES(owner),
              criticality = VALUES(criticality),
              schedule = VALUES(schedule),
              runner_host = VALUES(runner_host),
              active = VALUES(active),
              updated_at = UTC_TIMESTAMP()
            """
        )
        conn.execute(sql, {k: row[k] for k in fields})


def _list_tables(conn) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT TABLE_NAME AS name FROM information_schema.TABLES
             WHERE TABLE_SCHEMA = DATABASE()
            """
        )
    ).mappings().all()
    return [str(r["name"]) for r in rows]


def seed_runs(conn, *, count: int = 40) -> list[int]:
    table = settings.runs_table
    cols = _table_columns(conn, table)
    now = datetime.now(timezone.utc)
    run_ids: list[int] = []

    for i in range(count):
        pid, name, owner, crit = random.choice(PIPELINES)
        status = "OK" if random.random() > 0.22 else "NOK"
        start = now - timedelta(hours=random.randint(1, 168))
        duration = random.uniform(12, 420)
        end = start + timedelta(seconds=duration)

        row: dict = {
            "scriptName": name,
            "pipelineId": pid,
            "owner": owner,
            "criticality": crit,
            "status": status,
            "startDate": start.replace(tzinfo=None),
            "endDate": end.replace(tzinfo=None),
            "execTime": f"{duration:.2f}",
            "usageCPU": round(random.uniform(5, 85), 2),
            "usageMemoria": round(random.uniform(100, 900), 2),
            "hostname": random.choice(["runner-linux-01", "PTLTP024", "runner-win-02"]),
            "errorMessage": "mock failure" if status == "NOK" else None,
            "logMessage": f"mock run {i} completed",
            "triggerType": random.choice(["schedule", "manual", "trigger_db"]),
            "runId": f"run-{uuid.uuid4().hex[:8]}",
            "attemptId": "1",
        }
        if "osName" in cols:
            row["osName"] = random.choice(["Linux", "Windows"])
        if "regDate" in cols:
            row["regDate"] = start.replace(tzinfo=None)

        fields = [k for k in row if k in cols]
        placeholders = ", ".join(f":{k}" for k in fields)
        col_list = ", ".join(f"`{k}`" for k in fields)
        sql = text(f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})")
        result = conn.execute(sql, {k: row[k] for k in fields})
        run_ids.append(int(result.lastrowid))

    return run_ids


def seed_module_events(conn, run_ids: list[int]) -> None:
    if "pipeline_module_events" not in _list_tables(conn):
        return
    now = datetime.now(timezone.utc)
    for run_id in run_ids[-12:]:
        pid = random.choice(PIPELINES)[0]
        modules = ["config", "extract", "transform", "load"]
        parent = None
        for mod in modules:
            start = now - timedelta(minutes=random.randint(10, 500))
            end = start + timedelta(seconds=random.uniform(2, 60))
            conn.execute(
                text(
                    """
                    INSERT INTO pipeline_module_events
                      (pipelineId, runId, moduleId, parentModuleId, status,
                       startedAt, endedAt, durationSec, hostname, triggerType)
                    VALUES
                      (:pipelineId, :runId, :moduleId, :parentModuleId, :status,
                       :startedAt, :endedAt, :durationSec, :hostname, :triggerType)
                    """
                ),
                {
                    "pipelineId": pid,
                    "runId": str(run_id),
                    "moduleId": mod,
                    "parentModuleId": parent,
                    "status": "OK",
                    "startedAt": start.replace(tzinfo=None),
                    "endedAt": end.replace(tzinfo=None),
                    "durationSec": (end - start).total_seconds(),
                    "hostname": "mock-runner",
                    "triggerType": "schedule",
                },
            )
            parent = mod


def seed_triggers(conn) -> None:
    if "orchestrator_triggers_local" not in _list_tables(conn):
        return
    statuses = ["queued", "consumed", "failed"]
    for i, status in enumerate(statuses * 3):
        pid = PIPELINES[i % len(PIPELINES)][0]
        conn.execute(
            text(
                """
                INSERT INTO orchestrator_triggers_local
                  (trigger_id, trigger_type, pipeline_id, requested_by, requested_at,
                   source, runner_host, status, notes, created_at, updated_at)
                VALUES
                  (:trigger_id, 'run_now', :pipeline_id, 'mock-seed', UTC_TIMESTAMP(),
                   'seed', 'any', :status, 'mock data', UTC_TIMESTAMP(), UTC_TIMESTAMP())
                """
            ),
            {
                "trigger_id": f"mock-trg-{i}-{uuid.uuid4().hex[:6]}",
                "pipeline_id": pid,
                "status": status,
            },
        )


def seed_orch_runs(conn) -> None:
    if "orchestrator_runs_local" not in _list_tables(conn):
        return
    for pid, name, _, _ in PIPELINES:
        conn.execute(
            text(
                """
                INSERT INTO orchestrator_runs_local
                  (pipeline_id, pipeline_name, status, requested_by, trigger_source,
                   runner_host, retries, timeout_sec, started_at, ended_at, created_at, updated_at)
                VALUES
                  (:pipeline_id, :pipeline_name, 'success', 'mock-seed', 'schedule',
                   'any', 2, 3600, UTC_TIMESTAMP(), UTC_TIMESTAMP(), UTC_TIMESTAMP(), UTC_TIMESTAMP())
                """
            ),
            {"pipeline_id": pid, "pipeline_name": name},
        )


def seed_runners(conn) -> None:
    if "overseer_runners" not in _list_tables(conn):
        return
    runners = [
        ("runner-linux-01", "Linux", "6.1", "1.0.0"),
        ("PTLTP024", "Windows", "11", "1.0.0"),
        ("runner-win-02", "Windows", "10", "1.0.0"),
    ]
    for host, os_name, os_rel, ver in runners:
        conn.execute(
            text(
                """
                INSERT INTO overseer_runners
                  (hostname, os_name, os_release, agent_version, last_seen_at, created_at, updated_at)
                VALUES
                  (:hostname, :os_name, :os_release, :agent_version, UTC_TIMESTAMP(), UTC_TIMESTAMP(), UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE
                  last_seen_at = UTC_TIMESTAMP(),
                  agent_version = VALUES(agent_version)
                """
            ),
            {
                "hostname": host,
                "os_name": os_name,
                "os_release": os_rel,
                "agent_version": ver,
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed mock Overseer operational data")
    parser.add_argument("--runs", type=int, default=40, help="Number of pipeline runs to insert")
    args = parser.parse_args()

    engine = get_engine()
    with engine.begin() as conn:
        _ensure_pipeline_catalog(conn)
        run_ids = seed_runs(conn, count=max(5, args.runs))
        seed_module_events(conn, run_ids)
        seed_triggers(conn)
        seed_orch_runs(conn)
        seed_runners(conn)

    catalog = load_pipeline_catalog()
    print(f"Seeded {len(run_ids)} runs into {settings.runs_table}.")
    print(f"Pipeline catalog YAML entries: {len(catalog)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
