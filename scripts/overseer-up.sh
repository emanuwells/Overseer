#!/usr/bin/env sh
set -eu

PORT="${OVERSEER_API_PORT:-8090}"
COMPOSE="docker compose --project-directory . -f docker/docker-compose.yml"

if [ "${1:-}" = "--pull" ]; then
  $COMPOSE pull
fi

$COMPOSE up --build -d

HEALTH="http://127.0.0.1:${PORT}/v1/health"
UI="http://127.0.0.1:${PORT}/ui/"
elapsed=0

while [ "$elapsed" -lt 120 ]; do
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS "$HEALTH" >/dev/null 2>&1; then
      echo "Overseer pronto: $UI"
      echo "API: http://127.0.0.1:${PORT}/docs"
      exit 0
    fi
  elif command -v wget >/dev/null 2>&1; then
    if wget -qO- "$HEALTH" >/dev/null 2>&1; then
      echo "Overseer pronto: $UI"
      echo "API: http://127.0.0.1:${PORT}/docs"
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
