"""
Lightweight lineage emitter — zero DB dependency.

Pipelines import this module and use ``LineageEmitter`` to declare
module-level start/end events.  The only side-effect is a structured
``print()`` line with prefix ``@@OVERSEER_MODULE@@`` followed by a
JSON object.  The orchestrator streams stdout from the subprocess and
parses these markers in real-time, writing them to the
``pipeline_module_events`` table.

Protocol
--------
Start marker::

    @@OVERSEER_MODULE@@{"event":"start","module_id":"ssh_tunnel","critical":true}

End marker::

    @@OVERSEER_MODULE@@{"event":"end","module_id":"ssh_tunnel","status":"OK","message":"Connected in 1.2s"}

Fields
------
- ``event``   (required): ``"start"`` or ``"end"``
- ``module_id`` (required): alphanumeric identifier for the module/stage
- ``critical`` (optional, default ``true``): if ``false``, a failure in
  this module results in WARNING instead of NOK for the whole pipeline.
- ``status``  (only on ``end``): ``"OK"`` or ``"NOK"``
- ``message`` (optional on ``end``): human-readable summary / error
- ``parent_module_id`` (optional): for DAG-style dependencies
- ``context`` (optional): arbitrary dict

Usage
-----
::

    from overseer_monitor.lineage_emitter import LineageEmitter

    emit = LineageEmitter()

    with emit.module("db_connection", critical=True):
        connect_to_db()

    with emit.module("slack_notification", critical=False):
        send_slack()
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from contextlib import contextmanager
from typing import Any, Dict, Optional

MARKER_PREFIX = "@@OVERSEER_MODULE@@"


class LineageEmitter:
    """Emit structured lineage markers to stdout for the orchestrator to capture."""

    def __init__(self, *, flush: bool = True) -> None:
        self._flush = flush

    # ------------------------------------------------------------------
    # Low-level emit
    # ------------------------------------------------------------------

    def _emit(self, payload: Dict[str, Any]) -> None:
        line = f"{MARKER_PREFIX}{json.dumps(payload, ensure_ascii=False, default=str)}"
        print(line, flush=self._flush)

    def emit_start(
        self,
        module_id: str,
        *,
        critical: bool = True,
        parent_module_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        msg: Dict[str, Any] = {
            "event": "start",
            "module_id": module_id,
            "critical": critical,
        }
        if parent_module_id:
            msg["parent_module_id"] = parent_module_id
        if context:
            msg["context"] = context
        self._emit(msg)

    def emit_end(
        self,
        module_id: str,
        *,
        status: str = "OK",
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        msg: Dict[str, Any] = {
            "event": "end",
            "module_id": module_id,
            "status": status,
        }
        if message:
            msg["message"] = message
        if context:
            msg["context"] = context
        self._emit(msg)

    # ------------------------------------------------------------------
    # Context-manager helper
    # ------------------------------------------------------------------

    @contextmanager
    def module(
        self,
        module_id: str,
        *,
        critical: bool = True,
        parent_module_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Context manager that emits start/end markers automatically.

        If the wrapped block raises, the end marker has ``status="NOK"``
        and the exception message is included.  The exception is **not**
        swallowed — it re-raises after emitting the marker.
        """
        self.emit_start(
            module_id,
            critical=critical,
            parent_module_id=parent_module_id,
            context=context,
        )
        t0 = time.monotonic()
        try:
            yield
        except Exception as exc:
            elapsed = round(time.monotonic() - t0, 3)
            err_msg = str(exc)[:1200]
            self.emit_end(
                module_id,
                status="NOK",
                message=err_msg,
                context={"duration_sec": elapsed},
            )
            raise
        else:
            elapsed = round(time.monotonic() - t0, 3)
            self.emit_end(
                module_id,
                status="OK",
                message=f"completed in {elapsed}s",
                context={"duration_sec": elapsed},
            )
