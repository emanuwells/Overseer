#!/usr/bin/env bash
# Gera frontend/public/overseer-config.js a partir de .env (não versionar).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${1:-$REPO_ROOT/.env}"
OUT_FILE="${2:-$REPO_ROOT/frontend/public/overseer-config.js}"

TOKEN=""
if [ -f "$ENV_FILE" ]; then
  TOKEN="$(grep -E '^OVERSEER_API_TOKEN=' "$ENV_FILE" | cut -d= -f2- | tr -d '\r' || true)"
fi

mkdir -p "$(dirname "$OUT_FILE")"
printf '%s\n' "window.OVERSEER_CONFIG = window.OVERSEER_CONFIG || { apiToken: $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$TOKEN") };" > "$OUT_FILE"
echo "Config frontend: $OUT_FILE"
