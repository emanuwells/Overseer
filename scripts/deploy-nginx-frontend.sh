#!/usr/bin/env bash
# Publica o frontend do Overseer (build /Overseer/) no nginx e instala locations.
#
# Uso: sudo bash scripts/deploy-nginx-frontend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"
FRONTEND_SRC="$FRONTEND_DIR/dist-nginx"
WEB_ROOT="${OVERSEER_WEB_ROOT:-/usr/share/nginx/html/Overseer}"
LOCATIONS_SRC="$REPO_ROOT/deploy/nginx/overseer-locations.conf"
LOCATIONS_DST="/etc/nginx/overseer-locations.conf"
BUILD_DIR="${OVERSEER_FRONTEND_BUILD_DIR:-}"

echo "==> A construir frontend para nginx (base /Overseer/)"
if [ -n "$BUILD_DIR" ] && [ -d "$BUILD_DIR" ]; then
  cd "$BUILD_DIR/frontend"
else
  cd "$FRONTEND_DIR"
fi
if [ ! -d node_modules ]; then
  npm ci
fi
npm run build:nginx
DIST_OUT="$FRONTEND_DIR/dist-nginx"
rm -rf "$DIST_OUT"
cp -r dist "$DIST_OUT"

if [ ! -d "$FRONTEND_SRC" ]; then
    echo "Build nginx não encontrado em $FRONTEND_SRC" >&2
    exit 1
fi

echo "==> A publicar frontend em $WEB_ROOT"
mkdir -p "$WEB_ROOT"
cp -r "$FRONTEND_SRC"/. "$WEB_ROOT"/

ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/secrets/.env}"
if [ -f "$ENV_FILE" ]; then
    TOKEN="$(grep -E '^OVERSEER_API_TOKEN=' "$ENV_FILE" | cut -d= -f2- || true)"
    if [ -n "$TOKEN" ]; then
        CONFIG_JS="$WEB_ROOT/overseer-config.js"
        printf '%s\n' "window.OVERSEER_CONFIG = { apiToken: $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$TOKEN") };" > "$CONFIG_JS"
        chmod 644 "$CONFIG_JS" 2>/dev/null || true
        echo "==> Token API injectado em $CONFIG_JS"
    else
        echo "AVISO: OVERSEER_API_TOKEN vazio em $ENV_FILE; UI pode devolver 401." >&2
        cp "$FRONTEND_DIR/public/overseer-config.example.js" "$WEB_ROOT/overseer-config.js"
    fi
else
    echo "AVISO: $ENV_FILE não encontrado; a usar overseer-config.example.js." >&2
    cp "$FRONTEND_DIR/public/overseer-config.example.js" "$WEB_ROOT/overseer-config.js"
fi

echo "==> A instalar snippet de proxy em $LOCATIONS_DST"
cp "$LOCATIONS_SRC" "$LOCATIONS_DST"

if nginx -T 2>/dev/null | grep -q "overseer-locations.conf"; then
    echo "==> Include já presente na configuração nginx."
else
    echo "AVISO: adicione manualmente, dentro do server block principal:"
    echo "         include $LOCATIONS_DST;"
    echo "       depois valide e recarregue: nginx -t && systemctl reload nginx"
fi

echo "==> A validar configuração nginx"
nginx -t

echo "==> Concluído. UI: http://<host>/Overseer/"
