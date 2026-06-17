# COMMANDS.md

Comandos rápidos do Overseer.

## Ambiente

| Ação | Comando |
|---|---|
| Instalar dependências (local) | `pip install -r requirements.txt && pip install -e .` |
| Configurar ambiente | `cp .env.example .env` |
| DB oficial (sem MariaDB local) | `cp .env.official.example .env` |

## Testes, Lint E Build

| Ação | Comando |
|---|---|
| Testes | `python -m pytest -q` |
| Validar Compose | `docker compose config` |
| Build imagem | `docker compose build` |

## Slack

| Ação | Comando |
|---|---|
| Configurar webhook (prod) | Definir `OVERSEER_SLACK_WEBHOOK_URL` e `OVERSEER_SLACK_CHANNEL=#overseer` no `.env` |
| Configurar webhook (local) | `cp secrets/slack.json.example secrets/slack.json` e editar (ficheiro gitignored) |
| Digest manual | `docker compose exec overseer-api python scripts/slack_daily_digest.py` |
| Digest horário | `OVERSEER_SLACK_DIGEST_HOUR=8` + `OVERSEER_SLACK_DIGEST_MINUTE=30` (Europe/Lisbon, **08:30** diário) |
| @channel | `OVERSEER_SLACK_MENTION_CHANNEL=true` (falhas, resolução e digest com falhas em aberto) |
| Falha | alerta imediato + relembrado no digest até run OK |
| Resolvido | alerta imediato quando a run seguinte termina `ok` |
| Desactivar digest | `OVERSEER_SLACK_DIGEST_ENABLED=false` |

## Operações (fora da UI)

Os frontends Overseer (`/ui/`) e MAIATRON Overseer são **read-only**. Catálogo, triggers e sync remoto fazem-se por CLI/API.

| Ação | Comando |
|---|---|
| Token API (local) | Definir `OVERSEER_API_TOKEN` no `.env` ou `js/overseer-config.js` |
| Reconciliar catálogo pós-deploy | `curl -sf -X POST http://127.0.0.1:8090/v1/catalog/reconcile -H "Authorization: Bearer $OVERSEER_API_TOKEN" -H "Content-Type: application/json" -d '{"sync_remote":false}'` |
| Reconciliar + sync remoto | `curl ... -d '{"sync_remote":true}'` |
| PATCH agenda/owner (exemplo) | `curl -X PATCH http://127.0.0.1:8090/v1/catalog/pipelines/traffic_flow -H "Authorization: Bearer $OVERSEER_API_TOKEN" -H "Content-Type: application/json" -d '{"host_id":"baze2","schedule":"0 2 * * *","sync_remote":true}'` |
| Suspender pipeline | `curl -X PATCH .../medidata_pipeline -d '{"host_id":"WS1207","suspended":true,"sync_remote":false}'` |
| Run now (agent) | `overseer-agent trigger medidata_pipeline --host-id WS1207 --by ops` |
| Run now warden_clean (baze2) | `overseer-agent trigger warden_clean --host-id baze2 --by ops` |
| Run now (curl) | `curl -X POST .../v1/orchestrate/triggers -d '{"pipeline_id":"medidata_pipeline","host_id":"WS1207","requested_by":"ops"}'` |
| Purga pipelines legados | `python scripts/purge_legacy_pipelines.py --apply` |
| Retenção telemetria 30d | `python scripts/overseer_retention.py --apply` |
| Retenção (dry-run) | `python scripts/overseer_retention.py --dry-run` |
| Cron retenção (prod) | `0 3 * * * cd ~/Dev/Repos/emanuwells/Overseer && docker compose -f docker-compose.prod.yml exec -T overseer-api python scripts/overseer_retention.py --apply` |

## Sync remoto de runners (SSH)

| Ação | Comando |
|---|---|
| Activar sync na API | `OVERSEER_SSH_SYNC_ENABLED=1` no `.env` (requer chave SSH no host/container) |
| Hosts registados | `deploy/runners/hosts.yaml` |
| Hosts (API read) | `GET /v1/read/runner-hosts` |
| Provision Linux (baze2) | `bash scripts/provision-runners.sh --register` |
| Provision Windows (WS1207) | `.\scripts\windows\provision-runners.ps1 -Register` |
| Run now cross-host | API em baze2 faz SSH ao worker (`baze2` local ou `DQSI@WS1207`) |
| Agenda Windows (Task Scheduler) | Após PATCH com `sync_remote`: `update-taskscheduler-schedule.ps1` no host (automático via SSH) |

## Docker

