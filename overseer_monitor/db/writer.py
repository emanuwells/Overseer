from __future__ import annotations

from typing import Any, Dict, Optional

import pymysql
import pymysql.cursors


_COLUMN_CACHE: dict[tuple[str, str], dict[str, str]] = {}


def _get_table_columns(connection: pymysql.Connection, table_name: str, database: str) -> set[str]:
    return set(_get_table_column_types(connection, table_name, database).keys())


def _get_table_column_types(connection: pymysql.Connection, table_name: str, database: str) -> dict[str, str]:
    key = (database, table_name)
    if key in _COLUMN_CACHE:
        return _COLUMN_CACHE[key]
    query = """
        SELECT COLUMN_NAME, COLUMN_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (database, table_name))
        cols = {row["COLUMN_NAME"]: str(row.get("COLUMN_TYPE") or "") for row in cursor.fetchall()}
    _COLUMN_CACHE[key] = cols
    return cols


def write_log_record(table_name: str, db_params: Dict[str, Any], record: Dict[str, Any]) -> Optional[int]:
    params = {
        "host": db_params.get("host", "localhost"),
        "port": db_params.get("port", 3306),
        "user": db_params.get("user"),
        "password": db_params.get("password"),
        "database": db_params.get("database"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }
    if not params["user"] or not params["password"] or not params["database"]:
        return None

    default_columns = [
        "scriptName",
        "LogDate",
        "startDate",
        "endDate",
        "execTime",
        "usageCPU",
        "usageMemoria",
        "dbconn_wt",
        "dbconn_pt",
        "loading_wt",
        "loading_pt",
        "email_wt",
        "email_pt",
        "status",
        "errorMessage",
        "logMessage",
        "owner",
        "criticality",
        "regDate",
        "modDate",
        "hostname",
        "OS",
        "osName",
        "osRelease",
        "osPlatform",
        "pipelineId",
        "runId",
        "attemptId",
        "triggerType",
    ]

    connection = None
    try:
        connection = pymysql.connect(**params)
        table_columns = _get_table_columns(connection, table_name, params["database"])
        table_types = _get_table_column_types(connection, table_name, params["database"])
        if "OS" in table_columns and not record.get("OS"):
            record["OS"] = record.get("osName") or ""
        status_type = table_types.get("status", "").lower()
        if status_type.startswith("enum(") and "success" in status_type and "failed" in status_type:
            status_map = {"OK": "Success", "NOK": "Failed", "SUCCESS": "Success", "FAILED": "Failed"}
            record["status"] = status_map.get(str(record.get("status") or "").upper(), record.get("status"))
        criticality_type = table_types.get("criticality", "").lower()
        if criticality_type.startswith("enum(") and "low" in criticality_type:
            crit = str(record.get("criticality") or "").strip().lower()
            crit_map = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}
            if crit in crit_map:
                record["criticality"] = crit_map[crit]
        exec_type = table_types.get("execTime", "").lower()
        if exec_type.startswith("time"):
            try:
                total = max(0, int(float(record.get("execTime") or 0)))
                h = total // 3600
                m = (total % 3600) // 60
                s = total % 60
                record["execTime"] = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception:
                pass
        columns = [c for c in default_columns if c in table_columns]
        if not columns:
            return None
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(record.get(c) for c in columns))
            return getattr(cursor, "lastrowid", None)
    finally:
        if connection:
            connection.close()


def write_module_event_record(table_name: str, db_params: Dict[str, Any], record: Dict[str, Any]) -> Optional[int]:
    params = {
        "host": db_params.get("host", "localhost"),
        "port": db_params.get("port", 3306),
        "user": db_params.get("user"),
        "password": db_params.get("password"),
        "database": db_params.get("database"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }
    if not params["user"] or not params["password"] or not params["database"]:
        return None

    default_columns = [
        "pipelineId",
        "runId",
        "moduleId",
        "parentModuleId",
        "status",
        "startedAt",
        "endedAt",
        "durationSec",
        "errorMessage",
        "logMessage",
        "owner",
        "criticality",
        "hostname",
        "OS",
        "triggerType",
        "contextJson",
        "regDate",
    ]

    connection = None
    try:
        connection = pymysql.connect(**params)
        table_columns = _get_table_columns(connection, table_name, params["database"])
        table_types = _get_table_column_types(connection, table_name, params["database"])
        if "OS" in table_columns and not record.get("OS"):
            record["OS"] = record.get("osName") or ""
        status_type = table_types.get("status", "").lower()
        if status_type.startswith("enum(") and "success" in status_type and "failed" in status_type:
            status_map = {"OK": "Success", "NOK": "Failed", "SUCCESS": "Success", "FAILED": "Failed"}
            record["status"] = status_map.get(str(record.get("status") or "").upper(), record.get("status"))
        criticality_type = table_types.get("criticality", "").lower()
        if criticality_type.startswith("enum(") and "low" in criticality_type:
            crit = str(record.get("criticality") or "").strip().lower()
            crit_map = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}
            if crit in crit_map:
                record["criticality"] = crit_map[crit]
        exec_type = table_types.get("execTime", "").lower()
        if exec_type.startswith("time"):
            try:
                total = max(0, int(float(record.get("execTime") or 0)))
                h = total // 3600
                m = (total % 3600) // 60
                s = total % 60
                record["execTime"] = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception:
                pass
        columns = [c for c in default_columns if c in table_columns]
        if not columns:
            return None
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(record.get(c) for c in columns))
            return getattr(cursor, "lastrowid", None)
    finally:
        if connection:
            connection.close()


