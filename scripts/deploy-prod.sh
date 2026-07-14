#!/usr/bin/env bash
# Deploy remoto: git pull, Docker prod, nginx frontend.
# Requer: OVERSEER_SSH_TARGET e OVERSEER_REPO_PATH
set -euo pipefail

TARGET="${OVERSEER_SSH_TARGET:?Defina OVERSEER_SSH_TARGET (ex. user@host)}"
REPO_PATH="${OVERSEER_REPO_PATH:?Defina OVERSEER_REPO_PATH (caminho no servidor)}"

echo "==> Deploy em $TARGET:$REPO_PATH"
ssh "$TARGET" "set -euo pipefail
  cd '$REPO_PATH'
  git fetch origin
  git checkout main
  git pull --ff-only origin main
  docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
  curl -sf http://127.0.0.1:8090/v1/health
  sudo bash scripts/deploy-nginx-frontend.sh
"
echo "==> Deploy concluido. Verifique http://<host>/Overseer/"
