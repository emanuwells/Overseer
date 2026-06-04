# PROJECT_CONTEXT — Overseer

Este ficheiro descreve o contexto específico do projeto Overseer. Deve ser lido em conjunto com `AGENTS.md`, `HANDOFF.md`, `SKILLS.md`, `CHANGELOG_POLICY.md` e `README.md`.

## Identidade Do Projeto

| Campo | Valor |
|---|---|
| Nome | Overseer |
| Tipo | Núcleo Docker para orquestração, ingest e monitorização de pipelines |
| Responsável | A confirmar |
| Estado | Núcleo v4.0.0 com DB oficial preparada, UI operacional e kit padrão de pipelines |
| Escala | Projeto técnico não trivial, com API, DB, frontend, Docker, SDK e pipelines |

## Objetivo

Disponibilizar um workflow único por Docker que arranca API, frontend e base de dados local. O Overseer lê telemetria, escreve eventos operacionais na DB e orquestra pipelines por API.

## Stack Técnica

| Área | Tecnologia |
|---|---|
| API | FastAPI, Uvicorn |
| Frontend | React, Vite, lucide-react |
| Base de dados | MariaDB local; SQLAlchemy para preparar outros dialectos como PostgreSQL |
| SDK / Agent | Python, HTTPX, pacote instalável `overseer-core` |
| Configuração | `.env.example`, variáveis de ambiente, YAML |
| Docker | Dockerfile multi-stage, Docker Compose |
| Testes | `pytest` |

## Arquitetura

```mermaid
flowchart LR
    ui[React /ui] --> read[/v1/read/]
    pipelines[Pipelines / Agent] --> events[/v1/events/]
    ui --> orch[/v1/orchestrate/]
    orch --> runner[Execução de pipelines]
    runner --> events
    read --> db[(MariaDB)]
    events --> db
    orch --> db
```

## Fluxos Principais

| Fluxo | Origem | Processamento | Destino |
|---|---|---|---|
| Leitura | Frontend/API client | `/v1/read/*` | JSON operacional |
| Estado DB | Frontend/API client | `/v1/read/database` | URL mascarada, modo e contagens |
| Escrita | SDK, agent ou pipeline | `/v1/events/*` | Tabelas `overseer_*` |
| Orquestração | UI/API client | `/v1/orchestrate/*` | Trigger ou execução de pipeline |
| Arranque | `overseer-up.cmd`, `scripts/overseer-up.ps1` ou `scripts/overseer-up.sh` | Docker Compose | API + MariaDB + UI |

## Estrutura Do Repositório

```text
Overseer/
  docs/adr/
  overseer_agent/
  overseer_monitor/
  overseer_sdk/
  openapi/
  pipelines/microsoft_forms_2_datalake/
  templates/pipeline-repo/
  scripts/
  src/overseer_api/
  src/overseer_core/
  tasks/
  webapp/
  docker-compose.yml
  Dockerfile
  overseer-up.cmd
```

## Docker / Instalação

O caminho oficial é Docker-first e deve funcionar em Windows, Linux e macOS com Docker Compose.

| Sistema | Comando |
|---|---|
| Windows CMD | `overseer-up.cmd` |
| PowerShell | `.\scripts\overseer-up.ps1` |
| Linux/macOS | `sh scripts/overseer-up.sh` |
| Manual | `docker compose up --build -d` |

Python e Node locais não são requisitos para executar o Overseer; o Dockerfile instala dependências Python e compila o frontend dentro da imagem.

## Variáveis De Ambiente

| Variável | Obrigatória | Descrição | Exemplo seguro |
|---|---:|---|---|
| `OVERSEER_API_TOKEN` | Não | Token Bearer para APIs protegidas | `change-me-local-token` |
| `OVERSEER_API_PORT` | Não | Porta HTTP local | `8090` |
| `OVERSEER_DB_URL` | Não | URL SQLAlchemy canónico | `mysql+pymysql://overseer:overseer@mysql:3306/Overseer?charset=utf8mb4` |
| `OVERSEER_PIPELINES_DIR` | Não | Diretórios extra de pipelines, separados por `os.pathsep` | `/opt/pipelines` |
| `MYSQL_PASSWORD` | Não | Password local MariaDB | `overseer` |
| `MYSQL_ROOT_PASSWORD` | Não | Password root local MariaDB | `overseer` |

## MCP Servers Do Projeto

| MCP Server | Estado | Nota |
|---|---|---|
| N/A | Não configurado | Não foram encontrados `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json` |

## Skills Do Projeto

Skills locais inventariadas em `SKILLS.md`. Nesta tarefa são relevantes: `repo-onboarding`, `skill-selector`, `fullstack-delivery`, `backend-architecture`, `frontend-architecture`, `docker-coolify-deploy`, `api-contract-guardian`, `database-migration-safety`, `dependency-manager`, `file-pruner`, `documentation-keeper`, `handoff-maintainer`, `changelog-semver`, `definition-of-done`, `security-secrets-audit`, `prompt-injection-guard` e `stop-the-slop`.

## ADRs Do Projeto

| ADR | Decisão | Estado |
|---|---|---|
| `docs/adr/0000-template.md` | Template | Existente |
| `docs/adr/0001-overseer-core-api-refactor.md` | FastAPI única, schema `overseer_*`, React/Vite e Docker-first | Aceite |

## Riscos Conhecidos

| Risco | Impacto | Mitigação |
|---|---|---|
| `webapp/node_modules` parcial em OneDrive | Pode resistir a remoção local | Ignorado por Git e excluído por `.dockerignore`; Docker instala dependências dentro da imagem |
| Migração para schema novo | Dados legados não são contrato v4 | Refactor aceite como agressivo; tabelas antigas removidas do caminho principal |
| Produção/SSH não confirmados | Risco operacional remoto | Não usar SSH/produção sem confirmação explícita |
| Bind mount de pipelines em caminhos Windows/OneDrive | Pode chegar vazio ao container | O exemplo fica em `/app/pipelines`; o host monta em `/app/host_pipelines` sem sobrepor |

## Critérios De Verificação

- `python -m pytest -q`.
- `docker compose build` ou `docker compose up --build -d`.
- Health em `http://127.0.0.1:8090/v1/health`.
- UI em `http://127.0.0.1:8090/ui/`.
- DB ativa em `http://127.0.0.1:8090/v1/read/database`.
- Run de demonstração com `docker compose exec overseer-api python scripts/overseer_emit_demo.py`.
