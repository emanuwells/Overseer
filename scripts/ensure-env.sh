#!/usr/bin/env bash
# Garante secrets/.env (migra .env legado da raiz se existir).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${OVERSEER_ENV_FILE:-$REPO_ROOT/secrets/.env}"
TEMPLATE="$REPO_ROOT/docs/resources/templates/.env.example"
LEGACY="$REPO_ROOT/.env"

if [ -f "$LEGACY" ] && [ ! -f "$ENV_FILE" ]; then
  mkdir -p "$(dirname "$ENV_FILE")"
  mv "$LEGACY" "$ENV_FILE"
  echo "Movido .env da raiz para secrets/.env"
fi

if [ ! -f "$ENV_FILE" ]; then
  if [ ! -f "$TEMPLATE" ]; then
    echo "Falta $TEMPLATE" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$ENV_FILE")"
  cp "$TEMPLATE" "$ENV_FILE"
  echo "Criado secrets/.env a partir do exemplo. Ajusta OVERSEER_API_TOKEN se necessário."
fi

export OVERSEER_ENV_FILE="$ENV_FILE"
