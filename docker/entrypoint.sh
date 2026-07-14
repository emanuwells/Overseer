#!/bin/sh
set -eu

CONFIG="/app/frontend/dist/overseer-config.js"
if [ -d /app/frontend/dist ]; then
  TOKEN="${OVERSEER_API_TOKEN:-}"
  if [ -n "$TOKEN" ]; then
    python3 -c "import json, os; print('window.OVERSEER_CONFIG = { apiToken: ' + json.dumps(os.environ.get('OVERSEER_API_TOKEN', '')) + ' };')" > "$CONFIG"
  elif [ ! -f "$CONFIG" ]; then
    cp /app/frontend/public/overseer-config.example.js "$CONFIG" 2>/dev/null || true
  fi
fi

exec "$@"