| Ação | Comando |
|---|---|
| Subir (dev) | `docker compose up --build -d` |
| Subir (prod) | `docker compose -f docker-compose.prod.yml up --build -d` |
| Logs | `docker compose logs -f overseer-api` |
| Parar | `docker compose down` |
| Demo de telemetria | `docker compose exec overseer-api python scripts/overseer_emit_demo.py` |
| Shell na API | `docker compose exec overseer-api sh` |

## Atalhos De Arranque

| Sistema | Comando |
|---|---|
| Windows CMD | `scripts\overseer-up.cmd` |
| PowerShell | `.\scripts\overseer-up.ps1` |
| Linux/macOS | `sh scripts/overseer-up.sh` |

## Git

| Ação | Comando |
|---|---|
| Estado | `git status --short --branch` |
| Branch | `git branch --show-current` |
| Remotes | `git remote -v` |
| Fetch | `git fetch origin` |
| Pull | `git pull origin main` |

## Medidata / WS1207 (Windows, Task Scheduler)

Executar **na máquina WS1207** (PowerShell como DQSI), com repo actualizado e SSH para o prod:

| Passo | Comando |
|---|---|
| 1. Pull repo | `cd C:\MAIATRON\Overseer` (ou o teu clone) → `git pull origin main` |
| 2. Reinstalar agente | `.\scripts\windows\install-runner.ps1 -RepoPath C:\MAIATRON\Overseer -SshTarget eferreira@195.23.9.32` |
| 2b. Reprovisionar Medidata | `.\scripts\windows\provision-runners.ps1 -Register` ou `.\scripts\windows\setup-medidata-overseer.ps1 -SshTarget eferreira@195.23.9.32` |
| 3. Túnel activo | `Get-ScheduledTask -TaskName "Overseer SSH Tunnel"` → `Start-ScheduledTask` se parado |
| 4. Task Medidata | Programa: `powershell.exe` · Args: `-ExecutionPolicy Bypass -File "%USERPROFILE%\overseer-runners\medidata_pipeline\run.ps1"` |
| 5. Migrar 1.ª vez | `.\scripts\windows\migrate-taskscheduler.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"` |
| 6. Inventário Task Scheduler | `.\scripts\windows\collect-taskscheduler-info.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"` |
| 7. Heartbeat com inventário | `.\scripts\windows\heartbeat.ps1` |

Agenda esperada no catálogo: `30 7 * * *` (diário às 07:30). Se passar mais de 24h sem run, o deployment deve aparecer como `stale`.

Onboarding completo (máquina nova): `.\scripts\windows\bootstrap-windows.ps1 -RepoPath C:\MAIATRON\Overseer -SshTarget eferreira@195.23.9.32`

Validar no prod: última run `medidata_pipeline` com `host_id=WS1207` em `/v1/read/runs?pipeline_id=medidata_pipeline` e último heartbeat com `payload.task_scheduler` em `/v1/read/heartbeats?limit=1`.

## Agent no host Linux (após refactor `src/`)

| Ação | Comando |
|---|---|
| Reinstalar agent no venv | `~/overseer-venv/bin/pip install -e ~/Dev/Repos/emanuwells/Overseer` |
| Validar agent | `~/overseer-venv/bin/overseer-agent --help` |
| Testar pipeline | `~/overseer-runners/traffic_flow/run.sh` |
| Republicar UI nginx | `bash ~/Dev/Repos/emanuwells/Overseer/scripts/deploy-nginx-frontend.sh` (sudo para snippet `/etc/nginx`) |

## Produção (SSH)

| Ação | Comando |
|---|---|
| Repo prod | `ssh eferreira@195.23.9.32 'cd ~/Dev/Repos/emanuwells/Overseer && git status --short --branch'` |
| Pull prod | `ssh eferreira@195.23.9.32 'cd ~/Dev/Repos/emanuwells/Overseer && git pull origin main'` |
| Docker prod | `ssh eferreira@195.23.9.32 'cd ~/Dev/Repos/emanuwells/Overseer && docker compose -f docker-compose.prod.yml up --build -d'` |
| Frontend nginx | `ssh eferreira@195.23.9.32 'cd ~/Dev/Repos/emanuwells/Overseer && sudo bash scripts/deploy-nginx-frontend.sh'` |
| Health prod | `ssh eferreira@195.23.9.32 'curl -sf http://127.0.0.1:8090/v1/health'` |

## Comandos Proibidos Sem Confirmação

```bash
git reset --hard
git clean -fd
git push --force
docker compose down -v
rm -rf
DROP DATABASE
TRUNCATE TABLE
systemctl restart
reboot
```

## MCP

| Ação | Comando |
|---|---|
| Política MCP | `cat .agents/mcp/MCP_POLICY.md` |
| Exemplos MCP | `ls .agents/mcp` |

Não imprimir configs reais com tokens ou credenciais.
