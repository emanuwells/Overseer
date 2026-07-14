param(
    [string]$SshTarget = $env:OVERSEER_SSH_TARGET,
    [string]$RepoPath = $env:OVERSEER_REPO_PATH
)

$ErrorActionPreference = "Stop"
if (-not $SshTarget) { throw "Defina -SshTarget ou OVERSEER_SSH_TARGET" }
if (-not $RepoPath) { throw "Defina -RepoPath ou OVERSEER_REPO_PATH" }

$remote = @"
set -euo pipefail
cd '$RepoPath'
git fetch origin
git checkout main
git pull --ff-only origin main
bash scripts/ensure-env.sh
docker compose --project-directory . --env-file secrets/.env -f docker/docker-compose.prod.yml up --build -d
curl -sf http://127.0.0.1:8090/v1/health
sudo OVERSEER_ENV_FILE=secrets/.env bash scripts/deploy-nginx-frontend.sh
"@

Write-Host "==> Deploy em ${SshTarget}:${RepoPath}"
ssh $SshTarget $remote
Write-Host "==> Deploy concluido. Verifique http://<host>/Overseer/"
