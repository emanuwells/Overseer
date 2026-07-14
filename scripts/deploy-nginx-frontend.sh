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
ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/secrets/.env}"
case "$ENV_FILE" in
  /*) ;;
  *) ENV_FILE="$REPO_ROOT/$ENV_FILE" ;;
esac

echo "==> A construir frontend para nginx (base /Overseer/)"
build_nginx_frontend() {
  if [ -n "$BUILD_DIR" ] && [ -d "$BUILD_DIR" ]; then
    cd "$BUILD_DIR/frontend"
  else
    cd "$FRONTEND_DIR"
  fi
  local node_major=0
  if command -v node >/dev/null 2>&1; then
    node_major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
  fi
  if [ "$node_major" -ge 20 ] 2>/dev/null; then
    if [ ! -d node_modules ]; then
      npm ci
    fi
    npm run build:nginx
  else
    echo "Node local < 20; a usar Docker node:20-alpine para o build."
    docker run --rm -v "$FRONTEND_DIR":/app -w /app node:20-alpine sh -c "npm ci && npm run build:nginx"
  fi
}
build_nginx_frontend
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
rm -f "$WEB_ROOT"/dashboard.html "$WEB_ROOT"/deployments.html "$WEB_ROOT"/lineage.html "$WEB_ROOT"/run-detail.html
rm -rf "$WEB_ROOT"/css "$WEB_ROOT"/js
# Remover fallbacks legados (causam 301 desnecessários quando nginx tem try_files SPA).
rm -rf "$WEB_ROOT"/operations "$WEB_ROOT"/runs "$WEB_ROOT"/dag "$WEB_ROOT"/environment

if [ -f "$ENV_FILE" ]; then
    bash "$REPO_ROOT/scripts/generate-frontend-config.sh" "$ENV_FILE" "$WEB_ROOT/overseer-config.js"
    chmod 644 "$WEB_ROOT/overseer-config.js" 2>/dev/null || true
    echo "==> Token API injectado em $WEB_ROOT/overseer-config.js"
else
    echo "AVISO: $ENV_FILE não encontrado; a usar overseer-config.example.js." >&2
    cp "$FRONTEND_DIR/public/overseer-config.example.js" "$WEB_ROOT/overseer-config.js"
fi

echo "==> A instalar snippet de proxy em $LOCATIONS_DST"
if cp "$LOCATIONS_SRC" "$LOCATIONS_DST" 2>/dev/null; then
  if nginx -T 2>/dev/null | grep -q "overseer-locations.conf"; then
    echo "==> Include já presente na configuração nginx."
  else
    echo "AVISO: adicione manualmente, dentro do server block principal:"
    echo "         include $LOCATIONS_DST;"
    echo "       depois valide e recarregue: nginx -t && systemctl reload nginx"
  fi
  echo "==> A validar configuração nginx"
  nginx -t
else
  echo "AVISO: sem permissão para $LOCATIONS_DST; frontend publicado, nginx locations inalterado."
  echo "       Execute no servidor: bash scripts/install-nginx-overseer.sh"
fi

echo "==> Concluído. UI: http://<host>/Overseer/"
