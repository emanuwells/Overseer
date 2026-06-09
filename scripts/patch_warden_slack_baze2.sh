#!/usr/bin/env bash
# Apply Warden Slack policy on baze2: digest-only to #overseer at 08:00 UTC.
set -euo pipefail

WARDEN="${WARDEN_DIR:-/home/eferreira/MAIATRON/Warden}"

if [ ! -d "$WARDEN" ]; then
  echo "ERRO: Warden não encontrado em $WARDEN" >&2
  exit 1
fi

python3 - "$WARDEN" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
digest = root / "scripts" / "slack_daily_digest.py"
alerts = root / "scripts" / "slack_alerts.py"
secrets = root / "secrets" / "slack.json"

text = digest.read_text(encoding="utf-8")
text = text.replace(
    'channel_override=notifier.channel or "#warden"',
    'channel_override=notifier.channel or "#overseer"',
)
digest.write_text(text, encoding="utf-8")

text = alerts.read_text(encoding="utf-8")
if "IMMEDIATE_SLACK_ENABLED" not in text:
    text = text.replace(
        "SEND_WARNINGS_TO_SLACK = True",
        'SEND_WARNINGS_TO_SLACK = False\n'
        'IMMEDIATE_SLACK_ENABLED = os.getenv("WARDEN_SLACK_IMMEDIATE", "0").strip().lower() in {"1", "true", "yes", "on"}',
    )
    old = (
        '    if not payload:\n'
        '        logger.error("Payload not found or invalid.")\n'
        '        return 1\n\n'
        '    notifier = SlackNotifier()'
    )
    new = (
        '    if not payload:\n'
        '        logger.error("Payload not found or invalid.")\n'
        '        return 1\n\n'
        '    if not IMMEDIATE_SLACK_ENABLED:\n'
        '        logger.info("Immediate Warden Slack alerts disabled; digest-only mode.")\n'
        '        return 0\n\n'
        '    notifier = SlackNotifier()'
    )
    if old in text:
        text = text.replace(old, new)
alerts.write_text(text, encoding="utf-8")

if secrets.is_file():
    data = json.loads(secrets.read_text(encoding="utf-8"))
    data["channel"] = "#overseer"
    secrets.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Warden Slack patch OK")
PY

echo "Nota: comentar linha slack_alerts no crontab do Warden se ainda existir."
