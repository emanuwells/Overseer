# PROJECT_CONTEXT — Overseer

Este ficheiro descreve o contexto específico do projeto Overseer. Deve ser lido em conjunto com `AGENTS.md`, `.agents/ops/HANDOFF.md`, `.agents/skills/README.md`, `.agents/policies/CHANGELOG_POLICY.md` e `README.md`.

## Identidade Do Projeto

| Campo | Valor |
|---|---|
| Nome | Overseer |
| Tipo | Núcleo Docker para observabilidade de pipelines e DAGs |
| Responsável | A confirmar |
| Estado | Núcleo v4.2.0 com catálogo DAG por API e frontend estático operacional |
| Escala | Projeto técnico não trivial, com API, DB, frontend, Docker, SDK e templates |

## Objetivo

Disponibilizar um workflow Docker-first que arranca API, frontend e base de dados local. O Overseer recebe catálogo DAG e telemetria por API, persiste eventos operacionais na DB e permite acompanhar o funcionamento de pipelines externos sem executar o seu código.

## Stack Técnica

| Área | Tecnologia |
|---|---|
| API | FastAPI, Uvicorn |
| Frontend | HTML, CSS e JavaScript estático |
| Base de dados | MariaDB local; SQLAlchemy para outros dialectos |
| SDK / Agent | Python, HTTPX, pacote instalável `overseer-core` |
| Configuração | `.env.example`, variáveis de ambiente |
| Docker | Dockerfile Python, Docker Compose |
| Testes | `pytest` |

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

## Fluxos Principais

| Fluxo | Origem | Processamento | Destino |
|---|---|---|---|
| Catálogo DAG | Pipeline externo ou SDK | `/v1/catalog/pipelines` | `overseer_pipelines`, `overseer_pipeline_nodes`, `overseer_pipeline_edges` |
| Leitura | Frontend/API client | `/v1/read/*` | JSON operacional |
| Estado DB | Frontend/API client | `/v1/read/database` | URL mascarada, modo e contagens |
| Escrita | SDK, agent ou pipeline | `/v1/events/*` | Tabelas `overseer_*` |
| Triggers | UI/API client | `/v1/orchestrate/triggers` | Sinal operacional sem execução local |
| Arranque | `scripts/overseer-up.*` ou Compose | Docker Compose | API + MariaDB + UI |

## Estrutura Do Repositório

```text
Overseer/
  docs/
  frontend/
  openapi/
  overseer_agent/
  overseer_monitor/
  overseer_sdk/
  scripts/
  src/overseer_api/
  src/overseer_core/
  tasks/
  templates/pipeline-repo/
  tests/
  docker-compose.yml
  Dockerfile
  scripts/overseer-up.cmd
```

## Docker / Instalação

O caminho oficial é Docker-first e deve funcionar em Windows, Linux e macOS com Docker Compose.

| Sistema | Comando |
|---|---|
| Windows CMD | `scripts\overseer-up.cmd` |
| PowerShell | `.\scripts\overseer-up.ps1` |
| Linux/macOS | `sh scripts/overseer-up.sh` |
| Manual | `docker compose up --build -d` |

Python local só é necessário para desenvolvimento e testes. Node.js deixou de ser requisito porque o frontend é estático.

## Variáveis De Ambiente

| Variável | Obrigatória | Descrição | Exemplo seguro |
|---|---:|---|---|
| `OVERSEER_API_TOKEN` | Não | Token Bearer para APIs protegidas | `change-me-local-token` |
| `OVERSEER_API_PORT` | Não | Porta HTTP local | `8090` |
| `OVERSEER_DB_URL` | Não | URL SQLAlchemy canónico | `mysql+pymysql://overseer:overseer@mysql:3306/Overseer?charset=utf8mb4` |
| `MYSQL_PASSWORD` | Não | Password local MariaDB | `overseer` |
| `MYSQL_ROOT_PASSWORD` | Não | Password root local MariaDB | `overseer` |

## MCP Servers Do Projeto

| MCP Server | Estado | Nota |
|---|---|---|
| N/A | Não configurado | Não foram encontrados `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json` |

## Skills Do Projeto

Skills inventariadas em `.agents/skills/README.md` (cópia Claude em `.claude/skills/`). Para alterações fullstack são relevantes: `repo-onboarding`, `fullstack-delivery`, `backend-architecture`, `frontend-skill-orchestrator`, `frontend-api-integration`, `api-contract-guardian`, `database-migration-safety`, `dependency-manager`, `docker-deploy`, `secrets-layout-guardian`, `quality-gate-runner`, `professional-documentation` e `stop-the-slop`.

## ADRs Do Projeto

| ADR | Decisão | Estado |
|---|---|---|
| `docs/adr/0000-template.md` | Template | Existente |
| `docs/adr/0001-overseer-core-api-refactor.md` | FastAPI única, schema `overseer_*`, frontend local e Docker-first | Aceite |

## Riscos Conhecidos

| Risco | Impacto | Mitigação |
|---|---|---|
| Migração para schema novo | Dados legados não são contrato v4 | Refactor aceite; tabelas `overseer_*` são o contrato ativo |
| Produção/SSH não confirmados | Risco operacional remoto | Não usar SSH/produção sem confirmação explícita |
| Pipelines reais fora do repo | Catálogo pode ficar vazio até integração | Registar DAG por `/v1/catalog/pipelines` ou usar template |
| DB existente sem coluna `metadata_json` | Inserção de catálogo pode falhar sem migração | `init_schema()` adiciona a coluna quando está ausente |

## Critérios De Verificação

- `python -m pytest -q`.
- `docker compose config`.
- `docker compose build`.
- Health em `http://127.0.0.1:8090/v1/health`.
- UI em `http://127.0.0.1:8090/ui/dashboard.html`.
- DB ativa em `http://127.0.0.1:8090/v1/read/database`.
- Demo com `docker compose exec overseer-api python scripts/overseer_emit_demo.py`.
