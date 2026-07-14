# Comandos

## Desenvolvimento

```bash
pip install -r src/requirements.txt
pip install -e ./src
python -m pytest -q
```

## Frontend

### UI com Docker (dados locais)

```powershell
# Windows — arranca API+MariaDB, build UI em /ui/, abre browser opcional
.\scripts\dev-ui.ps1 -OpenBrowser
```

```bash
# Linux/macOS
cp docs/resources/templates/.env.example .env   # se ainda não existir
./scripts/overseer-up.sh
# UI: http://127.0.0.1:8090/ui/operations
```

O contentor injecta `overseer-config.js` a partir de `OVERSEER_API_TOKEN` no arranque.

### Vite dev (hot-reload)

```powershell
# API local (Docker)
.\scripts\dev-frontend.ps1 -Mode local

# API de produção via túnel SSH
$env:OVERSEER_SSH_TARGET = "user@servidor"
.\scripts\dev-frontend.ps1 -Mode prod
```

```bash
cd frontend
npm ci          # preferir fora de Google Drive; ver tasks/lessons.md
npm run dev
```

`npm run dev` usa proxy `/v1` → `http://127.0.0.1:8090` (configurável em `.env.development`).

### Builds

| Comando | Base path | Destino |
|---|---|---|
| `npm run build` | `/ui/` | Docker / FastAPI |
| `npm run build:nginx` | `/Overseer/` | nginx público |

## Docker

```bash
docker compose --project-directory . -f docker/docker-compose.yml config
docker compose --project-directory . -f docker/docker-compose.yml up --build -d
docker compose --project-directory . -f docker/docker-compose.yml logs -f overseer-api
docker compose --project-directory . -f docker/docker-compose.yml down
```

Produção requer `.env`, `OVERSEER_DB_URL`, `OVERSEER_RUNNERS_DIR`, `OVERSEER_RUNTIME_DIR` e diretórios privados persistentes:

```bash
docker compose --project-directory . -f docker/docker-compose.prod.yml config
docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
curl -sf http://127.0.0.1:8090/v1/health
```

## Operações

```bash
overseer-agent trigger <pipeline-id> --host-id <host-id> --by ops
python scripts/overseer_retention.py --dry-run
python scripts/overseer_retention.py --apply
python scripts/maintenance/overseer_db_maintenance.py --pipeline-id <pipeline-id>
```

Utilize `--apply` apenas depois de rever o resultado do modo de simulação. Não execute `docker compose down -v`, purgas, alterações de schema ou operações destrutivas sem backup e confirmação explícita.

## Git e deploy remoto

Defina destino (nunca versionar credenciais):

```powershell
$env:OVERSEER_SSH_TARGET = "user@servidor"
$env:OVERSEER_REPO_PATH = "/caminho/para/Overseer"
.\scripts\deploy-prod.ps1
```

```bash
export OVERSEER_SSH_TARGET=user@servidor
export OVERSEER_REPO_PATH=/caminho/para/Overseer
bash scripts/deploy-prod.sh
```

O deploy faz `git pull`, `docker compose ... prod up --build`, health check e `deploy-nginx-frontend.sh` (build `/Overseer/`).

Comandos manuais:

```bash
ssh <ssh-user>@<server> 'cd <repo-path> && git status --short --branch'
ssh <ssh-user>@<server> 'cd <repo-path> && docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d'
```
