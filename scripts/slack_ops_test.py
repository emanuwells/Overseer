#!/usr/bin/env python3
"""Send Slack digest or synthetic failure/resolution alerts for ops validation."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from overseer_core import slack_alerts, store  # noqa: E402
from overseer_core.slack_digest import send_daily_digest  # noqa: E402


def _test_run(*, status: str, suffix: str) -> dict:
    run_id = f"slack-test-{suffix}-{uuid.uuid4().hex[:8]}"
    return {
        "run_id": run_id,
        "pipeline_id": "slack_ops_test",
        "pipeline_name": "[TEST] Slack ops",
        "host_id": "BAZE2",
        "hostname": "BAZE2",
        "status": status,
        "duration_sec": 1.0,
        "error_message": "[TEST] Falha simulada para validação de alertas Slack.",
        "started_at": store.utcnow().isoformat(),
        "ended_at": store.utcnow().isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Slack digest and alert smoke tests.")
    parser.add_argument("--digest", action="store_true", help="Enviar digest diário agora")
    parser.add_argument("--failed", action="store_true", help="Enviar alerta de falha sintético")
    parser.add_argument("--resolved", action="store_true", help="Enviar alerta de resolução sintético")
    args = parser.parse_args()

    if not any((args.digest, args.failed, args.resolved)):
        parser.error("Indique pelo menos uma opção: --digest, --failed, --resolved")

    notifier = slack_alerts.get_slack_notifier()
    if not notifier.is_enabled:
        print("Slack webhook não configurado.", file=sys.stderr)
        return 1

    exit_code = 0
    if args.digest:
        ok = send_daily_digest()
        print("digest_sent" if ok else "digest_failed")
        exit_code |= 0 if ok else 1

    failed_run = _test_run(status="failed", suffix="failed")
    ok_run = _test_run(status="ok", suffix="resolved")

    if args.failed:
        ok = slack_alerts.notify_failed_run(failed_run)
        print("failed_alert_sent" if ok else "failed_alert_failed")
        exit_code |= 0 if ok else 1

    if args.resolved:
        ok = slack_alerts.notify_resolved_run(ok_run, failed_run)
        print("resolved_alert_sent" if ok else "resolved_alert_failed")
        exit_code |= 0 if ok else 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
