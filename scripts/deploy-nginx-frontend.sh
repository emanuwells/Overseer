#!/usr/bin/env bash
# Publica o frontend do Overseer no web root do nginx e instala o snippet de
# proxy da API (/v1 -> 127.0.0.1:8090).
#
# Suporta dois cenários:
#   - Host dedicado: usar deploy/nginx/overseer.conf (server block próprio).
#   - Host multi-aplicação (um server block partilhado): usar
#     deploy/nginx/overseer-locations.conf incluído dentro do server block.
#
# Este script trata do cenário multi-aplicação de forma conservadora: copia o
# frontend, instala o snippet de locations e NÃO edita automaticamente a
# configuração principal do nginx. Indica a linha de include a adicionar quando
# ainda não existir. Requer privilégios para escrever em /etc/nginx.
#
# Uso: sudo bash scripts/deploy-nginx-frontend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_SRC="$REPO_ROOT/frontend"
WEB_ROOT="${OVERSEER_WEB_ROOT:-/usr/share/nginx/html/Overseer}"
LOCATIONS_SRC="$REPO_ROOT/deploy/nginx/overseer-locations.conf"
LOCATIONS_DST="/etc/nginx/overseer-locations.conf"

if [ ! -d "$FRONTEND_SRC" ]; then
    echo "Frontend não encontrado em $FRONTEND_SRC" >&2
    exit 1
fi

echo "==> A publicar frontend em $WEB_ROOT"
mkdir -p "$WEB_ROOT"
cp -r "$FRONTEND_SRC"/. "$WEB_ROOT"/

ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/.env}"
if [ -f "$ENV_FILE" ]; then
    TOKEN="$(grep -E '^OVERSEER_API_TOKEN=' "$ENV_FILE" | cut -d= -f2- || true)"
    if [ -n "$TOKEN" ]; then
        CONFIG_JS="$WEB_ROOT/js/overseer-config.js"
        printf '%s\n' "window.OVERSEER_CONFIG = { apiToken: $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$TOKEN") };" > "$CONFIG_JS"
        chmod 644 "$CONFIG_JS" 2>/dev/null || true
        echo "==> Token API injectado em $CONFIG_JS"
    else
        echo "AVISO: OVERSEER_API_TOKEN vazio em $ENV_FILE; UI pode devolver 401." >&2
        cp "$FRONTEND_SRC/js/overseer-config.example.js" "$WEB_ROOT/js/overseer-config.js"
    fi
else
    echo "AVISO: $ENV_FILE não encontrado; a usar overseer-config.example.js." >&2
    cp "$FRONTEND_SRC/js/overseer-config.example.js" "$WEB_ROOT/js/overseer-config.js"
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

echo "==> Concluído. UI: http://<host>/Overseer/dashboard.html"
