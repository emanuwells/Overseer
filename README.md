# Overseer

![Estado](https://img.shields.io/badge/estado-stable-2ecc71)
![Versão](https://img.shields.io/badge/vers%C3%A3o-5.8.2-3498db)
![Licença](https://img.shields.io/badge/licen%C3%A7a-propriet%C3%A1ria-lightgrey)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-003545?logo=mariadb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

Núcleo Docker-first de observabilidade para pipelines e DAGs externos. O Overseer recebe catálogo e telemetria por API, persiste eventos operacionais na base de dados e expõe uma interface read-only — sem executar o código dos pipelines.

## Funcionalidades

- **Catálogo DAG** — registo idempotente de pipelines, nodes e edges via `/v1/catalog/pipelines`.
- **Telemetria** — runs, módulos, logs e heartbeats em `/v1/events/*`.
- **Leitura operacional** — overview, deployments, runs, DAG e estado da DB em `/v1/read/*`.
- **Orquestração** — triggers com dispatch SSH a workers Linux e Windows.
- **Interface read-only** — dashboard, runs, lineage e ambiente em `/ui/`.
- **Observabilidade Windows** — heartbeat com inventário read-only do Task Scheduler (v5.8.1).
- **Staleness diário** — deployments com agenda activa e sem runs há mais de 24h aparecem como `stale`.

## Arquitectura

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

O Overseer não executa pipelines. Cada repositório de pipeline mantém o seu código; a observabilidade liga-se por API ou por manifest YAML nos runners (`~/overseer-runners/` ou `%USERPROFILE%\overseer-runners\`).

## Stack

| Área | Tecnologia |
|---|---|
| API | FastAPI, Uvicorn |
| Frontend | HTML, CSS e JavaScript estático |
| Base de dados | MariaDB local; SQLAlchemy para outros dialectos |
| SDK / Agent | Python, HTTPX, pacote `overseer-core` |
| Configuração | `.env`, variáveis `OVERSEER_*` |
| Docker | Dockerfile Python, Docker Compose |
| Testes | `pytest` |

## Instalação

O caminho oficial é Docker-first (Windows, Linux e macOS).

```bash
cp .env.example .env
docker compose up --build -d
```

Atalhos por sistema operativo:

| Sistema | Comando |
|---|---|
| Windows CMD | `scripts\overseer-up.cmd` |
| PowerShell | `.\scripts\overseer-up.ps1` |
| Linux/macOS | `sh scripts/overseer-up.sh` |

Para ligar a uma base de dados oficial existente, copiar `.env.official.example` para `.env` e preencher `OVERSEER_DB_URL`.

Python local é necessário apenas para desenvolvimento e testes:

```bash
pip install -r requirements.txt && pip install -e .
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição | Exemplo |
|---|---:|---|---|
| `OVERSEER_API_TOKEN` | Não | Token Bearer para APIs protegidas | `change-me-local-token` |
| `OVERSEER_API_PORT` | Não | Porta HTTP local | `8090` |
| `OVERSEER_DB_URL` | Não | URL SQLAlchemy canónica | `mysql+pymysql://overseer:overseer@mysql:3306/Overseer?charset=utf8mb4` |
| `MYSQL_PASSWORD` | Não | Password MariaDB local | `overseer` |
| `MYSQL_ROOT_PASSWORD` | Não | Password root MariaDB local | `overseer` |
| `OVERSEER_SSH_SYNC_ENABLED` | Não | Activar sync remoto de runners via SSH | `1` |
| `OVERSEER_SLACK_WEBHOOK_URL` | Não | Webhook Slack para alertas e digest | — |

Lista completa e comandos operacionais em [`COMMANDS.md`](COMMANDS.md).

## Integração de pipelines

Pipelines externos comunicam com o Overseer por API. O contrato está documentado em [`docs/pipeline-integration.md`](docs/pipeline-integration.md).

| Modelo | Uso |
|---|---|
| SDK no repo do pipeline | Instrumentação directa com `overseer_bootstrap.py` (`templates/pipeline-repo/`) |
| Manifest YAML no host | Observabilidade sem alterar código (`templates/runner/` e `templates/runner-windows/`) |
| Catálogo por host | `deploy/runners/<hostname>.yaml` — ver [`deploy/runners/README.md`](deploy/runners/README.md) |

Exemplo em produção: **Medidata Pipeline** em `WS1207` (Windows, Task Scheduler, agenda `30 7 * * *`).

## Verificação

```bash
python -m pytest -q
docker compose config
docker compose build
```

Com a stack activa:

| Verificação | URL / comando |
|---|---|
| Health | `http://127.0.0.1:8090/v1/health` |
| Dashboard | `http://127.0.0.1:8090/ui/dashboard.html` |
| Estado DB | `http://127.0.0.1:8090/v1/read/database` |
| Demo telemetria | `docker compose exec overseer-api python scripts/overseer_emit_demo.py` |

## Estrutura do repositório

```text
Overseer/
├── src/
│   ├── overseer_api/
│   ├── overseer_core/
│   ├── overseer_agent/
│   ├── overseer_sdk/
│   └── overseer_monitor/
├── frontend/
├── scripts/
├── templates/
├── deploy/
├── openapi/
├── tests/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
└── pyproject.toml
```

## Documentação relacionada

| Ficheiro | Conteúdo |
|---|---|
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Contexto, fluxos e critérios de verificação |
| [`COMMANDS.md`](COMMANDS.md) | Comandos rápidos (Docker, ops, prod, WS1207) |
| [`docs/pipeline-integration.md`](docs/pipeline-integration.md) | Contrato de integração de pipelines |
| [`docs/adr/`](docs/adr/) | Decisões arquitecturais |
| [`.agents/`](.agents/) | Políticas e operação para agentes IA |
| [`CHANGELOG.md`](CHANGELOG.md) | Histórico de versões |

## Licença

Licença proprietária — todos os direitos reservados. Ver [`LICENSE`](LICENSE).
