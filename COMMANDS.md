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

## Sync remoto de runners (SSH)

| Ação | Comando |
|---|---|
| Activar sync na API | `OVERSEER_SSH_SYNC_ENABLED=1` no `.env` (requer chave SSH no host/container) |
| Hosts registados | `deploy/runners/hosts.yaml` |
| Editar pipeline (UI) | Dashboard → seleccionar linha → **Editar** → Guardar (DB + YAML + SSH) |
| Reconciliar catálogo (UI) | Ambiente → separador **Sync** → **Reconciliar catálogo** |
| Reconciliar catálogo (API) | `POST /v1/catalog/reconcile` com `{"sync_remote": false}` |
| Hosts de sync (API) | `GET /v1/read/runner-hosts` |
| PATCH API | `PATCH /v1/catalog/pipelines/{id}` com `host_id`, `owner`, `schedule`, `sync_remote` |
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
| 2. Upgrade agente | `.\scripts\windows\upgrade-windows-runner.ps1 -SshTarget eferreira@195.23.9.32 -TestMedidata` |
| 3. Túnel activo | `Get-ScheduledTask -TaskName "Overseer SSH Tunnel"` → `Start-ScheduledTask` se parado |
| 4. Task Medidata | Programa: `powershell.exe` · Args: `-ExecutionPolicy Bypass -File "%USERPROFILE%\overseer-runners\medidata_pipeline\run.ps1"` |
| 5. Migrar 1.ª vez | `.\scripts\windows\migrate-taskscheduler.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"` |

Onboarding completo (máquina nova): `.\scripts\windows\bootstrap-windows.ps1 -RepoPath C:\MAIATRON\Overseer -SshTarget eferreira@195.23.9.32`

Validar no prod: última run `medidata_pipeline` com `host_id=WS1207` em `/v1/read/runs?pipeline_id=medidata_pipeline`.

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
