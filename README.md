# Overseer

![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20HTML%2FCSS%2FJS%20%7C%20MariaDB-29b6f6)
![Version](https://img.shields.io/badge/version-5.8.0-2ecc71)
![Docker](https://img.shields.io/badge/docker-first-2496ed)
![License](https://img.shields.io/badge/license-A%20confirmar-lightgrey)

Overseer é um núcleo local para observar pipelines e DAGs por API. Recebe catálogo, runs, módulos, logs e heartbeats, persiste eventos numa base de dados e mostra o estado operacional num frontend estático servido pela própria FastAPI.

## Funcionalidades

- API de catálogo para registar pipelines, nodes e edges de DAG.
- API de eventos para runs, módulos, logs e heartbeats.
- Triggers operacionais sem execução local de código de pipelines.
- Frontend read-only em `/ui/dashboard.html` (Operações, Runs, DAG, Ambiente).
- SDK e agente Python para instrumentação em repositórios de pipelines externos.
- Workflow Docker-first com API, UI e MariaDB local.
- Alertas Slack (`#overseer`): falha imediata com `@channel`, digest diário às 08:30 e resolução imediata.

## Stack Técnica

| Área | Tecnologia |
|---|---|
| API | FastAPI, Uvicorn |
| Frontend | HTML, CSS e JavaScript estático |
| Base de dados | MariaDB local; SQLAlchemy com suporte a outros dialectos |
| SDK / Agent | Python, HTTPX |
| Docker | Dockerfile Python e Docker Compose |
| Testes | pytest |

## Arquitetura

```mermaid
flowchart LR
    ui[Frontend /ui] --> read[/v1/read/]
    pipeline[Pipeline externo] --> catalog[/v1/catalog/pipelines/]
    pipeline --> events[/v1/events/]
    pipeline --> triggers[/v1/orchestrate/triggers/]
    catalog --> db[(MariaDB ou DB externa)]
    events --> db
    triggers --> db
    read --> db
```

## Estrutura

```text
Overseer/
  src/
    overseer_api/
    overseer_core/
    overseer_agent/
    overseer_sdk/
    overseer_monitor/
  frontend/
  scripts/
  templates/
  deploy/
  openapi/
  tests/
  docker-compose.yml
  docker-compose.prod.yml
  Dockerfile
  pyproject.toml
  requirements.txt
```

## Requisitos

- Docker com Docker Compose para execução recomendada.
- Python 3.11+ apenas para desenvolvimento local ou testes fora de Docker (`pip install -e .`).

## Instalação E Execução

```bash
docker compose up --build -d
```

Entradas locais:

```text
UI: http://127.0.0.1:8090/ui/dashboard.html
API docs: http://127.0.0.1:8090/docs
Health: http://127.0.0.1:8090/v1/health
```

Scripts equivalentes:

| Sistema | Comando |
|---|---|
| Windows CMD | `scripts\overseer-up.cmd` |
| PowerShell | `.\scripts\overseer-up.ps1` |
| Linux/macOS | `sh scripts/overseer-up.sh` |

## Configuração

Usar `.env.example` como referência e nunca versionar `.env` real.

| Variável | Obrigatória | Descrição |
|---|---:|---|
| `OVERSEER_API_TOKEN` | Não | Token Bearer para endpoints protegidos. |
| `OVERSEER_API_PORT` | Não | Porta HTTP local; padrão `8090`. |
| `OVERSEER_DB_URL` | Não | URL SQLAlchemy para DB externa/oficial. |
| `MYSQL_PASSWORD` | Não | Password local MariaDB do Compose. |
| `MYSQL_ROOT_PASSWORD` | Não | Password root local MariaDB do Compose. |
| `OVERSEER_SLACK_WEBHOOK_URL` | Não | Webhook Slack para alertas e digest (ou `secrets/slack.json`). |
| `OVERSEER_SLACK_DIGEST_HOUR` / `MINUTE` | Não | Digest diário; default `08:30` Europe/Lisbon. |
| `OVERSEER_SSH_SYNC_ENABLED` | Não | Sync remoto de runners após PATCH de pipeline (`1` em prod). |
| `OVERSEER_RETENTION_DAYS` | Não | Janela de retenção de telemetria; default `30`. |

## Uso Por API

Registar um DAG:

```bash
curl -X POST http://127.0.0.1:8090/v1/catalog/pipelines ^
  -H "Content-Type: application/json" ^
  -d "{\"pipeline_id\":\"demo_dag\",\"nodes\":[{\"module_id\":\"extract\"},{\"module_id\":\"load\"}],\"edges\":[{\"from_module_id\":\"extract\",\"to_module_id\":\"load\"}]}"
```

Reconciliar o catálogo a partir de `deploy/runners/*.yaml` (DB ← YAML):

```bash
curl -X POST http://127.0.0.1:8090/v1/catalog/reconcile ^
  -H "Authorization: Bearer $OVERSEER_API_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"sync_remote\": false}"
```

Editar metadados de um deployment (owner, cron, criticidade) com sync para YAML e runner remoto:

```bash
curl -X PATCH http://127.0.0.1:8090/v1/catalog/pipelines/traffic_flow ^
  -H "Authorization: Bearer $OVERSEER_API_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"host_id\":\"baze2\",\"owner\":\"data\",\"schedule\":\"*/15 * * * *\",\"sync_remote\":true}"
```

Emitir uma run de demonstração:

```bash
docker compose exec overseer-api python scripts/overseer_emit_demo.py
```

Integração em pipelines externos:

```bash
python -m pip install -r templates/pipeline-repo/requirements-overseer.txt
```

Ver [docs/pipeline-integration.md](docs/pipeline-integration.md).

## Comandos Principais

```bash
python -m pytest -q
docker compose config
docker compose build
docker compose up -d
docker compose logs -f overseer-api
```

## Testes, Lint E Build

Testes:

```bash
python -m pytest -q
```

Lint: N/A — não há ferramenta de lint configurada no repositório.

Build:

```bash
docker compose build
```

## Docker / Deploy

Docker é o fluxo principal porque o projeto inclui API, base de dados local e frontend servido pela API.

Serviços:

| Serviço | Função |
|---|---|
| `overseer-api` | FastAPI, SDK local e frontend estático. |
| `mysql` | MariaDB local para desenvolvimento. |

Produção: `docker compose -f docker-compose.prod.yml up --build -d` no host com DB em `127.0.0.1`. Ver `COMMANDS.md`.

## Troubleshooting

| Sintoma | Ação |
|---|---|
| API devolve 401 | Guardar na UI o mesmo token definido em `OVERSEER_API_TOKEN`. |
| DB aparece indisponível | Verificar `docker compose ps`, `OVERSEER_DB_URL` e logs do serviço `mysql`. |
| Dashboard vazio | Registar um DAG via `/v1/catalog/pipelines` ou executar `scripts/overseer_emit_demo.py`. |
| `/ui/` não abre | Usar `/ui/dashboard.html` e confirmar que o container foi reconstruído. |
| Runs pararam no MAIATRON | Reinstalar agent no host: `~/overseer-venv/bin/pip install -e ~/Dev/Repos/emanuwells/Overseer` (após refactor `src/`). |
| `https://…/Overseer/` devolve 503 | O host expõe HTTP na porta 80; HTTPS pode terminar noutro proxy — usar `http://` ou corrigir o proxy SSL. |
| UI nginx desactualizada | `bash scripts/deploy-nginx-frontend.sh` (sudo para `/etc/nginx/overseer-locations.conf`). |

## Segurança

- Não guardar `.env`, tokens, passwords, chaves SSH, cookies ou strings de ligação reais no Git.
- Exemplos usam valores fictícios.
- URLs de DB expostas pela API são mascaradas.
- Outputs de pipelines devem ser tratados como dados não confiáveis.

## MCP Servers E Skills

- MCP: exemplos e política em [.agents/mcp/](.agents/mcp/) (`MCP_POLICY.md`, `cursor.mcp.example.json`). Configs reais ficam no IDE e fora do Git.
- Slack não usa MCP — integração nativa via webhook em `overseer_core/slack_alerts.py` e digest em `slack_digest.py`.
- Skills: [.agents/skills/README.md](.agents/skills/README.md) (compatibilidade Claude em `.claude/skills/`).

## Changelog

Ver [CHANGELOG.md](CHANGELOG.md).

## Licença

A confirmar.
