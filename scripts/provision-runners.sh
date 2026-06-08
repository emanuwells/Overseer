#!/usr/bin/env bash
# Provisiona manifests e run.sh em ~/overseer-runners/ a partir do catálogo YAML.
#
# O catálogo resolve automaticamente para deploy/runners/<hostname>.yaml
# (ex.: baze2.yaml no servidor prod). Override com OVERSEER_RUNNERS_CATALOG.
#
# Uso:
#   bash scripts/provision-runners.sh
#   bash scripts/provision-runners.sh --register
#   bash scripts/provision-runners.sh --register --crontab
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNNERS_ROOT="${OVERSEER_RUNNERS_ROOT:-$HOME/overseer-runners}"
VENV="${OVERSEER_VENV:-$HOME/overseer-venv}"
ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/.env}"

REGISTER=""
CRONTAB=""
CATALOG_ARG=()
for arg in "$@"; do
    case "$arg" in
        --register) REGISTER="--register" ;;
        --crontab) CRONTAB="--crontab" ;;
        --catalog)
            echo "AVISO: passe o caminho como --catalog=<ficheiro>" >&2
            ;;
        --catalog=*)
            CATALOG_ARG=(--catalog "${arg#--catalog=}")
            ;;
    esac
done

python3 "$REPO_ROOT/scripts/provision_runners.py" \
    "${CATALOG_ARG[@]}" \
    --repo-root "$REPO_ROOT" \
    --runners-root "$RUNNERS_ROOT" \
    --venv "$VENV" \
    --env-file "$ENV_FILE" \
    --catalog-json-out /tmp/overseer_runner_catalog.json \
    $REGISTER

if [ "$CRONTAB" = "--crontab" ]; then
    python3 "$REPO_ROOT/scripts/update-crontab-overseer.py" \
        --catalog-json /tmp/overseer_runner_catalog.json \
        --backup-dir "$HOME/backups"
fi
