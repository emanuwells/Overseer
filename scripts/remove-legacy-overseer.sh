#!/usr/bin/env bash
# Remove o Overseer legado (~/MAIATRON/Overseer) após preservar Python portátil.
# Também remove o location nginx /apps/overseer/ se existir.
#
# Uso: bash scripts/remove-legacy-overseer.sh
set -euo pipefail

LEGACY="$HOME/MAIATRON/Overseer"
PY_DEST="$HOME/overseer-py"
BACKUP_ROOT="$HOME/backups"
TS="$(date +%F-%H%M%S)"

if [ -d "$LEGACY/.pyportable/python" ] && [ ! -x "$PY_DEST/.pyportable/python/bin/python3.11" ]; then
    echo "==> A preservar Python portátil em $PY_DEST/.pyportable"
    mkdir -p "$PY_DEST"
    cp -a "$LEGACY/.pyportable" "$PY_DEST/"
fi

if [ -d "$LEGACY" ]; then
    ARCHIVE="$BACKUP_ROOT/MAIATRON-Overseer-legacy-$TS"
    mkdir -p "$BACKUP_ROOT"
    echo "==> A arquivar legado em $ARCHIVE"
    mv "$LEGACY" "$ARCHIVE"
fi

if [ -d /usr/share/nginx/html/MAIATRON/apps/overseer ]; then
    echo "==> A remover frontend legado em /usr/share/nginx/html/MAIATRON/apps/overseer"
    rm -rf /usr/share/nginx/html/MAIATRON/apps/overseer
fi

NGINX_CONF="/etc/nginx/nginx.conf"
if [ -f "$NGINX_CONF" ] && grep -q "location /apps/overseer/" "$NGINX_CONF" 2>/dev/null; then
    echo "==> A remover bloco /apps/overseer/ do nginx (requer sudo)"
    if [ "$(id -u)" -ne 0 ]; then
        echo "Execute com sudo para editar nginx: sudo bash $0" >&2
    else
        mkdir -p "$BACKUP_ROOT"
        cp "$NGINX_CONF" "$BACKUP_ROOT/nginx.conf.before-legacy-removal-$TS"
        python3 - <<'PY'
import pathlib
import re

path = pathlib.Path("/etc/nginx/nginx.conf")
text = path.read_text(encoding="utf-8")
pattern = r"\n\tlocation /apps/overseer/ \{.*?\n\}\n"
new_text, count = re.subn(pattern, "\n", text, flags=re.DOTALL)
if count:
    path.write_text(new_text, encoding="utf-8")
    print(f"Removidos {count} blocos /apps/overseer/")
else:
    print("Nenhum bloco /apps/overseer/ encontrado para remover.")
PY
        nginx -t && systemctl reload nginx
    fi
fi

echo "==> Legado removido. Recrie o venv com: $PY_DEST/.pyportable/python/bin/python3.11 -m venv ~/overseer-venv"
