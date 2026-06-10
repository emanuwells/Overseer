# COMMANDS.md

Comandos rápidos do Overseer.

## Ambiente

| Ação | Comando |
|---|---|
| Instalar dependências (local) | `pip install -r requirements.txt` |
| Configurar ambiente | `cp .env.example .env` |
| DB oficial (sem MariaDB local) | `cp .env.official.example .env` |

## Testes, Lint E Build

| Ação | Comando |
|---|---|
| Testes | `python -m pytest -q` |
| Validar Compose | `docker compose config` |
| Build imagem | `docker compose build` |

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
