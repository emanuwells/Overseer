#!/usr/bin/env bash
# Instala overseer-locations.conf e recarrega nginx (requer sudo).
# Uso: bash scripts/install-nginx-overseer.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/deploy/nginx/overseer-locations.conf"
DST="/etc/nginx/overseer-locations.conf"
TS="$(date +%Y%m%d%H%M%S)"

if [ ! -f "$SRC" ]; then
  echo "Falta $SRC" >&2
  exit 1
fi

echo "==> Backup $DST -> ${DST}.bak.${TS}"
sudo cp "$DST" "${DST}.bak.${TS}" 2>/dev/null || true

echo "==> Instalar $SRC em $DST"
sudo cp "$SRC" "$DST"

echo "==> Validar e recarregar nginx"
sudo nginx -t
sudo systemctl reload nginx

echo "==> Concluído. Teste: curl -I http://<host>/Overseer/operations"
