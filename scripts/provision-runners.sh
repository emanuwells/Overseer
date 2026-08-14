#!/usr/bin/env bash
# Provisiona manifests e run.sh em runtime/runners/ (dentro do repo) a partir
# do catálogo YAML.
#
# O catálogo resolve em OVERSEER_RUNNERS_DIR/<hostname>.yaml.
#
# Uso:
#   bash scripts/provision-runners.sh
#   bash scripts/provision-runners.sh --register
#   bash scripts/provision-runners.sh --register --crontab
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNNERS_ROOT="${OVERSEER_RUNNERS_ROOT:-$REPO_ROOT/runtime/runners}"
VENV="${OVERSEER_VENV:-$REPO_ROOT/.venv}"
ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/secrets/.env}"
if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

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

PYTHON="$VENV/bin/python3"
if [ ! -x "$PYTHON" ]; then
    echo "ERRO: venv Python não encontrado em $PYTHON" >&2
    echo "Cria o venv: python3 -m venv $VENV && $VENV/bin/pip install -r $REPO_ROOT/src/requirements.txt && $VENV/bin/pip install -e $REPO_ROOT/src" >&2
    exit 1
fi

"$PYTHON" "$REPO_ROOT/scripts/provision_runners.py" \
    "${CATALOG_ARG[@]}" \
    --repo-root "$REPO_ROOT" \
    --runners-root "$RUNNERS_ROOT" \
    --venv "$VENV" \
    --env-file "$ENV_FILE" \
    --catalog-json-out /tmp/overseer_runner_catalog.json \
    $REGISTER

if [ "$CRONTAB" = "--crontab" ]; then
    "$PYTHON" "$REPO_ROOT/scripts/update-crontab-overseer.py" \
        --catalog-json /tmp/overseer_runner_catalog.json \
        --backup-dir "$HOME/backups"
fi
