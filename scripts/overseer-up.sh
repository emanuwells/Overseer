#!/usr/bin/env sh
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/ensure-env.sh
. "$(dirname "$0")/ensure-env.sh"

PORT="${OVERSEER_API_PORT:-8090}"
COMPOSE="docker compose --project-directory . --env-file secrets/.env -f docker/docker-compose.yml"

if [ "${1:-}" = "--pull" ]; then
  $COMPOSE pull
fi

$COMPOSE up --build -d

HEALTH="http://127.0.0.1:${PORT}/v1/health"
UI="http://127.0.0.1:${PORT}/ui/operations"
elapsed=0

while [ "$elapsed" -lt 120 ]; do
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS "$HEALTH" >/dev/null 2>&1; then
      echo "Overseer pronto: $UI"
      echo "API: http://127.0.0.1:${PORT}/v1/health"
      echo "Produção nginx: http://<host>/Overseer/"
      exit 0
    fi
  elif command -v wget >/dev/null 2>&1; then
    if wget -qO- "$HEALTH" >/dev/null 2>&1; then
      echo "Overseer pronto: $UI"
      echo "API: http://127.0.0.1:${PORT}/v1/health"
      exit 0
    fi
  else
    echo "Overseer arrancado: $UI"
    echo "Health check requer curl ou wget."
    exit 0
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

echo "Overseer arrancou, mas o health check nao respondeu em 120s: $HEALTH"
exit 1
